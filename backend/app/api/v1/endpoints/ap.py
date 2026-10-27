from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from typing import List

from app.db.base import get_db
from app.api.deps import get_current_user, require_floor_access
from app.models.tenant import User, MembershipRole
from app.models.ap import APVendor, APModel, PlacedAP
from app.schemas.ap import APVendorOut, APModelOut, PlacedAPCreate, PlacedAPUpdate, PlacedAPOut

catalog_router = APIRouter(prefix="/catalog", tags=["ap-catalog"])
placement_router = APIRouter(prefix="/floors/{floor_id}/aps", tags=["ap-placement"])


# ── AP Catalog (read-only for all tenants) ────────────────────────────────────

@catalog_router.get("/vendors", response_model=List[APVendorOut])
def list_vendors(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(APVendor).order_by(APVendor.name).all()


@catalog_router.get("/models", response_model=List[APModelOut])
def list_models(
    vendor_id: str | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = db.query(APModel).options(joinedload(APModel.vendor))
    if vendor_id:
        q = q.filter(APModel.vendor_id == vendor_id)
    models = q.order_by(APModel.model_name).all()
    result = []
    for m in models:
        out = APModelOut.model_validate(m)
        out.vendor_name = m.vendor.name if m.vendor else None
        result.append(out)
    return result


@catalog_router.get("/models/{model_id}", response_model=APModelOut)
def get_model(model_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    m = db.query(APModel).options(joinedload(APModel.vendor)).filter(APModel.id == model_id).first()
    if not m:
        raise HTTPException(404, "AP model not found")
    out = APModelOut.model_validate(m)
    out.vendor_name = m.vendor.name if m.vendor else None
    return out


# ── AP Placement ──────────────────────────────────────────────────────────────

@placement_router.get("", response_model=List[PlacedAPOut])
def list_placed_aps(
    floor_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_floor_access(floor_id, user, db)
    aps = (
        db.query(PlacedAP)
        .options(joinedload(PlacedAP.ap_model).joinedload(APModel.vendor))
        .filter(PlacedAP.floor_id == floor_id)
        .all()
    )
    result = []
    for ap in aps:
        out = PlacedAPOut.model_validate(ap)
        if ap.ap_model:
            model_out = APModelOut.model_validate(ap.ap_model)
            model_out.vendor_name = ap.ap_model.vendor.name if ap.ap_model.vendor else None
            out.ap_model = model_out
        result.append(out)
    return result


@placement_router.post("", response_model=PlacedAPOut, status_code=201)
def place_ap(
    floor_id: str,
    payload: PlacedAPCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_floor_access(floor_id, user, db, MembershipRole.editor)

    model = db.query(APModel).filter(APModel.id == payload.ap_model_id).first()
    if not model:
        raise HTTPException(404, "AP model not found")

    # Default bands to all model bands if not specified
    bands = payload.bands_active if payload.bands_active else model.bands_ghz

    ap = PlacedAP(
        floor_id=floor_id,
        created_by=user.id,
        bands_active=bands,
        **{k: v for k, v in payload.model_dump().items() if k != "bands_active"},
    )
    ap.bands_active = bands
    db.add(ap)
    db.commit()
    db.refresh(ap)

    # Return with model info
    ap_with_model = (
        db.query(PlacedAP)
        .options(joinedload(PlacedAP.ap_model).joinedload(APModel.vendor))
        .filter(PlacedAP.id == ap.id)
        .first()
    )
    out = PlacedAPOut.model_validate(ap_with_model)
    if ap_with_model.ap_model:
        out.ap_model = APModelOut.model_validate(ap_with_model.ap_model)
    return out


@placement_router.patch("/{ap_id}", response_model=PlacedAPOut)
def update_placed_ap(
    floor_id: str,
    ap_id: str,
    payload: PlacedAPUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_floor_access(floor_id, user, db, MembershipRole.editor)
    ap = db.query(PlacedAP).filter(PlacedAP.id == ap_id, PlacedAP.floor_id == floor_id).first()
    if not ap:
        raise HTTPException(404, "Placed AP not found")
    for k, v in payload.model_dump(exclude_none=True).items():
        setattr(ap, k, v)
    db.commit()
    db.refresh(ap)
    out = PlacedAPOut.model_validate(ap)
    return out


@placement_router.delete("/{ap_id}", status_code=204)
def delete_placed_ap(
    floor_id: str,
    ap_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    require_floor_access(floor_id, user, db, MembershipRole.admin)
    ap = db.query(PlacedAP).filter(PlacedAP.id == ap_id, PlacedAP.floor_id == floor_id).first()
    if not ap:
        raise HTTPException(404, "Placed AP not found")
    db.delete(ap)
    db.commit()
