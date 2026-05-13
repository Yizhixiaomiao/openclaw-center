from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import json
import re
from app.utils.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.machine import Machine, AgentInfo
from app.models.deploy import DeployTask, DeployTaskItem
from app.schemas.deploy import DeployTaskCreate, DeployTaskResponse, DeployTaskItemResponse, SkillDistributeRequest


DEFAULT_SKILLS_DIR = r"C:\OpenClaw\skills"


def _get_skills_dir(agent_info):
    """Extract openclaw_skills_dir from agent config YAML (regex, no yaml dependency)."""
    if not agent_info or not agent_info.agent_config_content:
        return DEFAULT_SKILLS_DIR
    try:
        m = re.search(r'^openclaw_skills_dir:\s*[\'"]?(.+?)[\'"]?\s*$', agent_info.agent_config_content, re.MULTILINE)
        if m:
            return m.group(1).strip()
    except Exception:
        pass
    return DEFAULT_SKILLS_DIR

router = APIRouter()


@router.get("")
def list_deploy_tasks(
    task_type: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(DeployTask)
    if task_type:
        q = q.filter(DeployTask.task_type == task_type)
    if status:
        q = q.filter(DeployTask.status == status)
    total = q.count()
    items = q.order_by(DeployTask.created_at.desc()).offset(skip).limit(limit).all()
    return {"items": [DeployTaskResponse.model_validate(t).model_dump() for t in items], "total": total}


@router.post("", response_model=DeployTaskResponse, status_code=201)
def create_deploy_task(
    req: DeployTaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "support", "ops")),
):
    task = DeployTask(
        task_type=req.task_type,
        target_type=req.target_type,
        target_id=req.target_id,
        payload_json=req.payload_json,
        status="pending",
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    # Resolve target machines
    machine_ids = []
    if req.target_type == "machine":
        machine_ids = [int(req.target_id)]
    elif req.target_type == "user":
        machines = (
            db.query(Machine).filter(Machine.user_id == int(req.target_id)).all()
        )
        machine_ids = [m.id for m in machines]
    elif req.target_type == "department":
        machines = (
            db.query(Machine).filter(Machine.department == req.target_id).all()
        )
        machine_ids = [m.id for m in machines]

    if not machine_ids:
        task.status = "failed"
        db.commit()
        raise HTTPException(status_code=400, detail="No machines found for target")

    for mid in machine_ids:
        item = DeployTaskItem(task_id=task.id, machine_id=mid, status="pending")
        db.add(item)

    task.status = "in_progress"
    db.commit()
    db.refresh(task)
    return task


@router.post("/distribute-skill", response_model=DeployTaskResponse, status_code=201)
def distribute_skill(
    req: SkillDistributeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "support", "ops")),
):
    # Validate machines exist
    machines = db.query(Machine).filter(Machine.id.in_(req.machine_ids)).all()
    if not machines:
        raise HTTPException(status_code=400, detail="No valid machines found")
    found_ids = {m.id for m in machines}
    missing = set(req.machine_ids) - found_ids
    if missing:
        raise HTTPException(status_code=400, detail=f"Machine IDs not found: {missing}")

    # Get agent info for each machine to resolve skills dir
    agent_infos = db.query(AgentInfo).filter(AgentInfo.machine_id.in_(req.machine_ids)).all()
    agent_map = {ai.machine_id: ai for ai in agent_infos}

    # Create one deploy task per machine (each may have different install_path)
    created_tasks = []
    for mid in req.machine_ids:
        agent_info = agent_map.get(mid)
        skills_dir = req.install_path.strip() if req.install_path and req.install_path.strip() else _get_skills_dir(agent_info)

        payload = json.dumps({
            "skill_code": req.skill_code,
            "package_url": f"/api/skills/{req.skill_code}/download",
            "install_path": skills_dir,
        })

        task = DeployTask(
            task_type="skill",
            target_type="machine",
            target_id=str(mid),
            payload_json=payload,
            status="in_progress",
            created_by=current_user.id,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        item = DeployTaskItem(task_id=task.id, machine_id=mid, status="pending")
        db.add(item)
        db.commit()
        created_tasks.append(task)

    return created_tasks[0] if created_tasks else None


@router.get("/{task_id}")
def get_deploy_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = db.query(DeployTask).filter(DeployTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Deploy task not found")
    items = db.query(DeployTaskItem).filter(DeployTaskItem.task_id == task_id).all()
    return {
        "task": DeployTaskResponse.model_validate(task).model_dump(),
        "items": [
            DeployTaskItemResponse.model_validate(i).model_dump() for i in items
        ],
    }


@router.delete("/{task_id}")
def delete_deploy_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    task = db.query(DeployTask).filter(DeployTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Deploy task not found")
    db.query(DeployTaskItem).filter(DeployTaskItem.task_id == task_id).delete()
    db.delete(task)
    db.commit()
    return {"status": "ok", "message": "部署任务已删除"}
