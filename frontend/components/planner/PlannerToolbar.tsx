"use client";
import { usePlannerStore, type ToolMode, type LayerKey } from "@/store/planner";
import {
  CursorArrowRaysIcon, PencilIcon, WifiIcon,
  HandRaisedIcon, EyeIcon, EyeSlashIcon,
} from "@heroicons/react/24/outline";

const TOOLS: { mode: ToolMode; icon: React.ReactNode; label: string }[] = [
  { mode: "select", icon: <CursorArrowRaysIcon className="w-5 h-5" />, label: "Select" },
  { mode: "pan", icon: <HandRaisedIcon className="w-5 h-5" />, label: "Pan" },
  { mode: "draw-wall", icon: <PencilIcon className="w-5 h-5" />, label: "Draw Wall" },
  { mode: "place-ap", icon: <WifiIcon className="w-5 h-5" />, label: "Place AP" },
];

const LAYERS: { key: LayerKey; label: string }[] = [
  { key: "walls", label: "Walls" },
  { key: "aps", label: "APs" },
  { key: "heatmap", label: "Heatmap" },
  { key: "scope", label: "Scope" },
  { key: "obstacles", label: "Obstacles" },
];

export function PlannerToolbar() {
  const { toolMode, setToolMode, layers, toggleLayer } = usePlannerStore();

  return (
    <div className="w-14 bg-gray-900 border-r border-gray-800 flex flex-col items-center py-3 gap-1">
      {/* Tool buttons */}
      {TOOLS.map((t) => (
        <button
          key={t.mode}
          onClick={() => setToolMode(t.mode)}
          title={t.label}
          className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors ${
            toolMode === t.mode
              ? "bg-blue-600 text-white"
              : "text-gray-400 hover:bg-gray-800 hover:text-white"
          }`}
        >
          {t.icon}
        </button>
      ))}

      <div className="w-8 border-t border-gray-700 my-2" />

      {/* Layer toggles */}
      {LAYERS.map((l) => {
        const visible = layers[l.key];
        return (
          <button
            key={l.key}
            onClick={() => toggleLayer(l.key)}
            title={`${visible ? "Hide" : "Show"} ${l.label}`}
            className={`w-9 h-9 rounded-lg flex items-center justify-center transition-colors text-xs font-medium ${
              visible ? "text-gray-300 hover:bg-gray-800" : "text-gray-600 hover:bg-gray-800"
            }`}
          >
            {visible
              ? <EyeIcon className="w-4 h-4" />
              : <EyeSlashIcon className="w-4 h-4" />
            }
          </button>
        );
      })}
    </div>
  );
}
