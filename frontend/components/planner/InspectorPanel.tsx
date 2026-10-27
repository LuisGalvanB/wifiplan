"use client";
import { useMutation } from "@tanstack/react-query";
import Link from "next/link";
import { usePlannerStore } from "@/store/planner";
import api from "@/lib/api";
import type { Wall, PlacedAP } from "@/types";
import { TrashIcon } from "@heroicons/react/24/outline";

export function InspectorPanel() {
  const {
    selectedWallId, selectedAPId, geometry, placedAPs,
    updateWall, removeWall, updatePlacedAP, removePlacedAP, floorId, rfBand,
  } = usePlannerStore();

  const selectedWall = geometry?.walls.find((w) => w.id === selectedWallId);
  const selectedAP = placedAPs.find((a) => a.id === selectedAPId);

  const updateWallMutation = useMutation({
    mutationFn: (data: Partial<Wall>) =>
      api.patch<Wall>(`/floors/${floorId}/geometry/walls/${selectedWallId}`, data).then((r) => r.data),
    onSuccess: (wall) => updateWall(wall),
  });

  const deleteWallMutation = useMutation({
    mutationFn: () => api.delete(`/floors/${floorId}/geometry/walls/${selectedWallId}`),
    onSuccess: () => { if (selectedWallId) removeWall(selectedWallId); },
  });

  const updateAPMutation = useMutation({
    mutationFn: (data: Partial<PlacedAP>) =>
      api.patch<PlacedAP>(`/floors/${floorId}/aps/${selectedAPId}`, data).then((r) => r.data),
    onSuccess: (ap) => updatePlacedAP(ap),
  });

  const deleteAPMutation = useMutation({
    mutationFn: () => api.delete(`/floors/${floorId}/aps/${selectedAPId}`),
    onSuccess: () => { if (selectedAPId) removePlacedAP(selectedAPId); },
  });

  if (!selectedWall && !selectedAP) {
    return (
      <div className="w-56 bg-gray-900 border-l border-gray-800 p-4">
        <p className="text-xs text-gray-500 text-center pt-8">Select an object to inspect</p>
      </div>
    );
  }

  return (
    <div className="w-56 bg-gray-900 border-l border-gray-800 flex flex-col overflow-y-auto">
      <div className="px-3 py-2 border-b border-gray-800">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">
          {selectedWall ? "Wall" : "Access Point"}
        </span>
      </div>

      {selectedWall && (
        <div className="p-3 space-y-3">
          <Row label="Material">
            <select value={selectedWall.material}
              onChange={(e) => updateWallMutation.mutate({ material: e.target.value as Wall["material"] })}
              className="w-full bg-gray-800 border border-gray-700 text-white text-xs rounded px-2 py-1">
              {["glass","drywall","wood","brick","concrete","metal","unknown"].map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </Row>
          <Row label="Type">
            <select value={selectedWall.wall_type}
              onChange={(e) => updateWallMutation.mutate({ wall_type: e.target.value as Wall["wall_type"] })}
              className="w-full bg-gray-800 border border-gray-700 text-white text-xs rounded px-2 py-1">
              {["exterior","interior","partition","column","unknown"].map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </Row>
          <Link
            href={`/learn/muros?material=${encodeURIComponent(selectedWall.material)}&band=${encodeURIComponent(rfBand)}`}
            className="block text-xs leading-relaxed text-blue-300 hover:text-blue-200"
          >
            Aprende cómo influye este material en la señal →
          </Link>
          <Row label="Height (m)">
            <input type="number" step={0.1} value={selectedWall.height_m}
              onChange={(e) => updateWallMutation.mutate({ height_m: parseFloat(e.target.value) })}
              className="w-full bg-gray-800 border border-gray-700 text-white text-xs rounded px-2 py-1" />
          </Row>
          {selectedWall.source !== "manual" && (
            <div className="text-xs text-gray-500">
              Source: {selectedWall.source}
              {selectedWall.confidence != null && (
                <span className="ml-2">Conf: {(selectedWall.confidence * 100).toFixed(0)}%</span>
              )}
            </div>
          )}
          <button onClick={() => deleteWallMutation.mutate()}
            className="w-full flex items-center justify-center gap-1 text-red-400 hover:text-red-300 text-xs py-1.5 border border-red-800 hover:border-red-600 rounded-lg transition-colors">
            <TrashIcon className="w-3.5 h-3.5" /> Delete Wall
          </button>
        </div>
      )}

      {selectedAP && (
        <div className="p-3 space-y-3">
          <Row label="Model">
            <span className="text-xs text-white">{selectedAP.ap_model?.model_name ?? "Unknown"}</span>
          </Row>
          <Row label="Vendor">
            <span className="text-xs text-gray-400">{selectedAP.ap_model?.vendor_name ?? "—"}</span>
          </Row>
          <Row label="Label">
            <input type="text" value={selectedAP.label ?? ""}
              onChange={(e) => updateAPMutation.mutate({ label: e.target.value })}
              className="w-full bg-gray-800 border border-gray-700 text-white text-xs rounded px-2 py-1" />
          </Row>
          <Row label="Tx Power (dBm)">
            <input type="number" step={1}
              min={selectedAP.ap_model?.tx_power_min_dbm ?? 6}
              max={selectedAP.ap_model?.tx_power_max_dbm ?? 23}
              value={selectedAP.tx_power_dbm}
              onChange={(e) => updateAPMutation.mutate({ tx_power_dbm: parseFloat(e.target.value) })}
              className="w-full bg-gray-800 border border-gray-700 text-white text-xs rounded px-2 py-1" />
          </Row>
          <Row label="Height (m)">
            <input type="number" step={0.1} value={selectedAP.height_m}
              onChange={(e) => updateAPMutation.mutate({ height_m: parseFloat(e.target.value) })}
              className="w-full bg-gray-800 border border-gray-700 text-white text-xs rounded px-2 py-1" />
          </Row>
          <Row label="Bands">
            <span className="text-xs text-gray-400">
              {selectedAP.bands_active.map((b) => `${b} GHz`).join(", ")}
            </span>
          </Row>
          <Row label="Position">
            <span className="text-xs text-gray-400">
              ({selectedAP.x_px.toFixed(0)}, {selectedAP.y_px.toFixed(0)}) px
            </span>
          </Row>
          <button onClick={() => deleteAPMutation.mutate()}
            className="w-full flex items-center justify-center gap-1 text-red-400 hover:text-red-300 text-xs py-1.5 border border-red-800 hover:border-red-600 rounded-lg transition-colors">
            <TrashIcon className="w-3.5 h-3.5" /> Remove AP
          </button>
        </div>
      )}
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-xs text-gray-500 mb-1">{label}</label>
      {children}
    </div>
  );
}
