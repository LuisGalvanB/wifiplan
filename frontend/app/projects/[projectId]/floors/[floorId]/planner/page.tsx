// frontend/app/projects/[projectId]/floors/[floorId]/planner/page.tsx

"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import dynamic from "next/dynamic";
import { useAuthStore } from "@/store/auth";
import { usePlannerStore } from "@/store/planner";
import api from "@/lib/api";
import type { FloorGeometry, PlacedAP, FloorPlanAsset, RFSimulationRun } from "@/types";
import { PlannerToolbar } from "@/components/planner/PlannerToolbar";
import { PlannerSidebar } from "@/components/planner/PlannerSidebar";
import { PlannerTopbar } from "@/components/planner/PlannerTopbar";
import { InspectorPanel } from "@/components/planner/InspectorPanel";
import { JobProgressBanner } from "@/components/planner/JobProgressBanner";

// Importación dinámica SIN SSR para componentes que usan canvas/Three.js
const PlannerCanvas2D = dynamic(
  () => import("@/components/canvas/PlannerCanvas2D").then((mod) => mod.PlannerCanvas2D),
  { ssr: false, loading: () => <div className="flex-1 bg-gray-900 flex items-center justify-center text-gray-400">Cargando vista 2D...</div> }
);

const PlannerView3D = dynamic(
  () => import("@/components/three/PlannerView3D").then((mod) => mod.PlannerView3D),
  { ssr: false, loading: () => <div className="flex-1 bg-gray-900 flex items-center justify-center text-gray-400">Cargando vista 3D...</div> }
);

export default function PlannerPage() {
  const { floorId, projectId } = useParams<{ floorId: string; projectId: string }>();
  const router = useRouter();
  const { status } = useAuthStore();
  const [assetUrlError, setAssetUrlError] = useState<string | null>(null);
  
  const {
    setFloorId, setGeometry, setPlacedAPs,
    setFloorPlanUrl, setFloorPlanSize,
    viewMode, setLatestRFRun,
  } = usePlannerStore();

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/auth/login");
  }, [status, router]);

  useEffect(() => { setFloorId(floorId); }, [floorId, setFloorId]);

  // Load floor geometry
  const { data: geometry } = useQuery({
    queryKey: ["geometry", floorId],
    queryFn: () => api.get<FloorGeometry>(`/floors/${floorId}/geometry`).then((r) => r.data),
    enabled: status === "authenticated" && !!floorId,
  });
  useEffect(() => { if (geometry) setGeometry(geometry); }, [geometry, setGeometry]);

  // Load placed APs
  const { data: aps } = useQuery({
    queryKey: ["placed-aps", floorId],
    queryFn: () => api.get<PlacedAP[]>(`/floors/${floorId}/aps`).then((r) => r.data),
    enabled: status === "authenticated" && !!floorId,
  });
  useEffect(() => { if (aps) setPlacedAPs(aps); }, [aps, setPlacedAPs]);

  // Load latest floor plan asset URL
  const { data: assets } = useQuery({
    queryKey: ["assets", floorId],
    queryFn: () => api.get<FloorPlanAsset[]>(`/floors/${floorId}/assets`).then((r) => r.data),
    enabled: status === "authenticated" && !!floorId,
  });
  useEffect(() => {
    if (!assets || assets.length === 0) {
      setFloorPlanUrl(null);
      return;
    }
    let active = true;
    const latest = assets[assets.length - 1];
    if (latest.width_px) setFloorPlanSize(latest.width_px, latest.height_px ?? 800);
    api.get<{ url: string }>(`/floors/${floorId}/assets/${latest.id}/url`)
      .then(({ data }) => {
        if (!active) return;
        setAssetUrlError(null);
        setFloorPlanUrl(data.url);
      })
      .catch(() => {
        if (active) setAssetUrlError("No se pudo obtener la URL segura del plano. Vuelve a intentarlo.");
      });
    return () => {
      active = false;
    };
  }, [assets, floorId, setFloorPlanUrl, setFloorPlanSize]);

  // Load latest RF run
  const { data: rfRuns } = useQuery({
    queryKey: ["rf-runs", floorId],
    queryFn: () => api.get<RFSimulationRun[]>(`/floors/${floorId}/rf/runs`).then((r) => r.data),
    enabled: status === "authenticated" && !!floorId,
  });
  useEffect(() => {
    if (rfRuns && rfRuns.length > 0) setLatestRFRun(rfRuns[0]);
  }, [rfRuns, setLatestRFRun]);

  if (status !== "authenticated") return null;

  return (
    <div className="h-screen bg-gray-950 flex flex-col overflow-hidden">
      <PlannerTopbar projectId={projectId} floorId={floorId} />
      {assetUrlError && <p role="alert" className="border-b border-red-800 bg-red-950 px-4 py-2 text-sm text-red-200">{assetUrlError}</p>}
      <JobProgressBanner />
      <div className="flex flex-1 overflow-hidden">
        <PlannerToolbar />
        <div className="flex-1 relative overflow-hidden">
          {viewMode === "2d" ? (
            <PlannerCanvas2D />
          ) : (
            <PlannerView3D />
          )}
        </div>
        <div className="flex">
          <PlannerSidebar />
          <InspectorPanel />
        </div>
      </div>
    </div>
  );
}
