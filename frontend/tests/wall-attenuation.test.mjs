import assert from "node:assert/strict";
import test from "node:test";
import {
  getWallAttenuation,
  isWallMaterial,
  isWifiBand,
  WALL_ATTENUATION_DB,
  WALL_MATERIAL_LABELS,
  WIFI_BANDS,
} from "../components/learn/wallAttenuation.ts";

test("educational wall losses match the effective Wi-Fi planner values for every material and band", () => {
  assert.deepEqual(WIFI_BANDS, ["2.4", "5", "6"]);
  assert.deepEqual(WALL_ATTENUATION_DB, {
    glass: { "2.4": 2, "5": 3.3, "6": 4.2 },
    drywall: { "2.4": 3.5, "5": 5.5, "6": 7.2 },
    wood: { "2.4": 4, "5": 6.6, "6": 8.4 },
    brick: { "2.4": 8, "5": 13.2, "6": 16.8 },
    concrete: { "2.4": 12, "5": 17.6, "6": 21.6 },
    metal: { "2.4": 15, "5": 22, "6": 26.4 },
    unknown: { "2.4": 5, "5": 7.7, "6": 9.6 },
  });

  assert.deepEqual(
    Object.keys(WALL_ATTENUATION_DB).map((material) =>
      WIFI_BANDS.map((band) => getWallAttenuation(material, band)),
    ),
    [
      [2, 3.3, 4.2],
      [3.5, 5.5, 7.2],
      [4, 6.6, 8.4],
      [8, 13.2, 16.8],
      [12, 17.6, 21.6],
      [15, 22, 26.4],
      [5, 7.7, 9.6],
    ],
  );
  assert.equal(WALL_MATERIAL_LABELS.drywall, "Panel de yeso");
  assert.equal(WALL_MATERIAL_LABELS.unknown, "Desconocido");
  assert.equal(isWifiBand("6"), true);
  assert.equal(isWifiBand("60"), false);
  assert.equal(isWallMaterial("wood"), true);
  assert.equal(isWallMaterial("__proto__"), false);
});
