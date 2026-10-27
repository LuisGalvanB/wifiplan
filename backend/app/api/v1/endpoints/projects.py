from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.base import get_db
from app.api.deps import (
    get_current_user, require_organization_access, require_project_access,
)
from app.models.tenant import User, MembershipRole
from app.models.project import Project, Building, Floor
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectOut,
    BuildingCreate, BuildingOut,
    FloorCreate, FloorUpdate, FloorOut,
)

router = APIRouter(prefix="/orgs/{org_id}", tags=["projects"])


# ── Projects ──────────────────────────────────────────────────────────────────

@router.get("/projects", response_model=List[ProjectOut])
def list_projects(
    org_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_organization_access(org_id, user, db)
    return db.query(Project).filter(Project.organization_id == org_id).all()


@router.post("/projects", response_model=ProjectOut, status_code=201)
def create_project(
    org_id: str,
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_organization_access(org_id, user, db, MembershipRole.editor)
    project = Project(
        organization_id=org_id,
        name=payload.name,
        description=payload.description,
        address=payload.address,
        created_by=user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(
    org_id: str,
    project_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    proj = require_project_access(project_id, org_id, user, db)
    return proj


@router.patch("/projects/{project_id}", response_model=ProjectOut)
def update_project(
    org_id: str,
    project_id: str,
    payload: ProjectUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    proj = require_project_access(project_id, org_id, user, db, MembershipRole.editor)
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(proj, k, v)
    db.commit()
    db.refresh(proj)
    return proj


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(
    org_id: str,
    project_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    proj = require_project_access(project_id, org_id, user, db, MembershipRole.admin)
    db.delete(proj)
    db.commit()


# ── Buildings ─────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/buildings", response_model=List[BuildingOut])
def list_buildings(
    org_id: str,
    project_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_project_access(project_id, org_id, user, db)
    return db.query(Building).filter(Building.project_id == project_id).all()


@router.post("/projects/{project_id}/buildings", response_model=BuildingOut, status_code=201)
def create_building(
    org_id: str,
    project_id: str,
    payload: BuildingCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_project_access(project_id, org_id, user, db, MembershipRole.editor)
    b = Building(project_id=project_id, name=payload.name)
    db.add(b)
    db.commit()
    db.refresh(b)
    return b


# ── Floors ─────────────────────────────────────────────────────────────────────

@router.get("/projects/{project_id}/buildings/{building_id}/floors", response_model=List[FloorOut])
def list_floors(
    org_id: str,
    project_id: str,
    building_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_project_access(project_id, org_id, user, db)
    building = db.query(Building).filter(
        Building.id == building_id, Building.project_id == project_id,
    ).first()
    if not building:
        raise HTTPException(404, "Building not found")
    return db.query(Floor).filter(Floor.building_id == building_id).order_by(Floor.level).all()


@router.post("/projects/{project_id}/buildings/{building_id}/floors", response_model=FloorOut, status_code=201)
def create_floor(
    org_id: str,
    project_id: str,
    building_id: str,
    payload: FloorCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_project_access(project_id, org_id, user, db, MembershipRole.editor)
    building = db.query(Building).filter(
        Building.id == building_id, Building.project_id == project_id,
    ).first()
    if not building:
        raise HTTPException(404, "Building not found")
    f = Floor(building_id=building_id, **payload.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@router.patch("/projects/{project_id}/buildings/{building_id}/floors/{floor_id}", response_model=FloorOut)
def update_floor(
    org_id: str,
    project_id: str,
    building_id: str,
    floor_id: str,
    payload: FloorUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_project_access(project_id, org_id, user, db, MembershipRole.editor)
    building = db.query(Building).filter(
        Building.id == building_id, Building.project_id == project_id,
    ).first()
    if not building:
        raise HTTPException(404, "Building not found")
    f = db.query(Floor).filter(Floor.id == floor_id, Floor.building_id == building_id).first()
    if not f:
        raise HTTPException(404, "Floor not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(f, k, v)
    db.commit()
    db.refresh(f)
    return f
