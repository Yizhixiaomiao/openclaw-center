from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
import json
from app.utils.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.machine import Machine
from app.models.deploy import DeployTask, DeployTaskItem
from app.schemas.deploy import DeployTaskCreate, DeployTaskResponse, DeployTaskItemResponse, SkillDistributeRequest

router = APIRouter()


@router.get("", response_model=List[DeployTaskResponse])
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
    return q.order_by(DeployTask.created_at.desc()).offset(skip).limit(limit).all()


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

    # Build payload for skill distribution
    payload = json.dumps({
        "skill_code": req.skill_code,
        "package_url": f"/api/skills/{req.skill_code}/download",
        "install_path": req.install_path,
    })

    task = DeployTask(
        task_type="skill",
        target_type="machine",
        target_id=",".join(str(mid) for mid in req.machine_ids),
        payload_json=payload,
        status="in_progress",
        created_by=current_user.id,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    for mid in req.machine_ids:
        item = DeployTaskItem(task_id=task.id, machine_id=mid, status="pending")
        db.add(item)

    db.commit()
    db.refresh(task)
    return task


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
