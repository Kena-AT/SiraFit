import logging
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.api.users import get_current_user
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User
from app.schemas.agent import (
    ExtensionJobCaptureIn,
    ExtensionJobCaptureOut,
    ExtensionProfileOut,
    ExtensionStatusOut,
    ExtensionTokenCreate,
    ExtensionTokenOut,
)
from app.services.extension_service import (
    authenticate_extension_token,
    create_extension_token,
    get_candidate_profile_for_autofill,
    import_extension_capture,
    revoke_extension_token,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def get_agent_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> User:
    """Authenticate agent requests using either an ExtensionToken or a standard JWT."""
    token_str = None
    if authorization and authorization.startswith("Bearer "):
        token_str = authorization[7:].strip()
    elif "access_token" in request.cookies:
        token_str = request.cookies.get("access_token")

    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing extension or authorization token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Extension Token path
    if token_str.startswith("srf_ext_"):
        user = authenticate_extension_token(db, token_str)
        if user and user.is_active:
            return user
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired extension token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2. Standard JWT path (fallback for web dashboard callers)
    try:
        payload = decode_token(token_str)
        user_id = payload.get("sub")
        if user_id:
            import uuid

            user = db.query(User).filter(User.id == uuid.UUID(user_id)).first()
            if user and user.is_active:
                return user
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post(
    "/token",
    response_model=ExtensionTokenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Issue a new revocable extension token",
)
def issue_extension_token(
    payload: ExtensionTokenCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a dedicated token for browser extension authorization."""
    raw_token, record = create_extension_token(
        db=db,
        user_id=current_user.id,
        name=payload.name or "Browser Extension",
        expires_days=payload.expires_days or 30,
    )
    return ExtensionTokenOut(
        token=raw_token,
        token_type="Bearer",
        name=record.name,
        expires_at=record.expires_at,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Revoke active extension token",
)
def logout_extension(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Revoke the extension token provided in the Authorization header."""
    if authorization and authorization.startswith("Bearer "):
        token_str = authorization[7:].strip()
        if token_str.startswith("srf_ext_"):
            revoked = revoke_extension_token(db, token_str)
            if revoked:
                return {"success": True, "message": "Extension token revoked"}
    return {"success": True, "message": "Logged out"}


@router.get(
    "/status",
    response_model=ExtensionStatusOut,
    summary="Verify extension connection and token validity",
)
def get_agent_status(
    current_user: User = Depends(get_agent_user),
):
    """Return connection health and authenticated user metadata for the extension popup."""
    return ExtensionStatusOut(
        connected=True,
        user_id=str(current_user.id),
        user_email=current_user.email,
        user_name=current_user.full_name,
        version="1.0.0",
    )


@router.get(
    "/profile",
    response_model=ExtensionProfileOut,
    summary="Export candidate profile data for form autofill",
)
def get_autofill_profile(
    current_user: User = Depends(get_agent_user),
    db: Session = Depends(get_db),
):
    """Retrieve sanitized profile information strictly required for deterministic form autofill."""
    return get_candidate_profile_for_autofill(db, current_user.id)


@router.post(
    "/import",
    response_model=ExtensionJobCaptureOut,
    status_code=status.HTTP_200_OK,
    summary="Import captured job from browser extension",
)
def import_job_from_extension(
    capture: ExtensionJobCaptureIn,
    current_user: User = Depends(get_agent_user),
    db: Session = Depends(get_db),
):
    """Ingest structured job data captured from a job listing page."""
    return import_extension_capture(db, current_user.id, capture)
