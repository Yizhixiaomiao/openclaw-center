from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func as sa_func
from typing import Optional, List
from datetime import datetime
import json
import hashlib
from app.utils.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.machine import Machine, AgentInfo, OpenClawConfig
from app.models.skill import MachineSkill, Skill
from app.models.log import AgentLog
from app.models.deploy import DeployTask, DeployTaskItem
from app.schemas.machine import MachineCreate, MachineUpdate, MachineResponse, ConfigUpdateRequest, AgentConfigUpdateRequest

router = APIRouter()


@router.get("", response_model=List[MachineResponse])
def list_machines(
    status: Optional[str] = None,
    department: Optional[str] = None,
    user_id: Optional[int] = None,
    keyword: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Machine)
    if status:
        q = q.filter(Machine.status == status)
    if department:
        q = q.filter(Machine.department == department)
    if user_id:
        q = q.filter(Machine.user_id == user_id)
    if keyword:
        q = q.filter(
            (Machine.hostname.contains(keyword))
            | (Machine.code.contains(keyword))
            | (Machine.ip.contains(keyword))
        )
    machines = q.offset(skip).limit(limit).all()
    # Attach skills count
    machine_ids = [m.id for m in machines]
    if machine_ids:
        skills_counts = (
            db.query(MachineSkill.machine_id, sa_func.count(MachineSkill.id))
            .filter(MachineSkill.machine_id.in_(machine_ids))
            .group_by(MachineSkill.machine_id)
            .all()
        )
        skills_map = {mid: cnt for mid, cnt in skills_counts}
        result = []
        for m in machines:
            data = MachineResponse.model_validate(m).model_dump()
            data["skills_count"] = skills_map.get(m.id, 0)
            result.append(data)
        return result
    return [MachineResponse.model_validate(m).model_dump() for m in machines]


@router.post("", response_model=MachineResponse, status_code=201)
def create_machine(
    req: MachineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "ops")),
):
    if db.query(Machine).filter(Machine.code == req.code).first():
        raise HTTPException(status_code=400, detail="Machine code already exists")
    machine = Machine(**req.model_dump())
    db.add(machine)
    db.commit()
    db.refresh(machine)
    return machine


@router.get("/{machine_id}")
def get_machine(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    agent_info = (
        db.query(AgentInfo).filter(AgentInfo.machine_id == machine_id).first()
    )
    latest_config = (
        db.query(OpenClawConfig)
        .filter(OpenClawConfig.machine_id == machine_id)
        .order_by(OpenClawConfig.created_at.desc())
        .first()
    )
    skill_rows = (
        db.query(MachineSkill, Skill.name, Skill.code)
        .outerjoin(Skill, MachineSkill.skill_id == Skill.id)
        .filter(MachineSkill.machine_id == machine_id)
        .all()
    )
    recent_logs = (
        db.query(AgentLog)
        .filter(AgentLog.machine_id == machine_id)
        .order_by(AgentLog.created_at.desc())
        .limit(10)
        .all()
    )
    recent_deploys = (
        db.query(DeployTaskItem)
        .filter(DeployTaskItem.machine_id == machine_id)
        .order_by(DeployTaskItem.id.desc())
        .limit(10)
        .all()
    )
    return {
        "machine": MachineResponse.model_validate(machine).model_dump(),
        "agent": {
            "agent_version": agent_info.agent_version,
            "service_status": agent_info.service_status,
            "last_report_at": str(agent_info.last_report_at),
            "agent_config_content": agent_info.agent_config_content,
            "agent_config_path": agent_info.agent_config_path,
        }
        if agent_info
        else None,
        "config": {
            "config_version": latest_config.config_version,
            "model_provider": latest_config.model_provider,
            "model_name": latest_config.model_name,
            "config_content": latest_config.config_content,
            "config_file_path": latest_config.config_file_path,
        }
        if latest_config
        else None,
        "skills": [
            {
                "id": s.MachineSkill.id,
                "skill_id": s.MachineSkill.skill_id,
                "name": s.name or s.code or f"Skill-{s.skill_id}",
                "code": s.code or "",
                "installed_version": s.MachineSkill.installed_version,
                "status": s.MachineSkill.status,
            }
            for s in skill_rows
        ],
        "recent_logs": [
            {
                "level": l.level,
                "category": l.category,
                "message": l.message,
                "created_at": str(l.created_at),
            }
            for l in recent_logs
        ],
        "recent_deploys": [
            {
                "id": d.id,
                "task_id": d.task_id,
                "status": d.status,
                "message": d.message,
                "finished_at": str(d.finished_at),
            }
            for d in recent_deploys
        ],
    }


@router.put("/{machine_id}", response_model=MachineResponse)
def update_machine(
    machine_id: int,
    req: MachineUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "ops")),
):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(machine, k, v)
    db.commit()
    db.refresh(machine)
    return machine


@router.put("/{machine_id}/config")
def update_machine_config(
    machine_id: int,
    req: ConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "ops")),
):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    latest_config = (
        db.query(OpenClawConfig)
        .filter(OpenClawConfig.machine_id == machine_id)
        .order_by(OpenClawConfig.created_at.desc())
        .first()
    )

    # Parse new config content for model info
    model_provider = ""
    model_name = ""
    try:
        data = json.loads(req.config_content)
        model_provider = data.get("model_provider", data.get("provider", ""))
        model_name = data.get("model_name", data.get("model", ""))
    except (json.JSONDecodeError, TypeError):
        pass

    config_version = hashlib.md5(req.config_content.encode()).hexdigest()

    # Create new config record with updated content
    new_config = OpenClawConfig(
        machine_id=machine_id,
        config_version=config_version,
        model_provider=model_provider,
        model_name=model_name,
        config_content=req.config_content,
        config_file_path=latest_config.config_file_path if latest_config else None,
        config_json=latest_config.config_json if latest_config else "{}",
    )
    db.add(new_config)

    # Create deploy task to sync config to agent machine
    config_file_path = latest_config.config_file_path if latest_config else None
    if config_file_path:
        payload = json.dumps({
            "target_path": config_file_path,
            "content": req.config_content,
        })
        task = DeployTask(
            task_type="config",
            target_type="machine",
            target_id=str(machine_id),
            payload_json=payload,
            status="pending",
            created_by=current_user.id,
        )
        db.add(task)
        db.flush()
        task_item = DeployTaskItem(
            task_id=task.id,
            machine_id=machine_id,
            status="pending",
        )
        db.add(task_item)

    db.commit()
    return {"status": "ok", "message": "配置已保存" + ("，同步任务已创建" if config_file_path else "")}


@router.put("/{machine_id}/agent-config")
def update_agent_config(
    machine_id: int,
    req: AgentConfigUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "ops")),
):
    machine = db.query(Machine).filter(Machine.id == machine_id).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine not found")

    agent = db.query(AgentInfo).filter(AgentInfo.machine_id == machine_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent.agent_config_content = req.agent_config_content

    # Create deploy task to sync agent config
    config_path = agent.agent_config_path
    if config_path:
        payload = json.dumps({
            "target_path": config_path,
            "content": req.agent_config_content,
        })
        task = DeployTask(
            task_type="config",
            target_type="machine",
            target_id=str(machine_id),
            payload_json=payload,
            status="pending",
            created_by=current_user.id,
        )
        db.add(task)
        db.flush()
        task_item = DeployTaskItem(
            task_id=task.id,
            machine_id=machine_id,
            status="pending",
        )
        db.add(task_item)

    db.commit()
    return {"status": "ok", "message": "Agent配置已保存" + ("，同步任务已创建" if config_path else "")}
