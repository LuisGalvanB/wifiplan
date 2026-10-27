from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime
from app.models.ap import AntennaType, MountType


class APVendorOut(BaseModel):
    id: uuid.UUID
    name: str
    slug: str

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class APModelOut(BaseModel):
    id: uuid.UUID
    vendor_id: uuid.UUID
    vendor_name: str | None = None
    model_name: str
    model_number: str | None
    bands_ghz: list
    max_spatial_streams: int
    tx_power_min_dbm: float
    tx_power_max_dbm: float
    tx_power_default_dbm: float
    antenna_type: AntennaType
    antenna_gain_dbi: float
    mount_type: MountType
    is_indoor: bool
    is_outdoor: bool
    notes: str | None

    model_config = ConfigDict(from_attributes=True, protected_namespaces=())


class PlacedAPCreate(BaseModel):
    ap_model_id: uuid.UUID
    x_px: float
    y_px: float
    height_m: float = 2.5
    tx_power_dbm: float = 17.0
    bands_active: list = []
    label: str | None = None
    azimuth_deg: float = 0.0
    tilt_deg: float = 0.0


class PlacedAPUpdate(BaseModel):
    x_px: float | None = None
    y_px: float | None = None
    height_m: float | None = None
    tx_power_dbm: float | None = None
    bands_active: list | None = None
    label: str | None = None
    azimuth_deg: float | None = None
    tilt_deg: float | None = None


class PlacedAPOut(BaseModel):
    id: uuid.UUID
    floor_id: uuid.UUID
    ap_model_id: uuid.UUID
    label: str | None
    x_px: float
    y_px: float
    height_m: float
    tx_power_dbm: float
    bands_active: list
    azimuth_deg: float
    tilt_deg: float
    ap_model: APModelOut | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
