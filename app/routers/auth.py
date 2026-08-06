"""Local authentication routes (login/logout). Will be replaced by SSO in a later phase."""

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.security import verify_password
from app.config import settings
from app.db import get_db
from app.models import User

router = APIRouter(tags=["Auth"])
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request, error: str | None = None) -> HTMLResponse:
    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
            "error": error,
        },
    )


@router.post("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user = db.query(User).filter(User.username == username.strip().lower()).first()
    if not user or not user.is_active or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "app_name": settings.app_name,
                "app_version": settings.app_version,
                "environment": settings.environment,
                "error": "Invalid username or password.",
            },
            status_code=401,
        )
    request.session.clear()
    request.session["user_id"] = user.id
    request.session["username"] = user.username
    request.session["role"] = user.role.value
    return RedirectResponse(url="/", status_code=303)


@router.get("/logout", include_in_schema=False)
async def logout(request: Request) -> RedirectResponse:
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)
