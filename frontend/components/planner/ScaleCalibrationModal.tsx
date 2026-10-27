"use client";
import { useState, useCallback, useRef, useEffect } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { usePlannerStore } from "@/store/planner";
import api from "@/lib/api";
import type { Floor } from "@/types";
import { XMarkIcon, ArrowsPointingOutIcon } from "@heroicons/react/24/outline";

interface Props {
  floorId: string;
  onClose: () => void;
}

type CalibStep = "idle" | "picking-p1" | "picking-p2" | "entering-distance";

export function ScaleCalibrationModal({ floorId, onClose }: Props) {
  const qc = useQueryClient();
  const [step, setStep] = useState<CalibStep>("idle");
  const [p1, setP1] = useState<{ x: number; y: number } | null>(null);
  const [p2, setP2] = useState<{ x: number; y: number } | null>(null);
  const [distanceM, setDistanceM] = useState("10");
  const [imageError, setImageError] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement | null>(null);

  const { floorPlanUrl } = usePlannerStore();

  const drawPreview = useCallback((img: HTMLImageElement | null, pt1: typeof p1, pt2: typeof p2) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw floor plan scaled to fit canvas
    if (img) {
      const scale = Math.min(canvas.width / img.width, canvas.height / img.height);
      const dw = img.width * scale, dh = img.height * scale;
      const dx = (canvas.width - dw) / 2, dy = (canvas.height - dh) / 2;
      ctx.drawImage(img, dx, dy, dw, dh);

      // Draw calibration points
      const toCanvas = (pt: { x: number; y: number }) => ({
        x: dx + pt.x * scale,
        y: dy + pt.y * scale,
      });

      if (pt1) {
        const cp = toCanvas(pt1);
        ctx.beginPath();
        ctx.arc(cp.x, cp.y, 6, 0, Math.PI * 2);
        ctx.fillStyle = "#22c55e";
        ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.font = "11px sans-serif";
        ctx.fillText("P1", cp.x + 8, cp.y - 4);
      }
      if (pt2) {
        const cp = toCanvas(pt2);
        ctx.beginPath();
        ctx.arc(cp.x, cp.y, 6, 0, Math.PI * 2);
        ctx.fillStyle = "#f97316";
        ctx.fill();
        ctx.fillStyle = "#fff";
        ctx.font = "11px sans-serif";
        ctx.fillText("P2", cp.x + 8, cp.y - 4);
      }
      if (pt1 && pt2) {
        const c1 = toCanvas(pt1), c2 = toCanvas(pt2);
        ctx.beginPath();
        ctx.moveTo(c1.x, c1.y);
        ctx.lineTo(c2.x, c2.y);
        ctx.strokeStyle = "#fbbf24";
        ctx.lineWidth = 2;
        ctx.setLineDash([4, 3]);
        ctx.stroke();
        ctx.setLineDash([]);
        // Distance label
        const mx = (c1.x + c2.x) / 2, my = (c1.y + c2.y) / 2;
        ctx.fillStyle = "#fbbf24";
        ctx.font = "bold 11px sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("? m", mx, my - 8);
        ctx.textAlign = "left";
      }
    }
  }, []);

  useEffect(() => {
    if (!floorPlanUrl) {
      imgRef.current = null;
      return;
    }
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => {
      imgRef.current = img;
      setImageError(null);
      drawPreview(img, null, null);
    };
    img.onerror = () => {
      imgRef.current = null;
      setImageError("No se pudo cargar el plano para calibrar la escala.");
    };
    img.src = floorPlanUrl;
    return () => {
      img.onload = null;
      img.onerror = null;
    };
  }, [floorPlanUrl, drawPreview]);

  const handleCanvasClick = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !imgRef.current) return;
    const rect = canvas.getBoundingClientRect();
    const cx = (e.clientX - rect.left) * (canvas.width / rect.width);
    const cy = (e.clientY - rect.top) * (canvas.height / rect.height);
    const img = imgRef.current;
    const s = Math.min(canvas.width / img.width, canvas.height / img.height);
    const dx = (canvas.width - img.width * s) / 2;
    const dy = (canvas.height - img.height * s) / 2;
    const worldX = (cx - dx) / s;
    const worldY = (cy - dy) / s;

    if (step === "picking-p1") {
      setP1({ x: worldX, y: worldY });
      setStep("picking-p2");
      drawPreview(imgRef.current, { x: worldX, y: worldY }, p2);
    } else if (step === "picking-p2") {
      setP2({ x: worldX, y: worldY });
      setStep("entering-distance");
      drawPreview(imgRef.current, p1, { x: worldX, y: worldY });
    }
  };

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (!p1 || !p2) throw new Error("Pick two points first");
      const distPx = Math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2);
      const meters = parseFloat(distanceM);
      if (isNaN(meters) || meters <= 0) throw new Error("Invalid distance");
      const pxPerM = distPx / meters;
      // Use the direct floor PATCH route (no org/project/building context needed)
      await api.patch<Floor>(`/floors/${floorId}`, { scale_px_per_m: pxPerM });
      return pxPerM;
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["floors"] });
      onClose();
    },
  });

  const pxDist = p1 && p2
    ? Math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2).toFixed(1)
    : null;
  const computedScale = p1 && p2 && parseFloat(distanceM) > 0
    ? (Math.sqrt((p2.x - p1.x) ** 2 + (p2.y - p1.y) ** 2) / parseFloat(distanceM)).toFixed(2)
    : null;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-2xl w-full max-w-lg shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-800">
          <div className="flex items-center gap-2">
            <ArrowsPointingOutIcon className="w-5 h-5 text-blue-400" />
            <h2 className="font-semibold text-white">Scale Calibration</h2>
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-white">
            <XMarkIcon className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-4">
          {/* Instructions */}
          <div className="bg-gray-800 rounded-lg px-4 py-3 text-sm text-gray-300">
            {step === "idle" && "Click a button below to start picking calibration points on the floor plan."}
            {step === "picking-p1" && "🟢 Click Point 1 on the canvas — a known start of a measured distance."}
            {step === "picking-p2" && "🟠 Click Point 2 on the canvas — the end of the same measured distance."}
            {step === "entering-distance" && "Enter the real-world distance between your two points in meters."}
          </div>

          {/* Mini canvas preview */}
          {floorPlanUrl ? (
            <>
              <canvas
                ref={canvasRef}
                width={420}
                height={220}
                aria-label="Vista previa del plano para seleccionar dos puntos de calibración"
                className={`w-full rounded-lg border border-gray-700 ${
                  step === "picking-p1" || step === "picking-p2"
                    ? "cursor-crosshair border-blue-500"
                    : "cursor-default"
                }`}
                onClick={handleCanvasClick}
              />
              {imageError && <p role="alert" className="text-sm text-red-300">{imageError}</p>}
            </>
          ) : (
            <div className="h-40 rounded-lg border border-gray-700 bg-gray-800 flex items-center justify-center text-gray-500 text-sm">
              Upload a floor plan first to calibrate scale.
            </div>
          )}

          {/* Step buttons / inputs */}
          <div className="space-y-3">
            {step === "idle" && (
              <button
                onClick={() => { setP1(null); setP2(null); setStep("picking-p1"); }}
                className="w-full bg-blue-700 hover:bg-blue-600 text-white py-2.5 rounded-lg text-sm font-medium transition-colors"
              >
                Pick Two Points
              </button>
            )}

            {(step === "picking-p1" || step === "picking-p2") && (
              <button
                onClick={() => { setP1(null); setP2(null); setStep("idle"); }}
                className="w-full border border-gray-700 hover:border-gray-500 text-gray-400 hover:text-white py-2.5 rounded-lg text-sm transition-colors"
              >
                Cancel
              </button>
            )}

            {step === "entering-distance" && (
              <div className="space-y-3">
                <div className="flex items-center gap-3 bg-gray-800 rounded-lg px-4 py-3 text-sm">
                  <span className="text-gray-400">Distance on plan:</span>
                  <span className="text-white font-mono">{pxDist} px</span>
                </div>
                <div>
                  <label className="block text-xs text-gray-400 mb-1">
                    Real-world distance (meters)
                  </label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    value={distanceM}
                    onChange={(e) => setDistanceM(e.target.value)}
                    autoFocus
                    className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
                    placeholder="e.g. 10"
                  />
                </div>
                {computedScale && (
                  <div className="bg-green-900/30 border border-green-800 rounded-lg px-3 py-2 text-sm">
                    <span className="text-green-400">Scale: </span>
                    <span className="text-white font-mono">{computedScale} px/m</span>
                    <span className="text-gray-500 ml-2">
                      (1m = {computedScale}px)
                    </span>
                  </div>
                )}
                <div className="flex gap-2">
                  <button
                    onClick={() => saveMutation.mutate()}
                    disabled={!computedScale || saveMutation.isPending}
                    className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white py-2.5 rounded-lg text-sm font-medium transition-colors"
                  >
                    {saveMutation.isPending ? "Saving…" : "Save Scale"}
                  </button>
                  <button
                    onClick={() => { setP1(null); setP2(null); setStep("idle"); drawPreview(imgRef.current, null, null); }}
                    className="border border-gray-700 hover:border-gray-500 text-gray-400 hover:text-white px-4 rounded-lg text-sm transition-colors"
                  >
                    Redo
                  </button>
                </div>
                {saveMutation.isError && (
                  <p className="text-red-400 text-xs">{(saveMutation.error as Error).message}</p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
