from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.db.deps import get_db

from app.db.session import engine
from app.db.base import Base

from app.api.users import router as users_router
from app.api.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="FastAPI + MariaDB CRUD")

app.include_router(users_router)
app.include_router(auth_router)


# @app.get("/debug-settings")
# def debug_settings():
#     return {
#         "db_host": settings.db_host,
#         "db_port": settings.db_port,
#         "db_name": settings.db_name,
#         "db_user": settings.db_user,
#         "db_password_len": len(settings.db_password),
#         "database_url": (
#             settings.database_url.replace(settings.db_password, "***")
#             if settings.db_password
#             else settings.database_url
#         ),
#     }


@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.app_env, "debug": settings.debug}


@app.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    result = db.execute(text("SELECT 1")).scalar()
    return {"db": "ok", "result": result}
