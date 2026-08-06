"""Session-based authentication and role-based access control dependencies."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Role, User


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Return the logged-in user from the session cookie, or raise 401."""
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


def get_optional_user(request: Request, db: Session = Depends(get_db)) -> User | None:
    """Return the logged-in user, or None. Never raises — safe for nav/templates."""
    user_id = request.session.get("user_id")
    if user_id is None:
        return None
    return db.get(User, user_id)


def require_role(*roles: Role):
    """Dependency factory restricting a route to specific roles."""

    def _checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user

    return _checker


def is_zone_approver(user: User, zone_name: str) -> bool:
    """True if this user may approve requests for the given zone."""
    if user.role == Role.CLOUDOPS_ADMIN:
        return True
    if user.role == Role.ZONE_ADMIN:
        zone = zone_name.lower().rstrip(".")
        return any(scope.zone_name.lower().rstrip(".") == zone for scope in user.zone_scopes)
    return False
