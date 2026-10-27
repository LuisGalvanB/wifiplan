export const WIFI_BANDS = ["2.4", "5", "6"] as const;

export type WifiBand = (typeof WIFI_BANDS)[number];
export type WallMaterial = "glass" | "drywall" | "wood" | "brick" | "concrete" | "metal" | "unknown";

// Effective dB losses: the RF engine applies multipliers 1.0 / 1.1 / 1.2
// to the base material table for 2.4 / 5 / 6 GHz respectively.
export const WALL_ATTENUATION_DB: Record<WallMaterial, Record<WifiBand, number>> = {
  glass: { "2.4": 2, "5": 3.3, "6": 4.2 },
  drywall: { "2.4": 3.5, "5": 5.5, "6": 7.2 },
  wood: { "2.4": 4, "5": 6.6, "6": 8.4 },
  brick: { "2.4": 8, "5": 13.2, "6": 16.8 },
  concrete: { "2.4": 12, "5": 17.6, "6": 21.6 },
  metal: { "2.4": 15, "5": 22, "6": 26.4 },
  unknown: { "2.4": 5, "5": 7.7, "6": 9.6 },
};

export const WALL_MATERIAL_LABELS: Record<WallMaterial, string> = {
  glass: "Vidrio",
  drywall: "Panel de yeso",
  wood: "Madera",
  brick: "Ladrillo",
  concrete: "Concreto",
  metal: "Metal",
  unknown: "Desconocido",
};

export function getWallAttenuation(material: WallMaterial, band: WifiBand): number {
  return WALL_ATTENUATION_DB[material][band];
}

export function isWifiBand(value: unknown): value is WifiBand {
  return typeof value === "string" && (WIFI_BANDS as readonly string[]).includes(value);
}

export function isWallMaterial(value: unknown): value is WallMaterial {
  return typeof value === "string" && Object.prototype.hasOwnProperty.call(WALL_ATTENUATION_DB, value);
}
