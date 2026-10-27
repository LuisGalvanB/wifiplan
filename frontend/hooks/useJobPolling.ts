"use client";
import { useEffect, useRef, useCallback } from "react";
import api from "@/lib/api";
import type { Job } from "@/types";

interface UseJobPollingOptions {
  jobId: string | null;
  onComplete?: (job: Job) => void;
  onFailed?: (job: Job) => void;
  onProgress?: (job: Job) => void;
  intervalMs?: number;
}

export function useJobPolling({
  jobId,
  onComplete,
  onFailed,
  onProgress,
  intervalMs = 2000,
}: UseJobPollingOptions) {
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stop = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!jobId) { stop(); return; }

    const poll = async () => {
      try {
        const { data: job } = await api.get<Job>(`/jobs/${jobId}`);
        onProgress?.(job);
        if (job.status === "completed") { stop(); onComplete?.(job); }
        else if (job.status === "failed" || job.status === "cancelled") { stop(); onFailed?.(job); }
      } catch { /* network blip — keep polling */ }
    };

    poll();
    timerRef.current = setInterval(poll, intervalMs);
    return stop;
  }, [jobId, intervalMs, stop, onComplete, onFailed, onProgress]);

  return { stop };
}
