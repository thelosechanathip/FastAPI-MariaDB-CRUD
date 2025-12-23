import re
from pydantic_core import PydanticCustomError


def validate_password_policy(password: str) -> str:
    if len(password) < 8:
        raise PydanticCustomError("password_policy", "รหัสผ่านต้องมีอย่างน้อย 8 ตัวอักษร")

    if not re.search(r"[a-z]", password):
        raise PydanticCustomError("password_policy", "รหัสผ่านต้องมีตัวพิมพ์เล็กอย่างน้อย 1 ตัว")
    if not re.search(r"[A-Z]", password):
        raise PydanticCustomError("password_policy", "รหัสผ่านต้องมีตัวพิมพ์ใหญ่อย่างน้อย 1 ตัว")
    if not re.search(r"[0-9]", password):
        raise PydanticCustomError("password_policy", "รหัสผ่านต้องมีตัวเลขอย่างน้อย 1 ตัว")
    if not re.search(r"[^\w\s]", password):
        raise PydanticCustomError(
            "password_policy", "รหัสผ่านต้องมีอักขระพิเศษอย่างน้อย 1 ตัว (เช่น !@#)"
        )
    if " " in password:
        raise PydanticCustomError("password_policy", "รหัสผ่านห้ามมีช่องว่าง")

    return password
