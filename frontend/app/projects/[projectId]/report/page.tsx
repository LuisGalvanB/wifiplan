"use client";
import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth";
import api from "@/lib/api";
import {
  ArrowLeftIcon, ArrowDownTrayIcon, CheckCircleIcon,
  ExclamationTriangleIcon, XCircleIcon, WifiIcon,
} from "@heroicons/react/24/outline";

interface RFSummary {
  band_ghz: string;
  coverage_good_pct: number | null;
  coverage_fair_pct: number | null;
  coverage_poor_pct: number | null;
  avg_rssi_dbm: number | null;
  run_date: string;
}

interface APInventoryEntry {
  label: string | null;
  model: string;
  vendor: string;
  x_px: number;
  y_px: number;
  tx_power_dbm: number;
  bands: number[];
}

interface FloorReport {
  id: string;
  name: string;
  level: number;
  scale_px_per_m: number | null;
  wall_count: number;
  ap_count: number;
  floor_plan_uploaded: boolean;
  rf_summary: RFSummary | null;
  ap_inventory: APInventoryEntry[];
}

interface BuildingReport {
  id: string;
  name: string;
  floors: FloorReport[];
}

interface ProjectReport {
  project: {
    id: string;
    name: string;
    description: string | null;
    address: string | null;
    created_at: string;
  };
  buildings: BuildingReport[];
  report_generated_at: string;
  report_version: string;
}

function CoverageBadge({ pct, type }: { pct: number | null; type: "good" | "fair" | "poor" }) {
  if (pct === null) return <span className="text-gray-600 text-xs">—</span>;
  const styles = {
    good: "text-green-400",
    fair: "text-yellow-400",
    poor: "text-red-400",
  };
  const icons = {
    good: <CheckCircleIcon className="w-3.5 h-3.5" />,
    fair: <ExclamationTriangleIcon className="w-3.5 h-3.5" />,
    poor: <XCircleIcon className="w-3.5 h-3.5" />,
  };
  return (
    <span className={`flex items-center gap-1 text-xs font-mono ${styles[type]}`}>
      {icons[type]}{pct.toFixed(1)}%
    </span>
  );
}

function CoverageBar({ good, fair, poor }: { good: number | null; fair: number | null; poor: number | null }) {
  if (good === null) return <div className="text-xs text-gray-600">No RF simulation run yet</div>;
  return (
    <div className="space-y-1">
      <div className="flex h-3 rounded-full overflow-hidden bg-gray-800 w-full">
        <div className="bg-green-500" style={{ width: `${good}%` }} title={`Good: ${good?.toFixed(1)}%`} />
        <div className="bg-yellow-500" style={{ width: `${fair ?? 0}%` }} title={`Fair: ${fair?.toFixed(1)}%`} />
        <div className="bg-red-600" style={{ width: `${poor ?? 0}%` }} title={`Poor: ${poor?.toFixed(1)}%`} />
      </div>
      <div className="flex gap-4 text-xs text-gray-400">
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-green-500 rounded-sm inline-block" />Good ≥−65 dBm</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-yellow-500 rounded-sm inline-block" />Fair</span>
        <span className="flex items-center gap-1"><span className="w-2 h-2 bg-red-600 rounded-sm inline-block" />Poor &lt;−75 dBm</span>
      </div>
    </div>
  );
}

export default function ReportPage() {
  const { projectId } = useParams<{ projectId: string }>();
  const router = useRouter();
  const { orgId, status } = useAuthStore();

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/auth/login");
  }, [status, router]);

  const { data: report, isLoading, error } = useQuery({
    queryKey: ["report", projectId, orgId],
    queryFn: () =>
      api.get<ProjectReport>(`/orgs/${orgId}/projects/${projectId}/report/json`).then((r) => r.data),
    enabled: status === "authenticated" && !!orgId && !!projectId,
  });

  if (status !== "authenticated") return null;

  const handleExport = () => {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `wifiplan-report-${report.project.name.replace(/\s+/g, "-").toLowerCase()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const totalAPs = report?.buildings.flatMap((b) => b.floors).reduce((n, f) => n + f.ap_count, 0) ?? 0;
  const totalWalls = report?.buildings.flatMap((b) => b.floors).reduce((n, f) => n + f.wall_count, 0) ?? 0;
  const totalFloors = report?.buildings.flatMap((b) => b.floors).length ?? 0;

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="border-b border-gray-800 bg-gray-900 px-6 py-3 flex items-center gap-4">
        <button onClick={() => router.push(`/projects/${projectId}`)} className="text-gray-400 hover:text-white">
          <ArrowLeftIcon className="w-5 h-5" />
        </button>
        <span className="text-lg font-bold">📡 WifiPlan</span>
        <span className="text-gray-600">/</span>
        <span className="text-gray-300 font-medium">{report?.project.name ?? "…"}</span>
        <span className="text-gray-600">/</span>
        <span className="text-gray-400">Report</span>
        <div className="flex-1" />
        <button
          onClick={handleExport}
          disabled={!report}
          className="flex items-center gap-2 bg-blue-700 hover:bg-blue-600 disabled:opacity-40 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
        >
          <ArrowDownTrayIcon className="w-4 h-4" />
          Export JSON
        </button>
      </header>

      <main className="max-w-4xl mx-auto p-6 space-y-6">
        {isLoading && <div className="text-gray-500 text-center py-16">Generating report…</div>}
        {error && <div className="text-red-400 text-center py-16">Failed to load report.</div>}

        {report && (
          <>
            {/* Project summary card */}
            <div className="bg-gray-900 border border-gray-800 rounded-xl p-6">
              <h1 className="text-2xl font-semibold mb-1">{report.project.name}</h1>
              {report.project.description && (
                <p className="text-gray-400 text-sm mb-2">{report.project.description}</p>
              )}
              {report.project.address && (
                <p className="text-gray-500 text-sm mb-4">📍 {report.project.address}</p>
              )}
              <div className="grid grid-cols-3 gap-4 mt-4">
                {[
                  { label: "Floors", value: totalFloors },
                  { label: "Access Points", value: totalAPs },
                  { label: "Walls Mapped", value: totalWalls },
                ].map((s) => (
                  <div key={s.label} className="bg-gray-800 rounded-lg p-4 text-center">
                    <div className="text-2xl font-bold text-blue-400">{s.value}</div>
                    <div className="text-xs text-gray-400 mt-1">{s.label}</div>
                  </div>
                ))}
              </div>
              <p className="text-xs text-gray-600 mt-4">
                Generated {new Date(report.report_generated_at).toLocaleString()} · v{report.report_version}
              </p>
            </div>

            {/* Buildings */}
            {report.buildings.map((building) => (
              <div key={building.id} className="space-y-4">
                <h2 className="text-lg font-semibold text-gray-200 flex items-center gap-2">
                  🏢 {building.name}
                </h2>

                {building.floors.map((floor) => (
                  <div key={floor.id} className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
                    {/* Floor header */}
                    <div className="px-5 py-3 border-b border-gray-800 flex items-center justify-between">
                      <div>
                        <span className="font-medium">{floor.name}</span>
                        <span className="text-xs text-gray-500 ml-2">Level {floor.level}</span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-400">
                        <span>{floor.wall_count} walls</span>
                        <span>{floor.ap_count} APs</span>
                        {floor.scale_px_per_m && (
                          <span className="text-green-500">
                            {floor.scale_px_per_m.toFixed(1)} px/m
                          </span>
                        )}
                        {floor.floor_plan_uploaded
                          ? <span className="text-blue-400">Plan uploaded ✓</span>
                          : <span className="text-gray-600">No plan uploaded</span>
                        }
                      </div>
                    </div>

                    <div className="p-5 space-y-5">
                      {/* RF coverage summary */}
                      {floor.rf_summary ? (
                        <div>
                          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
                            RF Coverage — {floor.rf_summary.band_ghz} GHz
                          </h3>
                          <CoverageBar
                            good={floor.rf_summary.coverage_good_pct}
                            fair={floor.rf_summary.coverage_fair_pct}
                            poor={floor.rf_summary.coverage_poor_pct}
                          />
                          <div className="mt-2 flex gap-6 text-xs text-gray-500">
                            <CoverageBadge pct={floor.rf_summary.coverage_good_pct} type="good" />
                            <CoverageBadge pct={floor.rf_summary.coverage_fair_pct} type="fair" />
                            <CoverageBadge pct={floor.rf_summary.coverage_poor_pct} type="poor" />
                            {floor.rf_summary.avg_rssi_dbm !== null && (
                              <span className="text-gray-400">
                                Avg: {floor.rf_summary.avg_rssi_dbm.toFixed(1)} dBm
                              </span>
                            )}
                          </div>
                        </div>
                      ) : (
                        <p className="text-xs text-gray-600">
                          No RF simulation run yet for this floor. Open the planner and click Simulate RF.
                        </p>
                      )}

                      {/* AP inventory table */}
                      {floor.ap_inventory.length > 0 && (
                        <div>
                          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">
                            AP Inventory
                          </h3>
                          <div className="overflow-x-auto">
                            <table className="w-full text-xs">
                              <thead>
                                <tr className="text-gray-500 border-b border-gray-800">
                                  <th className="text-left pb-2 pr-4">Label</th>
                                  <th className="text-left pb-2 pr-4">Model</th>
                                  <th className="text-left pb-2 pr-4">Vendor</th>
                                  <th className="text-right pb-2 pr-4">Tx Power</th>
                                  <th className="text-left pb-2">Bands</th>
                                </tr>
                              </thead>
                              <tbody>
                                {floor.ap_inventory.map((ap, i) => (
                                  <tr key={i} className="border-b border-gray-800/50 hover:bg-gray-800/30">
                                    <td className="py-1.5 pr-4 font-mono text-blue-300">
                                      {ap.label ?? `AP-${String(i + 1).padStart(2, "0")}`}
                                    </td>
                                    <td className="py-1.5 pr-4 text-gray-200">{ap.model}</td>
                                    <td className="py-1.5 pr-4 text-gray-400">{ap.vendor}</td>
                                    <td className="py-1.5 pr-4 text-right text-gray-400">
                                      {ap.tx_power_dbm} dBm
                                    </td>
                                    <td className="py-1.5 text-gray-400">
                                      {ap.bands.map((b) => `${b}G`).join("/")}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}

                      {floor.ap_inventory.length === 0 && (
                        <p className="text-xs text-gray-600 flex items-center gap-1.5">
                          <WifiIcon className="w-3.5 h-3.5" />
                          No APs placed on this floor yet.
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ))}

            {/* PDF note */}
            <div className="bg-gray-900/50 border border-gray-800 rounded-xl p-4 text-sm text-gray-500 text-center">
              📄 PDF export is on the roadmap. Use <strong className="text-gray-400">Export JSON</strong> to download
              the full machine-readable report.
            </div>
          </>
        )}
      </main>
    </div>
  );
}
