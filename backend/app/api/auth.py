from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.schemas.auth import LoginRequest, TokenResponse
from app.utils.security import verify_password, hash_password, create_access_token
from app.models.user import User

router = APIRouter()


def seed_admin():
    """Ensure default admin user exists"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                name="System Admin",
                username="admin",
                hashed_password=hash_password("admin123"),
                role="admin",
                status="active",
            )
            db.add(admin)
            db.commit()
    finally:
        db.close()


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == req.username).first()
        if not user or not verify_password(req.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        if user.status != "active":
            raise HTTPException(status_code=403, detail="Account is disabled")
        token = create_access_token(data={"sub": str(user.id), "role": user.role})
        return TokenResponse(access_token=token, user_id=user.id, name=user.name, role=user.role)
    finally:
        db.close()
