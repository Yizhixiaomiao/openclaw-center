from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import json
import re
from app.config import settings
from app.utils.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.machine import Machine
from app.models.skill import Skill, MachineSkill
from app.models.deploy import DeployTask, DeployTaskItem
from app.models.machine import AgentInfo
from app.schemas.skill import SkillCreate, SkillUpdate, SkillResponse, MachineSkillResponse

EXCLUDED_FILES = {"package.zip"}
DEFAULT_SKILLS_DIR = r"C:\OpenClaw\skills"

router = APIRouter()


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


@router.get("")
def list_skills(
    position_type: Optional[str] = None,
    audit_status: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    machine_ip: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Skill)
    if position_type:
        q = q.filter(Skill.position_type == position_type)
    if audit_status:
        q = q.filter(Skill.audit_status == audit_status)
    if status:
        q = q.filter(Skill.status == status)
    if keyword:
        q = q.filter(
            Skill.name.contains(keyword)
            | Skill.code.contains(keyword)
            | Skill.version.contains(keyword)
            | Skill.description.contains(keyword)
            | Skill.position_type.contains(keyword)
        )
    if machine_ip:
        q = q.filter(
            Skill.id.in_(
                db.query(MachineSkill.skill_id)
                .join(Machine, MachineSkill.machine_id == Machine.id)
                .filter(Machine.ip.contains(machine_ip))
            )
        )
    total = q.count()
    items = q.order_by(Skill.updated_at.desc()).offset(skip).limit(limit).all()
    return {"items": items, "total": total}


@router.post("", response_model=SkillResponse, status_code=201)
def create_skill(
    req: SkillCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "support")),
):
    if db.query(Skill).filter(Skill.code == req.code).first():
        raise HTTPException(status_code=400, detail="Skill code already exists")
    skill = Skill(**req.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.get("/{skill_id}", response_model=SkillResponse)
def get_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.put("/{skill_id}", response_model=SkillResponse)
def update_skill(
    skill_id: int,
    req: SkillUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "support")),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(skill, k, v)
    db.commit()
    db.refresh(skill)
    return skill


@router.post("/{skill_id}/audit", response_model=SkillResponse)
def audit_skill(
    skill_id: int,
    audit_status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    if audit_status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Invalid audit status")
    skill.audit_status = audit_status
    if audit_status == "approved":
        skill.status = "published"
    db.commit()
    db.refresh(skill)
    return skill


@router.get("/machine/{machine_id}", response_model=List[MachineSkillResponse])
def list_machine_skills(
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(MachineSkill).filter(MachineSkill.machine_id == machine_id).all()


@router.get("/{skill_code}/download")
def download_skill(
    skill_code: str,
):
    skill_dir = os.path.join(settings.UPLOAD_DIR, "skills", skill_code)
    zip_path = os.path.join(skill_dir, "package.zip")
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="Skill package not found")
    return FileResponse(zip_path, filename=f"{skill_code}.zip", media_type="application/zip")


@router.get("/detail/{skill_id}")
def get_skill_detail(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    # Get machines that have this skill installed (exclude removed)
    ms_records = (
        db.query(MachineSkill, Machine.code, Machine.hostname, Machine.ip)
        .join(Machine, MachineSkill.machine_id == Machine.id)
        .filter(MachineSkill.skill_id == skill_id, MachineSkill.status != "removed")
        .all()
    )
    machines = [
        {
            "machine_id": m.MachineSkill.machine_id,
            "machine_code": m.code,
            "hostname": m.hostname,
            "ip": m.ip,
            "status": m.MachineSkill.status,
            "installed_version": m.MachineSkill.installed_version,
            "installed_at": str(m.MachineSkill.installed_at) if m.MachineSkill.installed_at else None,
        }
        for m in ms_records
    ]
    return {
        "skill": SkillResponse.model_validate(skill).model_dump(),
        "machines": machines,
    }


@router.delete("/{skill_id}/machine/{machine_id}")
def remove_skill_from_machine(
    skill_id: int,
    machine_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin", "support")),
):
    ms = (
        db.query(MachineSkill)
        .filter(MachineSkill.skill_id == skill_id, MachineSkill.machine_id == machine_id)
        .first()
    )
    if not ms:
        raise HTTPException(status_code=404, detail="Skill not installed on this machine")

    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    machine = db.query(Machine).filter(Machine.id == machine_id).first()

    # Mark as removed instead of deleting, so agent report won't restore it
    ms.status = "removed"
    db.commit()

    # Create deploy task to instruct agent to delete local skill folder
    if skill and machine:
        agent_info = db.query(AgentInfo).filter(AgentInfo.machine_id == machine_id).first()
        skills_dir = _get_skills_dir(agent_info)
        payload = json.dumps({
            "skill_code": skill.code,
            "install_path": skills_dir,
        })
        task = DeployTask(
            task_type="skill_remove",
            target_type="machine",
            target_id=str(machine_id),
            payload_json=payload,
            status="in_progress",
            created_by=current_user.id,
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        item = DeployTaskItem(task_id=task.id, machine_id=machine_id, status="pending")
        db.add(item)
        db.commit()

    return {"status": "ok", "message": "Skill removal task created"}


@router.delete("/{skill_id}")
def delete_skill(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    # Remove machine associations
    db.query(MachineSkill).filter(MachineSkill.skill_id == skill_id).delete()
    # Remove uploaded files
    skill_dir = os.path.join(settings.UPLOAD_DIR, "skills", skill.code)
    if os.path.exists(skill_dir):
        import shutil
        shutil.rmtree(skill_dir)
    db.delete(skill)
    db.commit()
    return {"status": "ok", "message": f"Skill '{skill.code}' deleted"}


def _build_file_tree(directory, base=""):
    """Recursively build file tree from directory, excluding package.zip."""
    items = []
    try:
        entries = sorted(os.listdir(directory))
    except OSError:
        return items
    for name in entries:
        if name in EXCLUDED_FILES:
            continue
        rel_path = f"{base}/{name}" if base else name
        full_path = os.path.join(directory, name)
        if os.path.isdir(full_path):
            children = _build_file_tree(full_path, rel_path)
            items.append({"path": rel_path, "type": "dir", "children": children})
        else:
            items.append({"path": rel_path, "type": "file", "size": os.path.getsize(full_path)})
    return items


@router.get("/{skill_id}/files")
def get_skill_files(
    skill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill_dir = os.path.join(settings.UPLOAD_DIR, "skills", skill.code)
    if not os.path.isdir(skill_dir):
        return {"files": []}
    return {"files": _build_file_tree(skill_dir)}


@router.get("/{skill_id}/files/content")
def get_skill_file_content(
    skill_id: int,
    path: str = Query(..., description="Relative file path within skill folder"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    skill = db.query(Skill).filter(Skill.id == skill_id).first()
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    skill_dir = os.path.join(settings.UPLOAD_DIR, "skills", skill.code)
    file_path = os.path.normpath(os.path.join(skill_dir, path))
    if not file_path.startswith(os.path.normpath(skill_dir)):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"path": path, "content": content, "size": os.path.getsize(file_path)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {e}")
