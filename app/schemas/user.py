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

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> EmailStr:
        # EmailStr เป็น type ที่ validate แล้ว แต่เราจะทำให้เป็น lower เพื่อกันซ้ำ
        return str(v).strip().lower()


class UserCreate(UserBase):
    password: str = Field(max_length=128)
    confirm_password: str = Field(max_length=128)

    # policy check (advance)
    @field_validator("password")
    @classmethod
    def password_policy(cls, v: str) -> str:
        return validate_password_policy(v)

    # cross-field validation: password ต้องตรงกัน
    @model_validator(mode="after")
    def password_match(self):
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

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        if v is None:
            return v
        return str(v).strip().lower()

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
