from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.utils.deps import get_db, get_current_user, require_role
from app.models.user import User
from app.models.skill import Skill, MachineSkill
from app.schemas.skill import SkillCreate, SkillUpdate, SkillResponse, MachineSkillResponse

router = APIRouter()


@router.get("", response_model=List[SkillResponse])
def list_skills(
    position_type: Optional[str] = None,
    audit_status: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
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
        q = q.filter(Skill.name.contains(keyword) | Skill.code.contains(keyword))
    return q.order_by(Skill.updated_at.desc()).offset(skip).limit(limit).all()


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
