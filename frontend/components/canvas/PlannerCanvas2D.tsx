//frontend/components/canvas/PlannerCanvas2D.tsx
"use client";
import { useEffect, useRef, useCallback, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { usePlannerStore } from "@/store/planner";
import api from "@/lib/api";
import type { Wall, PlacedAP, Point } from "@/types";

const WALL_COLOR = "#60a5fa";      // blue-400
const WALL_SELECTED = "#f59e0b";   // amber
const WALL_CV = "#a78bfa";         // purple — CV detected, not accepted
const SCOPE_COLOR = "#22c55e";     // green
const AP_COLOR = "#f97316";        // orange
const AP_SELECTED = "#fbbf24";

const MATERIAL_COLORS: Record<string, string> = {
  concrete: "#6b7280", brick: "#dc2626", drywall: "#fbbf24",
  wood: "#d97706", metal: "#06b6d4", glass: "#93c5fd", unknown: "#6b7280",
};

export function PlannerCanvas2D() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const animRef = useRef<number>(0);
  const qc = useQueryClient();

  // State for pan/zoom
  const panRef = useRef({ x: 0, y: 0 });
  const scaleRef = useRef(1);
  const isDraggingRef = useRef(false);
  const dragStartRef = useRef({ x: 0, y: 0 });
  const drawStartRef = useRef<Point | null>(null);
  const drawCurrentRef = useRef<Point | null>(null);
  const draggingAPId = useRef<string | null>(null);
  const [canvasSize, setCanvasSize] = useState({ w: 800, h: 600 });
  
  // ✅ Estado para saber si el plano está cargado
  const [loadedFloorPlanUrl, setLoadedFloorPlanUrl] = useState<string | null>(null);

  const {
    geometry, placedAPs, selectedWallId, selectedAPId,
    toolMode, selectedAPModel, layers, heatmapUrl,
    floorPlanUrl, floorPlanWidth, floorPlanHeight,
    selectWall, selectAP, addWall, addPlacedAP, updatePlacedAP,
    setTransform, floorId,
  } = usePlannerStore();
  const isFloorPlanLoaded = !!floorPlanUrl && loadedFloorPlanUrl === floorPlanUrl;

  // Loaded images
  const floorImgRef = useRef<HTMLImageElement | null>(null);
  const heatmapImgRef = useRef<HTMLImageElement | null>(null);

  // ✅ Cargar el plano y esperar a que esté listo
  useEffect(() => {
    if (!floorPlanUrl) { 
      floorImgRef.current = null; 
      return; 
    }
    
    const img = new Image();
    img.crossOrigin = "anonymous";
    
    img.onload = () => { 
      floorImgRef.current = img;
      setLoadedFloorPlanUrl(floorPlanUrl);
    };
    
    img.onerror = () => {
      setLoadedFloorPlanUrl(null);
    };
    
    img.src = floorPlanUrl;
    
    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [floorPlanUrl]);

  useEffect(() => {
    if (!heatmapUrl) { heatmapImgRef.current = null; return; }
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => { heatmapImgRef.current = img; };
    img.src = heatmapUrl;
  }, [heatmapUrl]);

  // Resize observer
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      setCanvasSize({ w: el.clientWidth, h: el.clientHeight });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // World ↔ screen transforms
  const toWorld = useCallback((sx: number, sy: number): Point => ({
    x: (sx - panRef.current.x) / scaleRef.current,
    y: (sy - panRef.current.y) / scaleRef.current,
  }), []);

  const toScreen = useCallback((wx: number, wy: number) => ({
    x: wx * scaleRef.current + panRef.current.x,
    y: wy * scaleRef.current + panRef.current.y,
  }), []);

  // ── Draw loop ────────────────────────────────────────────────────────────────
  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Background
    ctx.fillStyle = "#111827";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Grid
    const gridStep = 50 * scaleRef.current;
    if (gridStep > 8) {
      ctx.strokeStyle = "#1f2937";
      ctx.lineWidth = 0.5;
      const startX = panRef.current.x % gridStep;
      const startY = panRef.current.y % gridStep;
      for (let x = startX; x < canvas.width; x += gridStep) {
        ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
      }
      for (let y = startY; y < canvas.height; y += gridStep) {
        ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
      }
    }

    const s = scaleRef.current;
    const ox = panRef.current.x;
    const oy = panRef.current.y;

    // ✅ Floor plan image - SOLO dibujar si está cargado
    if (floorImgRef.current && isFloorPlanLoaded) {
      ctx.globalAlpha = 0.85;
      ctx.drawImage(floorImgRef.current, ox, oy, floorPlanWidth * s, floorPlanHeight * s);
      ctx.globalAlpha = 1;
    } else if (floorPlanUrl) {
      // Mostrar mensaje de carga si el plano no está listo
      ctx.fillStyle = "rgba(255,255,255,0.6)";
      ctx.font = "16px Arial";
      ctx.textAlign = "center";
      ctx.fillText("Cargando plano...", canvas.width/2, canvas.height/2);
      return; // No dibujar paredes hasta que el plano esté cargado
    }

    // Heatmap overlay
    if (heatmapImgRef.current && layers.heatmap) {
      ctx.globalAlpha = 0.65;
      ctx.drawImage(heatmapImgRef.current, ox, oy, floorPlanWidth * s, floorPlanHeight * s);
      ctx.globalAlpha = 1;
    }

    // ✅ Solo dibujar paredes si el plano está cargado
    if (!isFloorPlanLoaded) return;

    // Scope zones
    if (layers.scope && geometry?.scope_zones) {
      for (const sz of geometry.scope_zones) {
        const pts = sz.geometry.points;
        if (!pts || pts.length < 2) continue;
        ctx.beginPath();
        const p0 = toScreen(pts[0].x, pts[0].y);
        ctx.moveTo(p0.x, p0.y);
        for (let i = 1; i < pts.length; i++) {
          const p = toScreen(pts[i].x, pts[i].y);
          ctx.lineTo(p.x, p.y);
        }
        ctx.closePath();
        ctx.strokeStyle = SCOPE_COLOR;
        ctx.lineWidth = 2;
        ctx.setLineDash([8, 4]);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }

    // Walls
    if (layers.walls && geometry?.walls) {
      for (const wall of geometry.walls) {
        const start = toScreen(wall.geometry.start.x, wall.geometry.start.y);
        const end = toScreen(wall.geometry.end.x, wall.geometry.end.y);

        const isSelected = wall.id === selectedWallId;
        const isCV = wall.source === "cv_detected" && !wall.is_accepted;

        ctx.beginPath();
        ctx.moveTo(start.x, start.y);
        ctx.lineTo(end.x, end.y);
        ctx.strokeStyle = isSelected ? WALL_SELECTED : isCV ? WALL_CV : MATERIAL_COLORS[wall.material] ?? WALL_COLOR;
        ctx.lineWidth = isSelected ? 3 : wall.thickness_px * s * 0.3 + 1.5;
        ctx.stroke();

        // Endpoint dots on select
        if (isSelected) {
          for (const p of [start, end]) {
            ctx.beginPath();
            ctx.arc(p.x, p.y, 5, 0, Math.PI * 2);
            ctx.fillStyle = WALL_SELECTED;
            ctx.fill();
          }
        }
      }
    }

    // Wall being drawn
    if (toolMode === "draw-wall" && drawStartRef.current && drawCurrentRef.current) {
      const s1 = toScreen(drawStartRef.current.x, drawStartRef.current.y);
      const s2 = toScreen(drawCurrentRef.current.x, drawCurrentRef.current.y);
      ctx.beginPath();
      ctx.moveTo(s1.x, s1.y);
      ctx.lineTo(s2.x, s2.y);
      ctx.strokeStyle = "#fbbf24";
      ctx.lineWidth = 2;
      ctx.setLineDash([6, 3]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    // Placed APs
    if (layers.aps) {
      for (const ap of placedAPs) {
        const pos = toScreen(ap.x_px, ap.y_px);
        const isSelected = ap.id === selectedAPId;
        const r = 10 * Math.max(0.5, s);

        ctx.beginPath();
        ctx.arc(pos.x, pos.y, r, 0, Math.PI * 2);
        ctx.fillStyle = isSelected ? AP_SELECTED : AP_COLOR;
        ctx.fill();
        ctx.strokeStyle = isSelected ? "#fff" : "#92400e";
        ctx.lineWidth = isSelected ? 2 : 1;
        ctx.stroke();

        // WiFi symbol
        if (s > 0.5) {
          ctx.fillStyle = "#fff";
          ctx.font = `${Math.max(8, 10 * s)}px sans-serif`;
          ctx.textAlign = "center";
          ctx.textBaseline = "middle";
          ctx.fillText("📶", pos.x, pos.y);
        }

        // Label
        if (ap.label && s > 0.6) {
          ctx.fillStyle = "#fff";
          ctx.font = `${Math.max(7, 9 * s)}px sans-serif`;
          ctx.textAlign = "center";
          ctx.fillText(ap.label, pos.x, pos.y + r + 8);
        }
      }
    }

    // Heatmap legend
    if (layers.heatmap) {
      drawHeatmapLegend(ctx, canvas.width, canvas.height);
    }

  }, [geometry, placedAPs, selectedWallId, selectedAPId, toolMode, layers, floorPlanWidth, floorPlanHeight, toScreen, isFloorPlanLoaded, floorPlanUrl]);

  // Continuous render loop
  useEffect(() => {
    const loop = () => { draw(); animRef.current = requestAnimationFrame(loop); };
    animRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(animRef.current);
  }, [draw]);

  // ── AP mutations ─────────────────────────────────────────────────────────────
  const placeAPMutation = useMutation({
    mutationFn: (pos: Point) =>
      api.post<PlacedAP>(`/floors/${floorId}/aps`, {
        ap_model_id: selectedAPModel!.id,
        x_px: pos.x, y_px: pos.y,
        tx_power_dbm: selectedAPModel!.tx_power_default_dbm,
        bands_active: selectedAPModel!.bands_ghz,
      }).then((r) => r.data),
    onSuccess: (ap) => addPlacedAP(ap),
  });

  const moveAPMutation = useMutation({
    mutationFn: ({ id, x, y }: { id: string; x: number; y: number }) =>
      api.patch<PlacedAP>(`/floors/${floorId}/aps/${id}`, { x_px: x, y_px: y }).then((r) => r.data),
    onSuccess: (ap) => updatePlacedAP(ap),
  });

  const createWallMutation = useMutation({
    mutationFn: (data: { start: Point; end: Point }) =>
      api.post<Wall>(`/floors/${floorId}/geometry/walls`, {
        geometry: data,
        source: "manual",
      }).then((r) => r.data),
    onSuccess: (wall) => { addWall(wall); qc.invalidateQueries({ queryKey: ["geometry", floorId] }); },
  });

  // ── Hit testing ──────────────────────────────────────────────────────────────
  const hitTestWall = useCallback((wx: number, wy: number): string | null => {
    if (!geometry?.walls) return null;
    const THRESH = 8 / scaleRef.current;
    for (const wall of [...geometry.walls].reverse()) {
      const { start, end } = wall.geometry;
      const dx = end.x - start.x, dy = end.y - start.y;
      const len2 = dx * dx + dy * dy;
      if (len2 === 0) continue;
      const t = Math.max(0, Math.min(1, ((wx - start.x) * dx + (wy - start.y) * dy) / len2));
      const px = start.x + t * dx, py = start.y + t * dy;
      const dist = Math.sqrt((wx - px) ** 2 + (wy - py) ** 2);
      if (dist < THRESH) return wall.id;
    }
    return null;
  }, [geometry]);

  const hitTestAP = useCallback((wx: number, wy: number): string | null => {
    const THRESH = 16 / scaleRef.current;
    for (const ap of [...placedAPs].reverse()) {
      const dist = Math.sqrt((wx - ap.x_px) ** 2 + (wy - ap.y_px) ** 2);
      if (dist < THRESH) return ap.id;
    }
    return null;
  }, [placedAPs]);

  // ── Mouse handlers ────────────────────────────────────────────────────────────
  const onMouseDown = useCallback((e: React.MouseEvent) => {
    const world = toWorld(e.nativeEvent.offsetX, e.nativeEvent.offsetY);

    if (toolMode === "pan") {
      isDraggingRef.current = true;
      dragStartRef.current = { x: e.nativeEvent.clientX - panRef.current.x, y: e.nativeEvent.clientY - panRef.current.y };
      return;
    }

    if (toolMode === "place-ap" && selectedAPModel) {
      placeAPMutation.mutate(world);
      return;
    }

    if (toolMode === "draw-wall") {
      drawStartRef.current = world;
      drawCurrentRef.current = world;
      return;
    }

    if (toolMode === "select") {
      const apId = hitTestAP(world.x, world.y);
      if (apId) {
        selectAP(apId);
        draggingAPId.current = apId;
        return;
      }
      const wallId = hitTestWall(world.x, world.y);
      selectWall(wallId);
    }
  }, [toolMode, selectedAPModel, toWorld, hitTestAP, hitTestWall, selectAP, selectWall, placeAPMutation]);

  const onMouseMove = useCallback((e: React.MouseEvent) => {
    const world = toWorld(e.nativeEvent.offsetX, e.nativeEvent.offsetY);

    if (toolMode === "pan" && isDraggingRef.current) {
      panRef.current = {
        x: e.nativeEvent.clientX - dragStartRef.current.x,
        y: e.nativeEvent.clientY - dragStartRef.current.y,
      };
      setTransform(scaleRef.current, panRef.current.x, panRef.current.y);
      return;
    }

    if (toolMode === "draw-wall" && drawStartRef.current) {
      drawCurrentRef.current = world;
      return;
    }

    if (toolMode === "select" && draggingAPId.current) {
      const ap = placedAPs.find((a) => a.id === draggingAPId.current);
      if (ap) {
        updatePlacedAP({ ...ap, x_px: world.x, y_px: world.y });
      }
    }
  }, [toolMode, toWorld, placedAPs, updatePlacedAP, setTransform]);

  const onMouseUp = useCallback((e: React.MouseEvent) => {
    const world = toWorld(e.nativeEvent.offsetX, e.nativeEvent.offsetY);

    if (toolMode === "pan") { isDraggingRef.current = false; return; }

    if (toolMode === "draw-wall" && drawStartRef.current) {
      const start = drawStartRef.current;
      drawStartRef.current = null;
      drawCurrentRef.current = null;
      const dx = world.x - start.x, dy = world.y - start.y;
      if (Math.sqrt(dx * dx + dy * dy) > 5) {
        createWallMutation.mutate({ start, end: world });
      }
      return;
    }

    if (draggingAPId.current) {
      const apId = draggingAPId.current;
      draggingAPId.current = null;
      const ap = placedAPs.find((a) => a.id === apId);
      if (ap) {
        moveAPMutation.mutate({ id: apId, x: ap.x_px, y: ap.y_px });
      }
    }
  }, [toolMode, toWorld, createWallMutation, placedAPs, moveAPMutation]);

  const onWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    const factor = e.deltaY < 0 ? 1.1 : 0.9;
    const newScale = Math.max(0.05, Math.min(10, scaleRef.current * factor));
    const mx = e.nativeEvent.offsetX;
    const my = e.nativeEvent.offsetY;
    panRef.current = {
      x: mx - (mx - panRef.current.x) * (newScale / scaleRef.current),
      y: my - (my - panRef.current.y) * (newScale / scaleRef.current),
    };
    scaleRef.current = newScale;
    setTransform(newScale, panRef.current.x, panRef.current.y);
  }, [setTransform]);

  const cursor =
    toolMode === "pan" ? "grab"
    : toolMode === "draw-wall" ? "crosshair"
    : toolMode === "place-ap" ? "cell"
    : "default";

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden">
      <canvas
        ref={canvasRef}
        width={canvasSize.w}
        height={canvasSize.h}
        style={{ cursor, display: "block", width: "100%", height: "100%" }}
        onMouseDown={onMouseDown}
        onMouseMove={onMouseMove}
        onMouseUp={onMouseUp}
        onWheel={onWheel}
      />
      <div className="absolute bottom-3 left-3 text-xs text-gray-500 bg-gray-900/70 px-2 py-1 rounded">
        Scroll to zoom · Drag to pan (Pan tool) · {toolMode}
      </div>
    </div>
  );
}

function drawHeatmapLegend(ctx: CanvasRenderingContext2D, w: number, h: number) {
  const lw = 120, lh = 12;
  const lx = w - lw - 16, ly = h - 36;

  const grad = ctx.createLinearGradient(lx, 0, lx + lw, 0);
  grad.addColorStop(0, "rgba(220,38,38,0.8)");
  grad.addColorStop(0.5, "rgba(234,179,8,0.8)");
  grad.addColorStop(1, "rgba(34,197,94,0.8)");

  ctx.fillStyle = "rgba(17,24,39,0.7)";
  ctx.roundRect(lx - 8, ly - 4, lw + 16, lh + 22, 6);
  ctx.fill();

  ctx.fillStyle = grad;
  ctx.fillRect(lx, ly, lw, lh);
  ctx.strokeStyle = "#374151";
  ctx.lineWidth = 1;
  ctx.strokeRect(lx, ly, lw, lh);

  ctx.fillStyle = "#9ca3af";
  ctx.font = "10px sans-serif";
  ctx.textAlign = "left";
  ctx.fillText("< -75", lx, ly + lh + 12);
  ctx.textAlign = "right";
  ctx.fillText("> -65 dBm", lx + lw, ly + lh + 12);
}