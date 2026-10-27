"use client";
import { Suspense } from "react";
import { Canvas, useThree } from "@react-three/fiber";
import { OrbitControls, Grid } from "@react-three/drei";
import { usePlannerStore } from "@/store/planner";
import type { Wall, PlacedAP } from "@/types";

const MATERIAL_COLORS: Record<string, string> = {
  concrete: "#6b7280", brick: "#dc2626", drywall: "#fef9c3",
  wood: "#d97706", metal: "#06b6d4", glass: "#93c5fd", unknown: "#9ca3af",
};

function pxToWorld(px: number, scale: number) { return px / scale; }

function WallMesh({ wall, scale }: { wall: Wall; scale: number }) {
  const { start, end } = wall.geometry;
  const sx = pxToWorld(start.x, scale);
  const sy = pxToWorld(start.y, scale);
  const ex = pxToWorld(end.x, scale);
  const ey = pxToWorld(end.y, scale);
  const dx = ex - sx, dz = ey - sy;
  const len = Math.sqrt(dx * dx + dz * dz);
  if (len < 0.01) return null;
  const cx = (sx + ex) / 2, cz = (sy + ey) / 2;
  const angle = Math.atan2(dz, dx);
  const height = wall.height_m;
  const thickness = Math.max(0.05, (wall.thickness_px / scale) * 2);
  const color = MATERIAL_COLORS[wall.material] ?? "#9ca3af";
  return (
    <mesh position={[cx, height / 2, cz]} rotation={[0, -angle, 0]}>
      <boxGeometry args={[len, height, thickness]} />
      <meshStandardMaterial
        color={color} roughness={0.85}
        metalness={wall.material === "metal" ? 0.6 : 0.05}
        transparent={wall.material === "glass"} opacity={wall.material === "glass" ? 0.4 : 1}
      />
    </mesh>
  );
}

function APMarker({ ap, scale }: { ap: PlacedAP; scale: number }) {
  const { selectedAPId, selectAP } = usePlannerStore();
  const isSelected = ap.id === selectedAPId;
  const x = pxToWorld(ap.x_px, scale);
  const z = pxToWorld(ap.y_px, scale);
  const y = ap.height_m;
  return (
    <group position={[x, y, z]} onClick={(e) => { e.stopPropagation(); selectAP(ap.id); }}>
      <mesh position={[0, -y / 2, 0]}>
        <cylinderGeometry args={[0.02, 0.02, y, 6]} />
        <meshStandardMaterial color="#374151" />
      </mesh>
      <mesh>
        <cylinderGeometry args={[0.18, 0.18, 0.04, 16]} />
        <meshStandardMaterial
          color={isSelected ? "#f59e0b" : "#f97316"}
          emissive={isSelected ? "#f59e0b" : "#000000"}
          emissiveIntensity={isSelected ? 0.3 : 0}
          roughness={0.3} metalness={0.5}
        />
      </mesh>
      {[0.3, 0.55, 0.8].map((r, i) => (
        <mesh key={i} position={[0, 0.1 + i * 0.15, 0]}>
          <torusGeometry args={[r, 0.015, 6, 24]} />
          <meshStandardMaterial color="#22c55e" transparent opacity={0.6 - i * 0.15} />
        </mesh>
      ))}
    </group>
  );
}

function FloorPlane({ width, depth }: { width: number; depth: number }) {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[width / 2, 0, depth / 2]} receiveShadow>
      <planeGeometry args={[width, depth]} />
      <meshStandardMaterial color="#1f2937" roughness={1} />
    </mesh>
  );
}

function CameraSetup() {
  const { camera } = useThree();
  const { floorPlanWidth, floorPlanHeight } = usePlannerStore();
  const scale = 20;
  const cx = pxToWorld(floorPlanWidth / 2, scale);
  const cz = pxToWorld(floorPlanHeight / 2, scale);
  camera.position.set(cx + 15, 18, cz + 15);
  camera.lookAt(cx, 0, cz);
  return null;
}

function Scene() {
  const { geometry, placedAPs, floorPlanWidth, floorPlanHeight } = usePlannerStore();
  const scale = 20;
  const worldW = pxToWorld(floorPlanWidth, scale);
  const worldD = pxToWorld(floorPlanHeight, scale);
  return (
    <>
      <ambientLight intensity={0.5} />
      <directionalLight position={[worldW / 2, 10, worldD / 2]} intensity={1.2} castShadow />
      <pointLight position={[0, 5, 0]} intensity={0.3} color="#60a5fa" />
      <FloorPlane width={worldW} depth={worldD} />
      <Grid
        position={[worldW / 2, 0.001, worldD / 2]} args={[worldW, worldD]}
        cellSize={1} cellThickness={0.5} cellColor="#374151"
        sectionSize={5} sectionThickness={1} sectionColor="#4b5563"
        fadeDistance={80} fadeStrength={1}
      />
      {geometry?.walls.filter((w) => w.is_accepted).map((wall) => (
        <WallMesh key={wall.id} wall={wall} scale={scale} />
      ))}
      {placedAPs.map((ap) => (
        <APMarker key={ap.id} ap={ap} scale={scale} />
      ))}
    </>
  );
}

export function PlannerView3D() {
  const { geometry, placedAPs } = usePlannerStore();
  return (
    <div className="w-full h-full bg-gray-950 relative">
      <Canvas shadows="basic" camera={{ fov: 55, near: 0.1, far: 500 }} gl={{ antialias: true }}
        style={{ background: "#030712" }}>
        <Suspense fallback={null}>
          <CameraSetup />
          <Scene />
          <OrbitControls makeDefault enableDamping dampingFactor={0.05}
            minDistance={2} maxDistance={200} maxPolarAngle={Math.PI / 2.1} />
        </Suspense>
      </Canvas>
      <div className="absolute bottom-3 left-3 text-xs text-gray-500 bg-gray-900/70 px-2 py-1 rounded pointer-events-none">
        Orbit: Left drag · Zoom: Scroll · Pan: Right drag
      </div>
      <div className="absolute top-3 left-3 text-xs text-gray-400 bg-gray-900/70 px-2 py-1 rounded pointer-events-none">
        3D View — {geometry?.walls.filter((w) => w.is_accepted).length ?? 0} walls · {placedAPs.length} APs
      </div>
    </div>
  );
}
