from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from cryptography.fernet import Fernet
import base64
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


# Fernet encryption for sensitive config like API keys
_fernet_key = base64.urlsafe_b64encode(settings.ENCRYPTION_KEY.encode()[:32].ljust(32, b'0'))
fernet = Fernet(_fernet_key)


def encrypt_value(plain: str) -> str:
    return fernet.encrypt(plain.encode()).decode()


def decrypt_value(encrypted: str) -> str:
    return fernet.decrypt(encrypted.encode()).decode()
