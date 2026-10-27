// ── Auth ──────────────────────────────────────────────────────────────────────
export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface Organization {
  id: string;
  name: string;
  slug: string;
  is_active: boolean;
}

// ── Project hierarchy ─────────────────────────────────────────────────────────
export interface Project {
  id: string;
  organization_id: string;
  name: string;
  description: string | null;
  address: string | null;
  created_by: string;
  created_at: string;
  updated_at: string;
}

export interface Building {
  id: string;
  project_id: string;
  name: string;
  created_at: string;
}

export interface Floor {
  id: string;
  building_id: string;
  name: string;
  level: number;
  floor_height_m: number;
  ceiling_height_m: number;
  scale_px_per_m: number | null;
  created_at: string;
}

export interface FloorPlanAsset {
  id: string;
  floor_id: string;
  original_filename: string;
  s3_key: string;
  content_type: string;
  width_px: number | null;
  height_px: number | null;
  file_size_bytes: number | null;
  processing_job_id: string | null;
  created_at: string;
}

// ── Geometry ──────────────────────────────────────────────────────────────────
export type MaterialType = "glass" | "drywall" | "wood" | "brick" | "concrete" | "metal" | "unknown";
export type WallType = "exterior" | "interior" | "partition" | "column" | "unknown";
export type GeometrySource = "manual" | "cv_detected" | "ml_detected" | "imported";
export type OpeningType = "door" | "window" | "opening";
export type ObstacleType = "rack" | "shelf" | "column" | "elevator" | "stairwell" | "hvac" | "generic";

export interface Point { x: number; y: number; }

export interface Wall {
  id: string;
  floor_id: string;
  geometry: { start: Point; end: Point };
  wall_type: WallType;
  material: MaterialType;
  thickness_px: number;
  height_m: number;
  attenuation_2_4ghz_db: number | null;
  attenuation_5ghz_db: number | null;
  attenuation_6ghz_db: number | null;
  source: GeometrySource;
  confidence: number | null;
  is_accepted: boolean;
  created_at: string;
}

export interface Opening {
  id: string;
  floor_id: string;
  wall_id: string | null;
  opening_type: OpeningType;
  geometry: { start: Point; end: Point };
  source: GeometrySource;
  confidence: number | null;
  created_at: string;
}

export interface Obstacle {
  id: string;
  floor_id: string;
  obstacle_type: ObstacleType;
  geometry: { points: Point[] };
  height_m: number;
  material: MaterialType;
  source: GeometrySource;
  confidence: number | null;
  created_at: string;
}

export interface ScopeZone {
  id: string;
  floor_id: string;
  name: string;
  geometry: { points: Point[] };
  source: GeometrySource;
  confidence: number | null;
  created_at: string;
}

export interface FloorGeometry {
  floor_id: string;
  walls: Wall[];
  openings: Opening[];
  obstacles: Obstacle[];
  scope_zones: ScopeZone[];
}

// ── AP Catalog ────────────────────────────────────────────────────────────────
export type AntennaType = "omni" | "directional" | "patch" | "internal";
export type MountType = "ceiling" | "wall" | "desktop" | "outdoor_pole";

export interface APVendor {
  id: string;
  name: string;
  slug: string;
}

export interface APModel {
  id: string;
  vendor_id: string;
  vendor_name: string | null;
  model_name: string;
  model_number: string | null;
  bands_ghz: number[];
  max_spatial_streams: number;
  tx_power_min_dbm: number;
  tx_power_max_dbm: number;
  tx_power_default_dbm: number;
  antenna_type: AntennaType;
  antenna_gain_dbi: number;
  mount_type: MountType;
  is_indoor: boolean;
  is_outdoor: boolean;
  notes: string | null;
}

export interface PlacedAP {
  id: string;
  floor_id: string;
  ap_model_id: string;
  label: string | null;
  x_px: number;
  y_px: number;
  height_m: number;
  tx_power_dbm: number;
  bands_active: number[];
  azimuth_deg: number;
  tilt_deg: number;
  ap_model: APModel | null;
  created_at: string;
  updated_at: string;
}

// ── Jobs ──────────────────────────────────────────────────────────────────────
export type JobStatus = "pending" | "running" | "completed" | "failed" | "cancelled";
export type JobType = "floor_plan_analysis" | "rf_simulation" | "report_generation";

export interface Job {
  id: string;
  job_type: JobType;
  status: JobStatus;
  progress_pct: number;
  progress_message: string | null;
  error_message: string | null;
  result_payload: Record<string, unknown> | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface RFSimulationRun {
  id: string;
  floor_id: string;
  band_ghz: string;
  grid_resolution_px: number;
  heatmap_width: number | null;
  heatmap_height: number | null;
  heatmap_s3_key: string | null;
  coverage_good_pct: number | null;
  coverage_fair_pct: number | null;
  coverage_poor_pct: number | null;
  min_rssi_dbm: number | null;
  max_rssi_dbm: number | null;
  avg_rssi_dbm: number | null;
  created_at: string;
}
