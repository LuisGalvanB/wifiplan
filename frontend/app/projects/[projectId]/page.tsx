"use client";
import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth";
import api from "@/lib/api";
import type { Project, Building, Floor } from "@/types";
import { ArrowLeftIcon, PlusIcon, MapIcon, DocumentChartBarIcon } from "@heroicons/react/24/outline";
import Link from "next/link";

export default function ProjectPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const router = useRouter();
  const { orgId, status } = useAuthStore();
  const qc = useQueryClient();

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/auth/login");
  }, [status, router]);

  const [newBuilding, setNewBuilding] = useState("");
  const [newFloor, setNewFloor] = useState<{ buildingId: string; name: string; level: number } | null>(null);

  const { data: project } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => api.get<Project>(`/orgs/${orgId}/projects/${projectId}`).then((r) => r.data),
    enabled: status === "authenticated" && !!orgId,
  });

  const { data: buildings = [] } = useQuery({
    queryKey: ["buildings", projectId],
    queryFn: () =>
      api.get<Building[]>(`/orgs/${orgId}/projects/${projectId}/buildings`).then((r) => r.data),
    enabled: status === "authenticated" && !!orgId,
  });

  const createBuilding = useMutation({
    mutationFn: (name: string) =>
      api.post<Building>(`/orgs/${orgId}/projects/${projectId}/buildings`, { name }).then((r) => r.data),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ["buildings", projectId] }); setNewBuilding(""); },
  });

  const createFloor = useMutation({
    mutationFn: ({ buildingId, name, level }: { buildingId: string; name: string; level: number }) =>
      api.post<Floor>(`/orgs/${orgId}/projects/${projectId}/buildings/${buildingId}/floors`, { name, level }).then((r) => r.data),
    onSuccess: (floor) => {
      qc.invalidateQueries({ queryKey: ["floors"] });
      setNewFloor(null);
      router.push(`/projects/${projectId}/floors/${floor.id}/planner`);
    },
  });

  const { data: floorsByBuilding } = useQuery({
    queryKey: ["floors-by-building", buildings.map((b) => b.id).join(",")],
    queryFn: async () => {
      const result: Record<string, Floor[]> = {};
      for (const b of buildings) {
        const { data } = await api.get<Floor[]>(
          `/orgs/${orgId}/projects/${projectId}/buildings/${b.id}/floors`
        );
        result[b.id] = data;
      }
      return result;
    },
    enabled: status === "authenticated" && buildings.length > 0 && !!orgId,
  });

  if (status !== "authenticated") return null;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 bg-gray-900 px-6 py-3 flex items-center gap-4">
        <button onClick={() => router.push("/dashboard")} className="text-gray-400 hover:text-white">
          <ArrowLeftIcon className="w-5 h-5" />
        </button>
        <span className="text-xl font-bold">📡 WifiPlan</span>
        <span className="text-gray-400">/</span>
        <span className="text-white font-medium">{project?.name ?? "Loading…"}</span>
        <Link href="/learn" className="ml-auto rounded-lg border border-blue-700/70 px-3 py-1.5 text-sm text-blue-300 hover:border-blue-500 hover:text-white">
          Aprende Wi-Fi
        </Link>
      </header>

      <main className="max-w-4xl mx-auto p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-semibold">{project?.name}</h1>
          <button
            onClick={() => router.push(`/projects/${projectId}/report`)}
            className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 border border-gray-700 px-4 py-2 rounded-lg text-sm transition-colors"
          >
            <DocumentChartBarIcon className="w-4 h-4 text-blue-400" />
            View Report
          </button>
        </div>

        {/* Add building */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h2 className="font-medium mb-3">Buildings</h2>
          <div className="flex gap-2 mb-4">
            <input
              value={newBuilding}
              onChange={(e) => setNewBuilding(e.target.value)}
              placeholder="Building name"
              className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
            />
            <button
              onClick={() => newBuilding && createBuilding.mutate(newBuilding)}
              disabled={!newBuilding || createBuilding.isPending}
              className="flex items-center gap-1 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-3 py-2 rounded-lg text-sm font-medium"
            >
              <PlusIcon className="w-4 h-4" /> Add
            </button>
          </div>

          {buildings.length === 0 ? (
            <p className="text-gray-500 text-sm">No buildings yet.</p>
          ) : (
            <div className="space-y-4">
              {buildings.map((b) => (
                <div key={b.id} className="border border-gray-800 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-medium">{b.name}</span>
                    <button
                      onClick={() => setNewFloor({ buildingId: b.id, name: "", level: 0 })}
                      className="flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
                    >
                      <PlusIcon className="w-3 h-3" /> Add Floor
                    </button>
                  </div>

                  {newFloor?.buildingId === b.id && (
                    <div className="flex gap-2 mb-3">
                      <input
                        value={newFloor.name}
                        onChange={(e) => setNewFloor((f) => f && { ...f, name: e.target.value })}
                        placeholder="Floor name (e.g. Ground Floor)"
                        className="flex-1 bg-gray-800 border border-gray-700 text-white rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:border-blue-500"
                      />
                      <input
                        type="number"
                        value={newFloor.level}
                        onChange={(e) => setNewFloor((f) => f && { ...f, level: parseInt(e.target.value) || 0 })}
                        className="w-16 bg-gray-800 border border-gray-700 text-white rounded-lg px-2 py-1.5 text-sm text-center focus:outline-none focus:border-blue-500"
                        placeholder="Level"
                      />
                      <button
                        onClick={() => newFloor && createFloor.mutate(newFloor)}
                        disabled={!newFloor.name || createFloor.isPending}
                        className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-3 py-1.5 rounded-lg text-sm"
                      >
                        Create
                      </button>
                      <button onClick={() => setNewFloor(null)} className="text-gray-500 hover:text-white text-sm px-2">✕</button>
                    </div>
                  )}

                  {/* Floor list */}
                  <div className="space-y-1">
                    {(floorsByBuilding?.[b.id] ?? []).map((f) => (
                      <button
                        key={f.id}
                        onClick={() => router.push(`/projects/${projectId}/floors/${f.id}/planner`)}
                        className="w-full text-left flex items-center gap-2 bg-gray-800 hover:bg-gray-700 px-3 py-2 rounded-lg text-sm transition-colors group"
                      >
                        <MapIcon className="w-4 h-4 text-gray-500 group-hover:text-blue-400" />
                        <span>{f.name}</span>
                        <span className="text-gray-500 text-xs">Level {f.level}</span>
                        {f.scale_px_per_m && (
                          <span className="ml-auto text-xs text-green-500">Calibrated</span>
                        )}
                        <span className="ml-auto text-xs text-blue-400 opacity-0 group-hover:opacity-100">
                          Open Planner →
                        </span>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
