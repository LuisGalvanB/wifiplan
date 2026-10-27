"use client";
import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { usePlannerStore } from "@/store/planner";
import api from "@/lib/api";
import {
  ArrowLeftIcon, CubeIcon, Square2StackIcon,
  CloudArrowUpIcon, BoltIcon, AdjustmentsHorizontalIcon,
  MagnifyingGlassIcon,
} from "@heroicons/react/24/outline";
import { CVReviewPanel } from "./CVReviewPanel";
import { ScaleCalibrationModal } from "./ScaleCalibrationModal";

interface Props { projectId: string; floorId: string; }

export function PlannerTopbar({ projectId, floorId }: Props) {
  const router = useRouter();
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const { viewMode, setViewMode, rfBand, setRFBand, setActiveJobId, geometry } = usePlannerStore();
  const [showCVReview, setShowCVReview] = useState(false);
  const [showCalibration, setShowCalibration] = useState(false);

  // Count pending CV walls
  const pendingCV = (geometry?.walls ?? []).filter(
    (w) => w.source === "cv_detected" && !w.is_accepted
  ).length;

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append("file", file);
      const { data } = await api.post<{ job_id: string; asset_id: string }>(
        `/floors/${floorId}/upload`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      return data;
    },
    onSuccess: (data) => {
      setActiveJobId(data.job_id);
      qc.invalidateQueries({ queryKey: ["assets", floorId] });
    },
  });

  const simulateMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<{ job_id: string }>(
        `/floors/${floorId}/rf/simulate`,
        { band_ghz: rfBand, grid_resolution_px: 10 }
      );
      return data;
    },
    onSuccess: (data) => setActiveJobId(data.job_id),
  });

  const handleFile = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) uploadMutation.mutate(f);
    e.target.value = "";
  }, [uploadMutation]);

  return (
    <>
      <header className="bg-gray-900 border-b border-gray-800 px-4 py-2 flex items-center gap-2 text-white z-10 flex-wrap">
        <button onClick={() => router.push(`/projects/${projectId}`)}
          className="text-gray-400 hover:text-white p-1">
          <ArrowLeftIcon className="w-5 h-5" />
        </button>
        <span className="font-semibold text-sm">📡 WifiPlan</span>
        <span className="text-gray-600">/</span>
        <span className="text-sm text-gray-300">Planner</span>
        <div className="flex-1" />
        <Link href="/learn" className="rounded-lg border border-blue-800 px-2.5 py-1.5 text-xs text-blue-300 transition-colors hover:border-blue-500 hover:text-white">
          Aprende Wi-Fi
        </Link>

        {/* CV review badge */}
        {pendingCV > 0 && (
          <button
            onClick={() => setShowCVReview(true)}
            className="flex items-center gap-1.5 bg-purple-900/60 hover:bg-purple-800 border border-purple-700 px-3 py-1.5 rounded-lg text-sm text-purple-200 transition-colors animate-pulse"
          >
            <AdjustmentsHorizontalIcon className="w-4 h-4" />
            Review {pendingCV} detected walls
          </button>
        )}

        {/* Scale calibration */}
        <button
          onClick={() => setShowCalibration(true)}
          className="flex items-center gap-1.5 bg-gray-700 hover:bg-gray-600 px-3 py-1.5 rounded-lg text-xs text-gray-300 transition-colors"
          title="Calibrate floor plan scale (px/m)"
        >
          <MagnifyingGlassIcon className="w-4 h-4" />
          Scale
        </button>

        {/* RF band selector */}
        <div className="flex items-center gap-1 bg-gray-800 rounded-lg p-1">
          {["2.4", "5", "6"].map((b) => (
            <button key={b} onClick={() => setRFBand(b)}
              className={`px-2 py-0.5 rounded text-xs font-mono transition-colors ${
                rfBand === b ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"
              }`}>{b}G</button>
          ))}
        </div>
        <Link href={`/learn/espectro?band=${encodeURIComponent(rfBand)}`} className="text-xs text-blue-300 hover:text-blue-100" aria-label={`Aprender sobre la banda de ${rfBand} GHz`}>
          Guía de bandas
        </Link>

        {/* RF Simulate */}
        <button onClick={() => simulateMutation.mutate()}
          disabled={simulateMutation.isPending}
          className="flex items-center gap-1.5 bg-green-700 hover:bg-green-600 disabled:opacity-50 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
          title="Run RF heatmap simulation">
          <BoltIcon className="w-4 h-4" />
          {simulateMutation.isPending ? "Running…" : "Simulate RF"}
        </button>

        {/* Upload floor plan */}
        <input ref={fileRef} type="file" accept=".png,.jpg,.jpeg,.pdf,.dxf" className="hidden" onChange={handleFile} />
        <button onClick={() => fileRef.current?.click()}
          disabled={uploadMutation.isPending}
          className="flex items-center gap-1.5 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 px-3 py-1.5 rounded-lg text-sm transition-colors"
          title="Upload floor plan image">
          <CloudArrowUpIcon className="w-4 h-4" />
          {uploadMutation.isPending ? "Uploading…" : "Upload"}
        </button>

        {/* 2D / 3D toggle */}
        <div className="flex items-center bg-gray-800 rounded-lg p-1">
          <button onClick={() => setViewMode("2d")}
            className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
              viewMode === "2d" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"
            }`}>
            <Square2StackIcon className="w-3.5 h-3.5" /> 2D
          </button>
          <button onClick={() => setViewMode("3d")}
            className={`flex items-center gap-1 px-2 py-1 rounded text-xs transition-colors ${
              viewMode === "3d" ? "bg-blue-600 text-white" : "text-gray-400 hover:text-white"
            }`}>
            <CubeIcon className="w-3.5 h-3.5" /> 3D
          </button>
        </div>
      </header>

      {/* CV review slide-over */}
      {showCVReview && <CVReviewPanel onClose={() => setShowCVReview(false)} />}

      {/* Scale calibration modal */}
      {showCalibration && (
        <ScaleCalibrationModal
          floorId={floorId}
          onClose={() => setShowCalibration(false)}
        />
      )}
    </>
  );
}
