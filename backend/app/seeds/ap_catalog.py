"""
AP catalog seed data — demo/representative data only.
Models are illustrative of real vendor lineups but are NOT official specs.
Mark is_demo_seed=True on all.
"""
from sqlalchemy.orm import Session
from app.models.ap import APVendor, APModel, AntennaType, MountType


VENDORS_AND_MODELS = [
    {
        "name": "Cisco",
        "slug": "cisco",
        "models": [
            {
                "model_name": "Catalyst 9115AXI",
                "model_number": "C9115AXI",
                "bands_ghz": [2.4, 5],
                "max_spatial_streams": 4,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 17,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 4.0,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6 (802.11ax), 4x4 MIMO",
            },
            {
                "model_name": "Catalyst 9130AXI",
                "model_number": "C9130AXI",
                "bands_ghz": [2.4, 5, 6],
                "max_spatial_streams": 8,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 18,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 5.0,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6E, tri-band, 8x8 MIMO",
            },
        ],
    },
    {
        "name": "Meraki",
        "slug": "meraki",
        "models": [
            {
                "model_name": "MR46",
                "model_number": "MR46",
                "bands_ghz": [2.4, 5],
                "max_spatial_streams": 4,
                "tx_power_min_dbm": 5, "tx_power_max_dbm": 23, "tx_power_default_dbm": 17,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 3.5,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6, cloud-managed",
            },
            {
                "model_name": "MR57",
                "model_number": "MR57",
                "bands_ghz": [2.4, 5, 6],
                "max_spatial_streams": 8,
                "tx_power_min_dbm": 5, "tx_power_max_dbm": 23, "tx_power_default_dbm": 17,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 4.5,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6E, tri-band",
            },
        ],
    },
    {
        "name": "Aruba",
        "slug": "aruba",
        "models": [
            {
                "model_name": "AP-515",
                "model_number": "AP-515",
                "bands_ghz": [2.4, 5],
                "max_spatial_streams": 4,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 22, "tx_power_default_dbm": 17,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 3.6,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6, 802.11ax dual-band",
            },
            {
                "model_name": "AP-635",
                "model_number": "AP-635",
                "bands_ghz": [2.4, 5, 6],
                "max_spatial_streams": 8,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 22, "tx_power_default_dbm": 17,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 5.0,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6E tri-band",
            },
        ],
    },
    {
        "name": "Ruckus",
        "slug": "ruckus",
        "models": [
            {
                "model_name": "R650",
                "model_number": "R650",
                "bands_ghz": [2.4, 5],
                "max_spatial_streams": 4,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 17,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 3.8,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6 with BeamFlex+ adaptive antenna",
            },
            {
                "model_name": "R770",
                "model_number": "R770",
                "bands_ghz": [2.4, 5, 6],
                "max_spatial_streams": 8,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 18,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 5.2,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6E, 12 BeamFlex antennas",
            },
        ],
    },
    {
        "name": "Juniper Mist",
        "slug": "juniper-mist",
        "models": [
            {
                "model_name": "AP43",
                "model_number": "AP43",
                "bands_ghz": [2.4, 5],
                "max_spatial_streams": 4,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 17,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 3.5,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6, Mist AI cloud management",
            },
            {
                "model_name": "AP63",
                "model_number": "AP63",
                "bands_ghz": [2.4, 5, 6],
                "max_spatial_streams": 8,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 18,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 4.8,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6E, AI-driven Mist platform",
            },
        ],
    },
    {
        "name": "Ubiquiti",
        "slug": "ubiquiti",
        "models": [
            {
                "model_name": "UniFi U6 Lite",
                "model_number": "U6-Lite",
                "bands_ghz": [2.4, 5],
                "max_spatial_streams": 4,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 17,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 3.0,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6, entry-level indoor AP",
            },
            {
                "model_name": "UniFi U6 Pro",
                "model_number": "U6-Pro",
                "bands_ghz": [2.4, 5],
                "max_spatial_streams": 8,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 17,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 4.0,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6, 8x8 MU-MIMO",
            },
        ],
    },
    {
        "name": "Fortinet",
        "slug": "fortinet",
        "models": [
            {
                "model_name": "FortiAP 431F",
                "model_number": "FAP-431F",
                "bands_ghz": [2.4, 5],
                "max_spatial_streams": 4,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 17,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 4.0,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6, integrates with FortiGate NGFW",
            },
            {
                "model_name": "FortiAP 631F",
                "model_number": "FAP-631F",
                "bands_ghz": [2.4, 5, 6],
                "max_spatial_streams": 8,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 18,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 5.0,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6E, tri-band, FortiGate integration",
            },
        ],
    },
    {
        "name": "Extreme Networks",
        "slug": "extreme",
        "models": [
            {
                "model_name": "AP460C",
                "model_number": "AP460C",
                "bands_ghz": [2.4, 5],
                "max_spatial_streams": 4,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 17,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 3.5,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6, ExtremeCloud IQ managed",
            },
            {
                "model_name": "AP4000",
                "model_number": "AP4000",
                "bands_ghz": [2.4, 5, 6],
                "max_spatial_streams": 8,
                "tx_power_min_dbm": 6, "tx_power_max_dbm": 23, "tx_power_default_dbm": 18,
                "antenna_type": AntennaType.internal, "antenna_gain_dbi": 5.0,
                "mount_type": MountType.ceiling, "is_indoor": True, "is_outdoor": False,
                "notes": "Wi-Fi 6E, tri-band",
            },
        ],
    },
]


def seed_ap_catalog(db: Session):
    """Idempotent seed — skips vendors/models that already exist."""
    for vd in VENDORS_AND_MODELS:
        vendor = db.query(APVendor).filter(APVendor.slug == vd["slug"]).first()
        if not vendor:
            vendor = APVendor(name=vd["name"], slug=vd["slug"])
            db.add(vendor)
            db.flush()

        for md in vd["models"]:
            existing = db.query(APModel).filter(
                APModel.vendor_id == vendor.id,
                APModel.model_number == md.get("model_number"),
            ).first()
            if not existing:
                model = APModel(
                    vendor_id=vendor.id,
                    is_demo_seed=True,
                    **md,
                )
                db.add(model)

    db.commit()
    print(f"AP catalog seeded: {len(VENDORS_AND_MODELS)} vendors")
