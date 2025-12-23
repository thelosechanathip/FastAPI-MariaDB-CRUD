# First Project

#### Create Virtual Environment and Activate

## CRUD แบบปกติ

```PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
หมายเหตุ: RUN ทีละคำสั่ง

#### Install Package
```PowerShell(.venv)
pip install fastapi uvicorn sqlalchemy alembic pymysql pydantic-settings python-dotenv
```

#### Merse Directory app/main.py
```[app/main.py]
from fastapi import FastAPI

app = FastAPI(title="FastAPI + MariaDB CRUD")

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

ทดสอบยิง API ด้วย Postman
Method: Get
Endpoint: http://127.0.0.1:8000/health

#### Merse Directory All
app/__init__.py
app/api/__init__.py
app/core/__init__.py
app/db/__init__.py
app/models/__init__.py
app/schemas/__init__.py
app/crud/__init__.py
app/validators/__init__.py

#### Create file .env
```[app/.env]
APP_NAME="FastAPI + MariaDB CRUD"
APP_ENV="dev"
DEBUG=true
```

#### Setup Config too pydantic-settings
```[app/core/config.py]
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="FastAPI CRUD")
    app_env: str = Field(default="dev")  # dev/prod
    debug: bool = Field(default=False)


settings = Settings()
```

#### Adjust app/main.py to use Settings
```[app/main.py]
from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(title=settings.app_name)

@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "env": settings.app_env,
        "debug": settings.debug,
    }
```

#### Create Database for name fastapi_crud
```MySQL Command
CREATE DATABASE fastapi_crud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
```

#### Add value DB in .env file
```[app/.env]
APP_NAME="FastAPI + MariaDB CRUD"
APP_ENV="dev"
DEBUG=true

DB_HOST="127.0.0.1"
DB_PORT=3306
DB_NAME="fastapi_crud"
DB_USER="fastapi_user"
DB_PASSWORD="StrongPass123!"
```

#### Update app/core/config.py to support DB and Create DATEBASE_URL
```[app/core/config.py]
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="FastAPI CRUD")
    app_env: str = Field(default="dev")
    debug: bool = Field(default=False)

    db_host: str = Field(default="127.0.0.1")
    db_port: int = Field(default=3306)
    db_name: str = Field(default="fastapi_crud")
    db_user: str = Field(default="fastapi_user")
    db_password: str = Field(default="")

    @property
    def database_url(self) -> str:
        # MariaDB ใช้ MySQL protocol ได้ ผ่าน PyMySQL
        return (
            f"mysql+pymysql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
            f"?charset=utf8mb4"
        )


settings = Settings()
```

#### Create file connection DB: app/db/session.py
```[app/db/session.py]
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,   # ช่วยตรวจจับ connection หลุด
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)
```

#### Create Dependency for pulling session:app/db/deps/py
```[app/db/deps.py]
from typing import Generator
from sqlalchemy.orm import Session
from app.db.session import SessionLocal

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

#### Add endpoint /db-check in app/main.py
```[app/main.py]
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.db.deps import get_db

app = FastAPI(title=settings.app_name)

@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.app_env, "debug": settings.debug}

@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"db": "ok", "result": result}
```

ทดสอบด้วย Postman เหมือนเดิม
Method: Get
Endpoint: http://127.0.0.1:8000/db_check

#### Create Base ORM
```[app/db/base.py]
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

#### Create Model: User
```[app/models/user.py]
from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        default=True
    )

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        onupdate=func.now()
    )
```

#### Edit file app/db/session.py
```[app/db/session.py]
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)
```

#### Create table temporary
```[app/main.py]
from app.db.session import engine
from app.db.base import Base
from app.models.user import User  # noqa

Base.metadata.create_all(bind=engine)
```

#### Install Dependencies
```PowerShell(.venv)
pip install email-validator
```

#### Create validator "advance password"
```[app/validators/password.py]
import re

class PasswordPolicyError(ValueError):
    pass

def validate_password_policy(password: str) -> str:
    if len(password) < 8:
        raise PasswordPolicyError("รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")

    # อย่างน้อย 1 ตัวพิมพ์เล็ก / 1 ตัวพิมพ์ใหญ่ / 1 ตัวเลข / 1 อักขระพิเศษ
    if not re.search(r"[a-z]", password):
        raise PasswordPolicyError("รหัสผ่านต้องมีตัวพิมพ์เล็กอย่างน้อย 1 ตัว")
    if not re.search(r"[A-Z]", password):
        raise PasswordPolicyError("รหัสผ่านต้องมีตัวพิมพ์ใหญ่อย่างน้อย 1 ตัว")
    if not re.search(r"[0-9]", password):
        raise PasswordPolicyError("รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว")
    if not re.search(r"[^\w\s]", password):
        raise PasswordPolicyError("รหัสผ่านต้องมีอักขระพิเศษอย่างน้อย 1 ตัว (เช่น !@#)")

    if " " in password:
        raise PasswordPolicyError("รหัสผ่านห้ามมีช่องว่าง")

    return password
```

#### Create Schemas User (Pydantic v2 + validator)
```[app/schemas/user.py]
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from app.validators.password import validate_password_policy


class UserBase(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr

    # normalize: ตัดช่องว่าง/ทำให้เป็นรูปแบบมาตรฐาน
    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: str) -> str:
        v = v.strip()
        if " " in v:
            raise ValueError("username ห้ามมีช่องว่าง")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> EmailStr:
        # EmailStr เป็น type ที่ validate แล้ว แต่เราจะทำให้เป็น lower เพื่อกันซ้ำ
        return EmailStr(str(v).strip().lower())


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str = Field(min_length=8, max_length=128)

    # policy check (advance)
    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        return validate_password_policy(v)

    # cross-field validation: password ต้องตรงกัน
    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("password และ confirm_password ต้องตรงกัน")
        return self


class UserUpdate(BaseModel):
    # update เลยใช้ optional
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)

    @field_validator("username")
    @classmethod
    def normalize_username(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if " " in v:
            raise ValueError("username ห้ามมีช่องว่าง")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: Optional[EmailStr]) -> Optional[EmailStr]:
        if v is None:
            return v
        return EmailStr(str(v).strip().lower())

    @field_validator("password")
    @classmethod
    def password_policy(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        return validate_password_policy(v)


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None

    class Config:
        from_attributes = True  # ✅ ทำให้แปลงจาก SQLAlchemy model ได้
```

#### Add Endpoint to app/main.py
```[app/main.py]
from app.schemas.user import UserCreate

@app.post("/test-validate")
def test_validate(payload: UserCreate):
    return {"ok": True, "data": payload.model_dump(exclude={"password", "confirm_password"})}
```

#### Instal Dependencies
```PowerShell(.venv)
pip install bcrypt
```

#### Create file app/core/security.py
```[app/core/security.py]
import bcrypt

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
```

#### Create CRUD layer: app/crud/user.py
```[app/crud/user.py]
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password

def get_user_by_username(db: Session, username: str) -> User | None:
    stmt = select(User).where(User.username == username)
    return db.execute(stmt).scalar_one_or_none()

def get_user_by_email(db: Session, email: str) -> User | None:
    stmt = select(User).where(User.email == email)
    return db.execute(stmt).scalar_one_or_none()

def create_user(db: Session, payload: UserCreate) -> User:
    # ตรวจซ้ำ (ระดับ CRUD)
    if get_user_by_username(db, payload.username):
        raise ValueError("username นี้ถูกใช้แล้ว")
    if get_user_by_email(db, str(payload.email)):
        raise ValueError("email นี้ถูกใช้แล้ว")

    user = User(
        username=payload.username,
        email=str(payload.email),
        hashed_password=hash_password(payload.password),
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

#### Create API router: app/api/users.py
```[app/api/users.py]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.user import UserCreate, UserOut
from app.crud.user import create_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        user = create_user(db, payload)
        return user
    except ValueError as e:
        # ส่ง error 400 แบบอ่านง่าย
        raise HTTPException(status_code=400, detail=str(e))
```

#### Tied router enter app/main.py
```[app/main.py]
from app.api.users import router as users_router

app.include_router(users_router)
```

#### Add Function CRUD for Read Data
```[ap/crud/user.py]
from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.models.user import User

def get_user(db: Session, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()

def list_users(
    db: Session,
    skip: int = 0,
    limit: int = 10,
    q: str | None = None,
) -> list[User]:
    stmt = select(User)

    # search แบบง่าย: username/email มีคำค้น
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(or_(User.username.like(like), User.email.like(like)))

    stmt = stmt.order_by(User.id.desc()).offset(skip).limit(limit)
    return list(db.execute(stmt).scalars().all())
```

#### Add endpoint READ in app/api/users.py
```[app/api/users.py]
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.user import UserOut, UserCreate
from app.crud.user import create_user, get_user, list_users

router = APIRouter(prefix="/users", tags=["users"])

# CREATE (ของเดิม)
@router.post("", response_model=UserOut, status_code=201)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        return create_user(db, payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# READ: list + pagination + search
@router.get("", response_model=list[UserOut])
def read_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    q: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
):
    return list_users(db, skip=skip, limit=limit, q=q)

# READ: by id
@router.get("/{user_id}", response_model=UserOut)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    return user
```

#### CRUD: Add Function update/delete
```[app/crud/user.py]
from sqlalchemy.orm import Session
from sqlalchemy import select, or_
from app.models.user import User
from app.schemas.user import UserUpdate
from app.core.security import hash_password

def update_user(db: Session, user_id: int, payload: UserUpdate) -> User | None:
    user = get_user(db, user_id)
    if not user:
        return None

    # อัปเดตเฉพาะ field ที่ส่งมา
    data = payload.model_dump(exclude_unset=True)

    # ตรวจซ้ำ username/email (ถ้าส่งมา)
    if "username" in data and data["username"] != user.username:
        exists = get_user_by_username(db, data["username"])
        if exists and exists.id != user.id:
            raise ValueError("username นี้ถูกใช้แล้ว")

    if "email" in data and str(data["email"]) != user.email:
        exists = get_user_by_email(db, str(data["email"]))
        if exists and exists.id != user.id:
            raise ValueError("email นี้ถูกใช้แล้ว")

    # ถ้าส่ง password มา -> hash แล้วเก็บใน hashed_password
    if "password" in data:
        user.hashed_password = hash_password(data["password"])
        data.pop("password")

    # set ค่า field อื่น ๆ
    for k, v in data.items():
        setattr(user, k, v)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user(db, user_id)
    if not user:
        return False

    db.delete(user)
    db.commit()
    return True
```

#### API: Add PATCH/DELETE
```[app/api/users.py]
from app.schemas.user import UserUpdate

@router.patch("/{user_id}", response_model=UserOut)
def patch_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    try:
        user = update_user(db, user_id, payload)
        if not user:
            raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{user_id}", status_code=204)
def remove_user(user_id: int, db: Session = Depends(get_db)):
    ok = delete_user(db, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    return None
```

## Authentication
#### Install Package
```PowerShell(.venv)
pip install "python-jose[cryptography]"
```

#### Add value in .env
```[.env]
JWT_SECRET_KEY="change-me-to-a-long-random-string"
JWT_ALGORITHM="HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
```

#### Add config for JWT in app/core/config.py
```[app/core/config.py]
jwt_secret_key: str = Field(default="change-me", alias="JWT_SECRET_KEY")
jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
jwt_access_token_expire_minutes: int = Field(default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
```

#### Create file app/core/jwt.py
```[app/core/jwt.py]
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.core.config import settings

def create_access_token(subject: str, expires_minutes: int | None = None) -> str:
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.jwt_access_token_expire_minutes
    )
    payload = {
        "sub": subject,          # subject = ตัวตน เช่น user_id หรือ username
        "exp": expire,
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError("Token ไม่ถูกต้องหรือหมดอายุ") from e
```

#### Add CRUD find for user (use the episode login/verify token) 
```[app/crud/user.py]
def get_user_by_id(db: Session, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()
```

#### Create Schemas for Auth
```[app/schemas/auth.py]
from pydantic import BaseModel

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

#### Create dependency "fetch user from JWT"
```[app/api/deps.py]
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.core.jwt import decode_access_token
from app.crud.user import get_user_by_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_access_token(token)
        sub = payload.get("sub")
        if not sub:
            raise ValueError()
        user_id = int(sub)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ไม่ถูกต้องหรือหมดอายุ",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="ไม่พบผู้ใช้")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="บัญชีถูกปิดใช้งาน")

    return user
```

#### Create API Login (Out token)
```[app/api/auth.py]
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.auth import TokenOut
from app.crud.user import get_user_by_username
from app.core.security import verify_password
from app.core.jwt import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, form.username)
    if not user:
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    if not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

    token = create_access_token(subject=str(user.id))
    return {"access_token": token, "token_type": "bearer"}
```

#### tied router auth enter app/main.py
```[app/main.py]
from app.api.auth import router as auth_router
app.include_router(auth_router)
```

#### Log endpoint must have Token
```[app/api/users.py]
from app.api.deps import get_current_user

@router.get("", response_model=list[UserOut])
def read_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    q: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),  # ✅ เพิ่มบรรทัดนี้
):
    return list_users(db, skip=skip, limit=limit, q=q)
```