from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.utils.deps import get_db, get_current_user, require_role
from app.models.user import User, UserProfile, BusinessScenario
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, UserProfileUpdate, UserProfileResponse,
    ScenarioCreate, ScenarioUpdate, ScenarioResponse,
)
from app.utils.security import hash_password

router = APIRouter()


@router.get("")
def list_users(
    department: Optional[str] = None,
    position: Optional[str] = None,
    role: Optional[str] = None,
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(User)
    if department:
        q = q.filter(User.department == department)
    if position:
        q = q.filter(User.position == position)
    if role:
        q = q.filter(User.role == role)
    if status:
        q = q.filter(User.status == status)
    if keyword:
        q = q.filter((User.name.contains(keyword)) | (User.username.contains(keyword)))
    total = q.count()
    items = q.offset(skip).limit(limit).all()
    return {"items": [UserResponse.model_validate(u).model_dump() for u in items], "total": total}


@router.post("", response_model=UserResponse, status_code=201)
def create_user(req: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "support"))):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    user = User(
        name=req.name,
        username=req.username,
        hashed_password=hash_password(req.password),
        company=req.company,
        department=req.department,
        position=req.position,
        phone=req.phone,
        support_owner=req.support_owner,
        role=req.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.put("/{user_id}", response_model=UserResponse)
def update_user(user_id: int, req: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "support"))):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    db.query(UserProfile).filter(UserProfile.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"status": "ok", "message": "用户已删除"}


@router.get("/{user_id}/profile", response_model=UserProfileResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("/{user_id}/profile", response_model=UserProfileResponse)
def update_user_profile(user_id: int, req: UserProfileUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role("admin", "support"))):
    profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(profile, k, v)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/{user_id}/scenarios", response_model=List[ScenarioResponse])
def list_user_scenarios(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(BusinessScenario).filter(BusinessScenario.user_id == user_id).all()
