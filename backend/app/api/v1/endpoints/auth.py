from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.tenant import User, Organization, Membership, MembershipRole
from app.schemas.auth import LoginRequest, TokenResponse, RefreshRequest, RegisterRequest, UserOut
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.api.deps import get_current_user
from jose import JWTError
import re

router = APIRouter(prefix="/auth", tags=["auth"])


def _validate_slug(slug: str):
    if not re.match(r"^[a-z0-9\-]+$", slug):
        raise HTTPException(400, "Slug must be lowercase alphanumeric with hyphens only")


@router.post("/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    _validate_slug(payload.org_slug)

    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(400, "Email already registered")

    if db.query(Organization).filter(Organization.slug == payload.org_slug).first():
        raise HTTPException(400, "Organization slug already taken")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.flush()  # get user.id

    org = Organization(name=payload.org_name, slug=payload.org_slug)
    db.add(org)
    db.flush()

    membership = Membership(
        organization_id=org.id,
        user_id=user.id,
        role=MembershipRole.admin,
    )
    db.add(membership)
    db.commit()

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email, User.is_active).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(401, "Invalid credentials")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        data = decode_token(payload.refresh_token)
        if data.get("type") != "refresh":
            raise HTTPException(401, "Invalid refresh token")
        user_id = data["sub"]
    except JWTError:
        raise HTTPException(401, "Token invalid or expired")

    user = db.query(User).filter(User.id == user_id, User.is_active).first()
    if not user:
        raise HTTPException(401, "User not found")

    return TokenResponse(
        access_token=create_access_token(user.id),
        refresh_token=create_refresh_token(user.id),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


class MembershipOut(BaseModel):
    organization_id: str
    organization_name: str
    organization_slug: str
    role: str

    model_config = {"from_attributes": True}


@router.get("/me/memberships")
def my_memberships(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns all organizations the current user belongs to."""
    memberships = db.query(Membership).filter(Membership.user_id == user.id).all()
    result = []
    for m in memberships:
        from app.models.tenant import Organization
        org = db.query(Organization).filter(Organization.id == m.organization_id).first()
        if org:
            result.append({
                "organization_id": str(org.id),
                "organization_name": org.name,
                "organization_slug": org.slug,
                "role": m.role.value,
            })
    return result
