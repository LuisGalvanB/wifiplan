"use client";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { usePlannerStore } from "@/store/planner";
import { useJobPolling } from "@/hooks/useJobPolling";
import type { Job } from "@/types";
import api from "@/lib/api";

function JobBannerInner({ jobId, onComplete, onFailed }: {
  jobId: string;
  onComplete: (j: Job) => void;
  onFailed: (j: Job) => void;
}) {
  const [job, setJob] = useState<Job | null>(null);

  useJobPolling({
    jobId,
    onProgress: (j) => setJob(j),
    onComplete,
    onFailed,
  });

  const pct = job?.progress_pct ?? 0;
  const msg = job?.progress_message ?? "Processing…";

  return (
    <div className="bg-blue-900/80 border-b border-blue-700 px-4 py-1.5 flex items-center gap-3">
      <div className="w-3 h-3 rounded-full bg-blue-400 animate-pulse shrink-0" />
      <div className="flex-1">
        <div className="flex items-center justify-between mb-0.5">
          <span className="text-xs text-blue-200">{msg}</span>
          <span className="text-xs text-blue-400 font-mono">{pct}%</span>
        </div>
        <div className="h-1 bg-blue-900 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-400 rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>
    </div>
  );
}

export function JobProgressBanner() {
  const { activeJobId, setActiveJobId, floorId, setHeatmapUrl } = usePlannerStore();
  const qc = useQueryClient();
  const [jobError, setJobError] = useState<string | null>(null);

  const handleComplete = async (job: Job) => {
    setActiveJobId(null);
    setJobError(null);
    if (job.job_type === "floor_plan_analysis") {
      qc.invalidateQueries({ queryKey: ["geometry", floorId] });
      qc.invalidateQueries({ queryKey: ["assets", floorId] });
    }
    if (job.job_type === "rf_simulation" && job.result_payload?.run_id) {
      qc.invalidateQueries({ queryKey: ["rf-runs", floorId] });
      try {
        const { data } = await api.get<{ url: string }>(
          `/floors/${floorId}/rf/runs/${job.result_payload.run_id}/heatmap-url`
        );
        setHeatmapUrl(data.url);
        // Auto-enable heatmap layer
        usePlannerStore.setState((s) => ({ layers: { ...s.layers, heatmap: true } }));
      } catch {
        setJobError("El cálculo terminó, pero no se pudo cargar el mapa de calor.");
      }
    }
  };

  if (!activeJobId) {
    return jobError ? <p role="alert" className="border-b border-red-800 bg-red-950 px-4 py-2 text-sm text-red-200">{jobError}</p> : null;
  }

  return (
    <>
      {jobError && <p role="alert" className="border-b border-red-800 bg-red-950 px-4 py-2 text-sm text-red-200">{jobError}</p>}
      <JobBannerInner
        jobId={activeJobId}
        onComplete={handleComplete}
        onFailed={(job) => {
          setActiveJobId(null);
          setJobError(job.error_message ?? "El trabajo de procesamiento ha fallado.");
        }}
      />
    </>
  );
}
