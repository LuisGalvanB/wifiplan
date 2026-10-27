from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db.base import get_db
from app.api.deps import get_current_user, require_floor_access
from app.models.tenant import User, MembershipRole
from app.models.project import Floor
from app.models.geometry import Wall, Opening, Obstacle, ScopeZone
from app.schemas.geometry import (
    WallCreate, WallUpdate, WallOut, WallBulkCreate, WallBulkOut,
    OpeningCreate, OpeningOut,
    ObstacleCreate, ObstacleOut,
    ScopeZoneCreate, ScopeZoneOut,
    FloorGeometryOut,
)

router = APIRouter(prefix="/floors/{floor_id}/geometry", tags=["geometry"])


def _authorize_floor(
    floor_id: str,
    user: User,
    db: Session,
    minimum_role: MembershipRole = MembershipRole.viewer,
) -> Floor:
    return require_floor_access(floor_id, user, db, minimum_role)


# ── Full geometry snapshot ─────────────────────────────────────────────────────

@router.get("", response_model=FloorGeometryOut)
def get_floor_geometry(
    floor_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Returns all geometry for the floor in one response — optimized for planner load."""
    _authorize_floor(floor_id, user, db)
    return FloorGeometryOut(
        floor_id=floor_id,
        walls=db.query(Wall).filter(Wall.floor_id == floor_id).all(),
        openings=db.query(Opening).filter(Opening.floor_id == floor_id).all(),
        obstacles=db.query(Obstacle).filter(Obstacle.floor_id == floor_id).all(),
        scope_zones=db.query(ScopeZone).filter(ScopeZone.floor_id == floor_id).all(),
    )


# ── Walls ─────────────────────────────────────────────────────────────────────

@router.get("/walls", response_model=List[WallOut])
def list_walls(floor_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _authorize_floor(floor_id, user, db)
    return db.query(Wall).filter(Wall.floor_id == floor_id).all()


@router.post("/walls", response_model=WallOut, status_code=201)
def create_wall(
    floor_id: str,
    payload: WallCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _authorize_floor(floor_id, user, db, MembershipRole.editor)
    w = Wall(floor_id=floor_id, created_by=user.id, **payload.model_dump())
    db.add(w)
    db.commit()
    db.refresh(w)
    return w


@router.post("/walls/bulk", response_model=WallBulkOut, status_code=201)
def bulk_create_walls(
    floor_id: str,
    payload: WallBulkCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Used by CV pipeline results acceptance flow."""
    _authorize_floor(floor_id, user, db, MembershipRole.editor)
    walls = []
    for wd in payload.walls:
        w = Wall(floor_id=floor_id, created_by=user.id, **wd.model_dump())
        db.add(w)
        walls.append(w)
    db.commit()
    for w in walls:
        db.refresh(w)
    return WallBulkOut(created=len(walls), walls=walls)


@router.patch("/walls/{wall_id}", response_model=WallOut)
def update_wall(
    floor_id: str,
    wall_id: str,
    payload: WallUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _authorize_floor(floor_id, user, db, MembershipRole.editor)
    w = db.query(Wall).filter(Wall.id == wall_id, Wall.floor_id == floor_id).first()
    if not w:
        raise HTTPException(404, "Wall not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(w, k, v)
    db.commit()
    db.refresh(w)
    return w


@router.delete("/walls/{wall_id}", status_code=204)
def delete_wall(
    floor_id: str,
    wall_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _authorize_floor(floor_id, user, db, MembershipRole.admin)
    w = db.query(Wall).filter(Wall.id == wall_id, Wall.floor_id == floor_id).first()
    if not w:
        raise HTTPException(404, "Wall not found")
    db.delete(w)
    db.commit()


# ── Openings ──────────────────────────────────────────────────────────────────

@router.get("/openings", response_model=List[OpeningOut])
def list_openings(floor_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _authorize_floor(floor_id, user, db)
    return db.query(Opening).filter(Opening.floor_id == floor_id).all()


@router.post("/openings", response_model=OpeningOut, status_code=201)
def create_opening(
    floor_id: str,
    payload: OpeningCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _authorize_floor(floor_id, user, db, MembershipRole.editor)
    o = Opening(floor_id=floor_id, **payload.model_dump())
    db.add(o)
    db.commit()
    db.refresh(o)
    return o


@router.delete("/openings/{opening_id}", status_code=204)
def delete_opening(
    floor_id: str,
    opening_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _authorize_floor(floor_id, user, db, MembershipRole.admin)
    o = db.query(Opening).filter(Opening.id == opening_id, Opening.floor_id == floor_id).first()
    if not o:
        raise HTTPException(404)
    db.delete(o)
    db.commit()


# ── Obstacles ─────────────────────────────────────────────────────────────────

@router.get("/obstacles", response_model=List[ObstacleOut])
def list_obstacles(floor_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _authorize_floor(floor_id, user, db)
    return db.query(Obstacle).filter(Obstacle.floor_id == floor_id).all()


@router.post("/obstacles", response_model=ObstacleOut, status_code=201)
def create_obstacle(
    floor_id: str,
    payload: ObstacleCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _authorize_floor(floor_id, user, db, MembershipRole.editor)
    ob = Obstacle(floor_id=floor_id, **payload.model_dump())
    db.add(ob)
    db.commit()
    db.refresh(ob)
    return ob


@router.delete("/obstacles/{obstacle_id}", status_code=204)
def delete_obstacle(
    floor_id: str,
    obstacle_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _authorize_floor(floor_id, user, db, MembershipRole.admin)
    ob = db.query(Obstacle).filter(Obstacle.id == obstacle_id, Obstacle.floor_id == floor_id).first()
    if not ob:
        raise HTTPException(404)
    db.delete(ob)
    db.commit()


# ── Scope Zones ───────────────────────────────────────────────────────────────

@router.get("/scope-zones", response_model=List[ScopeZoneOut])
def list_scope_zones(floor_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _authorize_floor(floor_id, user, db)
    return db.query(ScopeZone).filter(ScopeZone.floor_id == floor_id).all()


@router.post("/scope-zones", response_model=ScopeZoneOut, status_code=201)
def create_scope_zone(
    floor_id: str,
    payload: ScopeZoneCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _authorize_floor(floor_id, user, db, MembershipRole.editor)
    sz = ScopeZone(floor_id=floor_id, **payload.model_dump())
    db.add(sz)
    db.commit()
    db.refresh(sz)
    return sz


@router.delete("/scope-zones/{zone_id}", status_code=204)
def delete_scope_zone(
    floor_id: str,
    zone_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _authorize_floor(floor_id, user, db, MembershipRole.admin)
    sz = db.query(ScopeZone).filter(ScopeZone.id == zone_id, ScopeZone.floor_id == floor_id).first()
    if not sz:
        raise HTTPException(404)
    db.delete(sz)
    db.commit()
