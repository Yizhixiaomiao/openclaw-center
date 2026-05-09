from fastapi import APIRouter, HTTPException, Depends, Header
from sqlalchemy.orm import Session
from datetime import datetime
import json
from app.database import SessionLocal
from app.models.machine import Machine, AgentInfo, OpenClawConfig
from app.models.skill import MachineSkill, Skill
from app.models.deploy import DeployTask, DeployTaskItem
from app.models.log import AgentLog
from app.models.plan import UsageRecord, CodingPlan
from app.schemas.machine import (
    AgentRegisterRequest,
    AgentHeartbeatRequest,
    AgentConfigReportRequest,
    AgentTaskReportRequest,
    AgentLogReportRequest,
    AgentUsageReportRequest,
)

router = APIRouter()


def get_machine_by_code(db: Session, machine_code: str) -> Machine:
    machine = db.query(Machine).filter(Machine.code == machine_code).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    return machine


@router.post("/register")
def agent_register(req: AgentRegisterRequest):
    db = SessionLocal()
    try:
        machine = db.query(Machine).filter(Machine.code == req.machine_code).first()
        if not machine:
            machine = Machine(
                code=req.machine_code,
                hostname=req.hostname,
                ip=req.ip,
                os=req.os,
                agent_version=req.agent_version,
                openclaw_version=req.openclaw_version,
                status="online",
                last_heartbeat_at=datetime.now(),
            )
            db.add(machine)
            db.commit()
            db.refresh(machine)
        else:
            machine.hostname = req.hostname
            machine.ip = req.ip
            if req.os:
                machine.os = req.os
            if req.agent_version:
                machine.agent_version = req.agent_version
            if req.openclaw_version:
                machine.openclaw_version = req.openclaw_version
            machine.status = "online"
            machine.last_heartbeat_at = datetime.now()

        agent = (
            db.query(AgentInfo).filter(AgentInfo.machine_id == machine.id).first()
        )
        if not agent:
            agent = AgentInfo(
                machine_id=machine.id,
                agent_version=req.agent_version or "0.1.0",
                install_path="C:\\ProgramData\\OpenClawCenterAgent",
                service_status="running",
                last_report_at=datetime.now(),
            )
            db.add(agent)
        else:
            agent.service_status = "running"
            agent.last_report_at = datetime.now()
            if req.agent_version:
                agent.agent_version = req.agent_version

        db.commit()
        return {"status": "ok", "machine_id": machine.id}
    finally:
        db.close()


@router.post("/heartbeat")
def agent_heartbeat(req: AgentHeartbeatRequest):
    db = SessionLocal()
    try:
        machine = get_machine_by_code(db, req.machine_code)
        machine.status = req.status or "online"
        machine.last_heartbeat_at = datetime.now()

        agent = (
            db.query(AgentInfo).filter(AgentInfo.machine_id == machine.id).first()
        )
        if agent:
            agent.service_status = req.service_status or "running"
            agent.last_report_at = datetime.now()

        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


@router.post("/config/report")
def agent_config_report(req: AgentConfigReportRequest):
    db = SessionLocal()
    try:
        machine = get_machine_by_code(db, req.machine_code)

        config = OpenClawConfig(
            machine_id=machine.id,
            config_version=req.openclaw_config_hash or "unknown",
            model_provider=req.model_provider,
            model_name=req.model_name,
            config_json=json.dumps(
                {"skills": req.skills, "prompt_versions": req.prompt_versions}
            ),
        )
        db.add(config)

        # Update machine skills
        if req.skills:
            try:
                skills_data = json.loads(req.skills)
                db.query(MachineSkill).filter(
                    MachineSkill.machine_id == machine.id
                ).delete()
                for s in skills_data if isinstance(skills_data, list) else []:
                    skill = db.query(Skill).filter(Skill.code == s.get("code")).first()
                    if skill:
                        ms = MachineSkill(
                            machine_id=machine.id,
                            skill_id=skill.id,
                            installed_version=s.get("version"),
                            status="installed",
                        )
                        db.add(ms)
            except (json.JSONDecodeError, TypeError):
                pass

        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


@router.get("/tasks/pull")
def agent_tasks_pull(machine_code: str, agent_version: str = None):
    db = SessionLocal()
    try:
        machine = get_machine_by_code(db, machine_code)
        pending_items = (
            db.query(DeployTaskItem)
            .filter(
                DeployTaskItem.machine_id == machine.id,
                DeployTaskItem.status == "pending",
            )
            .all()
        )
        tasks = []
        for item in pending_items:
            task = (
                db.query(DeployTask).filter(DeployTask.id == item.task_id).first()
            )
            if task:
                tasks.append(
                    {
                        "task_item_id": item.id,
                        "task_id": task.id,
                        "task_type": task.task_type,
                        "payload": task.payload_json,
                    }
                )
                item.status = "downloading"
                item.started_at = datetime.now()

        db.commit()
        return {"tasks": tasks}
    finally:
        db.close()


@router.post("/tasks/report")
def agent_tasks_report(req: AgentTaskReportRequest):
    db = SessionLocal()
    try:
        item = (
            db.query(DeployTaskItem).filter(DeployTaskItem.id == req.task_item_id).first()
        )
        if not item:
            raise HTTPException(status_code=404, detail="Task item not found")

        item.status = req.status
        item.message = req.message
        item.finished_at = datetime.now()

        # Check if all items of this task are done
        task = (
            db.query(DeployTask).filter(DeployTask.id == item.task_id).first()
        )
        if task:
            all_items = (
                db.query(DeployTaskItem)
                .filter(DeployTaskItem.task_id == task.id)
                .all()
            )
            if all(i.status in ("success", "failed", "rollback") for i in all_items):
                if all(i.status == "success" for i in all_items):
                    task.status = "completed"
                elif all(i.status == "failed" for i in all_items):
                    task.status = "failed"
                else:
                    task.status = "partial"

        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


@router.post("/logs/report")
def agent_logs_report(req: AgentLogReportRequest):
    db = SessionLocal()
    try:
        machine = get_machine_by_code(db, req.machine_code)
        log = AgentLog(
            machine_id=machine.id,
            level=req.level or "info",
            category=req.category,
            message=req.message,
            detail_json=req.detail_json,
        )
        db.add(log)
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


@router.post("/usage/report")
def agent_usage_report(req: AgentUsageReportRequest):
    db = SessionLocal()
    try:
        machine = get_machine_by_code(db, req.machine_code)
        record = UsageRecord(
            machine_id=machine.id,
            user_id=machine.user_id,
            plan_id=req.plan_id,
            calls=req.calls,
            tokens=req.tokens,
        )
        db.add(record)

        # Update plan quota_used
        if req.plan_id:
            plan = db.query(CodingPlan).filter(CodingPlan.id == req.plan_id).first()
            if plan:
                plan.quota_used = (plan.quota_used or 0) + req.tokens

        db.commit()
        return {"status": "ok"}
    finally:
        db.close()
