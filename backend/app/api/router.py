from fastapi import APIRouter
from app.api import auth, users, profiles, jobs, applications, resumes, cover_letters, dashboard, settings

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(settings.router, prefix="/users", tags=["settings"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(cover_letters.router, prefix="/cover-letters", tags=["cover-letters"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
