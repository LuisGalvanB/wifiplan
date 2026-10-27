from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError

from app.db.base import get_db
from app.core.security import decode_token
from app.models.tenant import User, Membership, MembershipRole
from app.models.project import Project, Building, Floor

bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token invalid or expired")

    user = db.query(User).filter(User.id == user_id, User.is_active).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_membership(
    org_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Membership:
    """Verify user is a member of the given organization."""
    membership = db.query(Membership).filter(
        Membership.organization_id == org_id,
        Membership.user_id == user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return membership


def require_role(*roles: MembershipRole):
    def dependency(membership: Membership = Depends(get_membership)) -> Membership:
        if membership.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return membership
    return dependency


_ROLE_LEVEL = {
    MembershipRole.viewer: 0,
    MembershipRole.editor: 1,
    MembershipRole.admin: 2,
}


def require_organization_access(
    org_id: str,
    user: User,
    db: Session,
    minimum_role: MembershipRole = MembershipRole.viewer,
) -> Membership:
    """Authorize organization access using the viewer < editor < admin hierarchy."""
    membership = get_membership_for_user(org_id, user, db)
    if _ROLE_LEVEL[membership.role] < _ROLE_LEVEL[minimum_role]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return membership


def get_membership_for_user(org_id: str, user: User, db: Session) -> Membership:
    membership = db.query(Membership).filter(
        Membership.organization_id == org_id,
        Membership.user_id == user.id,
    ).first()
    if not membership:
        raise HTTPException(status_code=403, detail="Not a member of this organization")
    return membership


def require_project_access(
    project_id: str,
    org_id: str,
    user: User,
    db: Session,
    minimum_role: MembershipRole = MembershipRole.viewer,
) -> Project:
    """Resolve a project only through its organization and authorize that ancestry."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.organization_id == org_id,
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    require_organization_access(org_id, user, db, minimum_role)
    return project


def require_floor_access(
    floor_id: str,
    user: User,
    db: Session,
    minimum_role: MembershipRole = MembershipRole.viewer,
) -> Floor:
    """Resolve a floor through building/project ancestry, then authorize its tenant."""
    floor = (
        db.query(Floor)
        .join(Building, Building.id == Floor.building_id)
        .join(Project, Project.id == Building.project_id)
        .filter(Floor.id == floor_id)
        .first()
    )
    if not floor:
        raise HTTPException(status_code=404, detail="Floor not found")
    organization_id = (
        db.query(Project.organization_id)
        .join(Building, Building.project_id == Project.id)
        .filter(Building.id == floor.building_id)
        .scalar()
    )
    if organization_id is None:
        raise HTTPException(status_code=404, detail="Floor not found")
    require_organization_access(str(organization_id), user, db, minimum_role)
    return floor
