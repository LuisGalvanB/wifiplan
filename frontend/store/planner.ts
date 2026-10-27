import { create } from "zustand";
import type { Wall, PlacedAP, APModel, FloorGeometry, RFSimulationRun } from "@/types";

export type ToolMode = "select" | "draw-wall" | "place-ap" | "pan";
export type ViewMode = "2d" | "3d";
export type LayerKey = "walls" | "aps" | "heatmap" | "scope" | "obstacles";

interface PlannerState {
  // Floor context
  floorId: string | null;
  setFloorId: (id: string) => void;

  // Geometry (loaded from API)
  geometry: FloorGeometry | null;
  setGeometry: (g: FloorGeometry) => void;
  updateWall: (wall: Wall) => void;
  addWall: (wall: Wall) => void;
  removeWall: (id: string) => void;

  // Placed APs
  placedAPs: PlacedAP[];
  setPlacedAPs: (aps: PlacedAP[]) => void;
  addPlacedAP: (ap: PlacedAP) => void;
  updatePlacedAP: (ap: PlacedAP) => void;
  removePlacedAP: (id: string) => void;

  // Selection
  selectedWallId: string | null;
  selectedAPId: string | null;
  selectWall: (id: string | null) => void;
  selectAP: (id: string | null) => void;

  // Tool state
  toolMode: ToolMode;
  setToolMode: (mode: ToolMode) => void;
  selectedAPModel: APModel | null;
  setSelectedAPModel: (m: APModel | null) => void;

  // View
  viewMode: ViewMode;
  setViewMode: (v: ViewMode) => void;
  layers: Record<LayerKey, boolean>;
  toggleLayer: (k: LayerKey) => void;

  // Canvas transform (for PixiJS sync)
  scale: number;
  offsetX: number;
  offsetY: number;
  setTransform: (scale: number, x: number, y: number) => void;

  // Floor plan image
  floorPlanUrl: string | null;
  setFloorPlanUrl: (url: string | null) => void;
  floorPlanWidth: number;
  floorPlanHeight: number;
  setFloorPlanSize: (w: number, h: number) => void;

  // Heatmap
  heatmapUrl: string | null;
  setHeatmapUrl: (url: string | null) => void;
  latestRFRun: RFSimulationRun | null;
  setLatestRFRun: (run: RFSimulationRun | null) => void;
  rfBand: string;
  setRFBand: (b: string) => void;

  // Job polling
  activeJobId: string | null;
  setActiveJobId: (id: string | null) => void;
}

export const usePlannerStore = create<PlannerState>((set) => ({
  floorId: null,
  setFloorId: (id) => set({ floorId: id }),

  geometry: null,
  setGeometry: (g) => set({ geometry: g }),
  updateWall: (wall) =>
    set((s) => ({
      geometry: s.geometry
        ? { ...s.geometry, walls: s.geometry.walls.map((w) => (w.id === wall.id ? wall : w)) }
        : s.geometry,
    })),
  addWall: (wall) =>
    set((s) => ({
      geometry: s.geometry ? { ...s.geometry, walls: [...s.geometry.walls, wall] } : s.geometry,
    })),
  removeWall: (id) =>
    set((s) => ({
      geometry: s.geometry
        ? { ...s.geometry, walls: s.geometry.walls.filter((w) => w.id !== id) }
        : s.geometry,
      selectedWallId: s.selectedWallId === id ? null : s.selectedWallId,
    })),

  placedAPs: [],
  setPlacedAPs: (aps) => set({ placedAPs: aps }),
  addPlacedAP: (ap) => set((s) => ({ placedAPs: [...s.placedAPs, ap] })),
  updatePlacedAP: (ap) =>
    set((s) => ({ placedAPs: s.placedAPs.map((a) => (a.id === ap.id ? ap : a)) })),
  removePlacedAP: (id) =>
    set((s) => ({
      placedAPs: s.placedAPs.filter((a) => a.id !== id),
      selectedAPId: s.selectedAPId === id ? null : s.selectedAPId,
    })),

  selectedWallId: null,
  selectedAPId: null,
  selectWall: (id) => set({ selectedWallId: id, selectedAPId: null }),
  selectAP: (id) => set({ selectedAPId: id, selectedWallId: null }),

  toolMode: "select",
  setToolMode: (mode) => set({ toolMode: mode }),
  selectedAPModel: null,
  setSelectedAPModel: (m) => set({ selectedAPModel: m }),

  viewMode: "2d",
  setViewMode: (v) => set({ viewMode: v }),
  layers: { walls: true, aps: true, heatmap: false, scope: true, obstacles: true },
  toggleLayer: (k) => set((s) => ({ layers: { ...s.layers, [k]: !s.layers[k] } })),

  scale: 1,
  offsetX: 0,
  offsetY: 0,
  setTransform: (scale, x, y) => set({ scale, offsetX: x, offsetY: y }),

  floorPlanUrl: null,
  setFloorPlanUrl: (url) => set({ floorPlanUrl: url }),
  floorPlanWidth: 1200,
  floorPlanHeight: 800,
  setFloorPlanSize: (w, h) => set({ floorPlanWidth: w, floorPlanHeight: h }),

  heatmapUrl: null,
  setHeatmapUrl: (url) => set({ heatmapUrl: url }),
  latestRFRun: null,
  setLatestRFRun: (run) => set({ latestRFRun: run }),
  rfBand: "5",
  setRFBand: (b) => set({ rfBand: b }),

  activeJobId: null,
  setActiveJobId: (id) => set({ activeJobId: id }),
}));
