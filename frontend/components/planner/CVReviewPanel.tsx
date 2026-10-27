"use client";
import { useState, useMemo } from "react";
import { useMutation } from "@tanstack/react-query";
import { usePlannerStore } from "@/store/planner";
import api from "@/lib/api";
import type { Wall } from "@/types";
import {
  CheckIcon, XMarkIcon, CheckCircleIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/outline";

const MATERIAL_BADGE: Record<string, string> = {
  concrete: "bg-gray-700 text-gray-200",
  brick: "bg-red-900 text-red-200",
  drywall: "bg-yellow-900 text-yellow-200",
  wood: "bg-orange-900 text-orange-200",
  metal: "bg-cyan-900 text-cyan-200",
  glass: "bg-blue-900 text-blue-200",
  unknown: "bg-gray-800 text-gray-400",
};

function ConfidenceBadge({ conf }: { conf: number | null }) {
  if (conf === null) return null;
  const pct = Math.round(conf * 100);
  const color = pct >= 70 ? "text-green-400" : pct >= 45 ? "text-yellow-400" : "text-red-400";
  return <span className={`text-xs font-mono ${color}`}>{pct}%</span>;
}

interface Props {
  onClose: () => void;
}

export function CVReviewPanel({ onClose }: Props) {
  const { geometry, floorId, updateWall, removeWall, selectWall } = usePlannerStore();
  const pendingWalls = useMemo(
    () => (geometry?.walls ?? []).filter((w) => w.source === "cv_detected" && !w.is_accepted),
    [geometry]
  );

  const acceptedCVWalls = useMemo(
    () => (geometry?.walls ?? []).filter((w) => w.source === "cv_detected" && w.is_accepted),
    [geometry]
  );

  const [accepting, setAccepting] = useState<Set<string>>(new Set());
  const [rejecting, setRejecting] = useState<Set<string>>(new Set());

  const acceptMutation = useMutation({
    mutationFn: (wallId: string) =>
      api.patch<Wall>(`/floors/${floorId}/geometry/walls/${wallId}`, { is_accepted: true }).then((r) => r.data),
    onSuccess: (wall) => {
      updateWall(wall);
      setAccepting((s) => { const n = new Set(s); n.delete(wall.id); return n; });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: (wallId: string) =>
      api.delete(`/floors/${floorId}/geometry/walls/${wallId}`),
    onMutate: (wallId) => {
      setRejecting((s) => new Set(s).add(wallId));
    },
    onSuccess: (_, wallId) => {
      removeWall(wallId);
      setRejecting((s) => { const n = new Set(s); n.delete(wallId); return n; });
    },
  });

  const acceptAllMutation = useMutation({
    mutationFn: async () => {
      const results = await Promise.allSettled(
        pendingWalls.map((w) =>
          api.patch<Wall>(`/floors/${floorId}/geometry/walls/${w.id}`, { is_accepted: true }).then((r) => r.data)
        )
      );
      return results
        .filter((r): r is PromiseFulfilledResult<Wall> => r.status === "fulfilled")
        .map((r) => r.value);
    },
    onSuccess: (walls) => {
      walls.forEach((w) => updateWall(w));
    },
  });

  const rejectAllMutation = useMutation({
    mutationFn: async () => {
      await Promise.allSettled(
        pendingWalls.map((w) => api.delete(`/floors/${floorId}/geometry/walls/${w.id}`))
      );
      return pendingWalls.map((w) => w.id);
    },
    onSuccess: (ids) => {
      ids.forEach((id) => removeWall(id));
    },
  });

  return (
    <div className="absolute inset-y-0 right-0 w-72 bg-gray-900 border-l border-gray-700 flex flex-col z-20 shadow-2xl">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-800 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-white text-sm">CV Detection Review</h3>
          <p className="text-xs text-gray-400 mt-0.5">
            {pendingWalls.length} pending · {acceptedCVWalls.length} accepted
          </p>
        </div>
        <button onClick={onClose} className="text-gray-500 hover:text-white">
          <XMarkIcon className="w-5 h-5" />
        </button>
      </div>

      {/* Info banner */}
      <div className="mx-3 mt-3 bg-blue-900/30 border border-blue-800 rounded-lg px-3 py-2 flex gap-2">
        <InformationCircleIcon className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
        <p className="text-xs text-blue-300">
          These walls were detected by computer vision. Review each one — accept to keep,
          reject to discard. You can edit properties after accepting.
        </p>
      </div>

      {/* Bulk actions */}
      {pendingWalls.length > 0 && (
        <div className="mx-3 mt-3 flex gap-2">
          <button
            onClick={() => acceptAllMutation.mutate()}
            disabled={acceptAllMutation.isPending}
            className="flex-1 flex items-center justify-center gap-1.5 bg-green-800 hover:bg-green-700 disabled:opacity-50 text-white text-xs py-2 rounded-lg transition-colors font-medium"
          >
            <CheckCircleIcon className="w-4 h-4" />
            Accept All ({pendingWalls.length})
          </button>
          <button
            onClick={() => rejectAllMutation.mutate()}
            disabled={rejectAllMutation.isPending}
            className="flex-1 flex items-center justify-center gap-1.5 bg-red-900 hover:bg-red-800 disabled:opacity-50 text-white text-xs py-2 rounded-lg transition-colors font-medium"
          >
            <XMarkIcon className="w-4 h-4" />
            Reject All
          </button>
        </div>
      )}

      {/* Wall list */}
      <div className="flex-1 overflow-y-auto mt-3 space-y-1 px-3 pb-3">
        {pendingWalls.length === 0 ? (
          <div className="text-center py-8 text-gray-500 text-sm">
            <CheckCircleIcon className="w-10 h-10 mx-auto mb-2 text-green-700" />
            No pending walls to review.
          </div>
        ) : (
          pendingWalls.map((wall) => {
            const len = Math.round(Math.sqrt(
              (wall.geometry.end.x - wall.geometry.start.x) ** 2 +
              (wall.geometry.end.y - wall.geometry.start.y) ** 2
            ));
            const isAccepting = accepting.has(wall.id) || acceptMutation.isPending;
            const isRejecting = rejecting.has(wall.id);

            return (
              <div
                key={wall.id}
                className="bg-gray-800 border border-gray-700 rounded-lg p-3 hover:border-gray-600 transition-colors cursor-pointer"
                onClick={() => selectWall(wall.id)}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${MATERIAL_BADGE[wall.material] ?? MATERIAL_BADGE.unknown}`}>
                        {wall.material}
                      </span>
                      <ConfidenceBadge conf={wall.confidence} />
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      ({wall.geometry.start.x.toFixed(0)}, {wall.geometry.start.y.toFixed(0)}) →
                      ({wall.geometry.end.x.toFixed(0)}, {wall.geometry.end.y.toFixed(0)})
                      <span className="ml-1 text-gray-600">· {len}px</span>
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setAccepting((s) => new Set(s).add(wall.id));
                      acceptMutation.mutate(wall.id);
                    }}
                    disabled={isAccepting || isRejecting}
                    className="flex-1 flex items-center justify-center gap-1 bg-green-900 hover:bg-green-800 disabled:opacity-40 text-green-300 text-xs py-1.5 rounded transition-colors"
                  >
                    <CheckIcon className="w-3.5 h-3.5" />
                    {isAccepting ? "…" : "Accept"}
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      rejectMutation.mutate(wall.id);
                    }}
                    disabled={isAccepting || isRejecting}
                    className="flex-1 flex items-center justify-center gap-1 bg-red-950 hover:bg-red-900 disabled:opacity-40 text-red-400 text-xs py-1.5 rounded transition-colors"
                  >
                    <XMarkIcon className="w-3.5 h-3.5" />
                    {isRejecting ? "…" : "Reject"}
                  </button>
                </div>
              </div>
            );
          })
        )}

        {/* Accepted CV walls summary */}
        {acceptedCVWalls.length > 0 && (
          <div className="mt-4 pt-3 border-t border-gray-800">
            <p className="text-xs text-gray-500 mb-2 flex items-center gap-1">
              <CheckCircleIcon className="w-3.5 h-3.5 text-green-600" />
              {acceptedCVWalls.length} accepted CV walls
            </p>
            <p className="text-xs text-gray-600">
              These are now editable via the Inspector panel.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
