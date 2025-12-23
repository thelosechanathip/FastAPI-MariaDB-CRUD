from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.crud.user import create_user, get_user, list_users, update_user, delete_user

from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        user = create_user(db, payload)
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
# READ: list + pagination + search
@router.get("", response_model=list[UserOut])
def read_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    q: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    return list_users(db, skip=skip, limit=limit, q=q)

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
def remove_user(user_id: int ,db: Session = Depends(get_db)):
    ok = delete_user(db, user_id)
    if not ok:
        raise HTTPException(status_code=404, detail="ไม่พบผู้ใช้")
    return None