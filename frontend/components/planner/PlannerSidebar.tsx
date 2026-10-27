"use client";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { usePlannerStore } from "@/store/planner";
import api from "@/lib/api";
import type { APModel, APVendor } from "@/types";
import { WifiIcon } from "@heroicons/react/24/outline";

export function PlannerSidebar() {
  const { selectedAPModel, setSelectedAPModel, setToolMode } = usePlannerStore();
  const [selectedVendor, setSelectedVendor] = useState<string>("all");

  const { data: vendors = [] } = useQuery({
    queryKey: ["vendors"],
    queryFn: () => api.get<APVendor[]>("/catalog/vendors").then((r) => r.data),
  });

  const { data: models = [] } = useQuery({
    queryKey: ["ap-models", selectedVendor],
    queryFn: () =>
      api.get<APModel[]>("/catalog/models", {
        params: selectedVendor !== "all" ? { vendor_id: selectedVendor } : {},
      }).then((r) => r.data),
  });

  return (
    <div className="w-52 bg-gray-900 border-l border-gray-800 flex flex-col overflow-hidden">
      <div className="px-3 py-2 border-b border-gray-800">
        <span className="text-xs font-semibold text-gray-400 uppercase tracking-wide">AP Catalog</span>
      </div>
      <div className="px-3 py-2 border-b border-gray-800">
        <select value={selectedVendor} onChange={(e) => setSelectedVendor(e.target.value)}
          className="w-full bg-gray-800 border border-gray-700 text-white text-xs rounded px-2 py-1.5 focus:outline-none">
          <option value="all">All vendors</option>
          {vendors.map((v) => (<option key={v.id} value={v.id}>{v.name}</option>))}
        </select>
      </div>
      <div className="flex-1 overflow-y-auto">
        {models.map((m) => (
          <button key={m.id}
            onClick={() => { setSelectedAPModel(m); setToolMode("place-ap"); }}
            className={`w-full text-left px-3 py-2.5 border-b border-gray-800/50 transition-colors ${
              selectedAPModel?.id === m.id
                ? "bg-blue-900/40 border-l-2 border-l-blue-500"
                : "hover:bg-gray-800"
            }`}>
            <div className="flex items-center gap-2">
              <WifiIcon className="w-3.5 h-3.5 text-blue-400 shrink-0" />
              <span className="text-xs text-white font-medium truncate">{m.model_name}</span>
            </div>
            <div className="text-xs text-gray-500 mt-0.5 pl-5">
              {m.vendor_name} · {m.bands_ghz.map((b) => `${b}G`).join("/")}
            </div>
            <div className="text-xs text-gray-600 pl-5">
              {m.max_spatial_streams}×{m.max_spatial_streams} · {m.tx_power_default_dbm} dBm
            </div>
          </button>
        ))}
      </div>
      {selectedAPModel && (
        <div className="px-3 py-2 border-t border-gray-800 bg-blue-900/20">
          <p className="text-xs text-blue-300 font-medium">
            Click canvas to place {selectedAPModel.model_name}
          </p>
          <button onClick={() => { setSelectedAPModel(null); setToolMode("select"); }}
            className="text-xs text-gray-500 hover:text-gray-300 mt-1">
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}
