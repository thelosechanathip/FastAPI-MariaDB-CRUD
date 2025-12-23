from sqlalchemy.orm import Session
from sqlalchemy import select, or_

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
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

def update_user(db: Session, user_id: int, payload: UserUpdate) -> User | None:
    user = get_user(db, user_id)
    if not user:
        return None
    
    # อัปเดตเฉพาะ field ที่ส่งมา
    data = payload.model_dump(exclude_unset=True)

    # ตรวจซ้ำ username/email ถ้าส่งมา
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

    # set ค่า field อื่นๆ
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

def get_user_by_id(db: Session, user_id: int) -> User | None:
    stmt = select(User).where(User.id == user_id)
    return db.execute(stmt).scalar_one_or_none()