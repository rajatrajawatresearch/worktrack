from fastapi import APIRouter

from app.api.v1 import (
    attendance,
    auth,
    companies,
    dashboard,
    employees,
    me,
    reports,
    system,
)

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(attendance.router)
api_router.include_router(employees.router)
api_router.include_router(companies.router)
api_router.include_router(dashboard.router)
api_router.include_router(reports.router)
api_router.include_router(system.router)
