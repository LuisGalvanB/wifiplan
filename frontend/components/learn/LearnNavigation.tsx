import Link from "next/link";

const lessons = [
  ["qam", "Modulación QAM"],
  ["ofdm", "OFDM y OFDMA"],
  ["csma-ca", "Acceso CSMA/CA"],
  ["espectro", "Espectro Wi-Fi"],
  ["transmision", "Viaje de la señal"],
  ["muros", "Pérdida en paredes"],
  ["data-journey", "Viaje del dato"],
] as const;

export function LearnNavigation() {
  return (
    <nav aria-label="Módulos educativos" className="flex flex-wrap gap-2">
      {lessons.map(([slug, title]) => (
        <Link
          key={slug}
          href={`/learn/${slug}`}
          className="rounded-lg border border-slate-700 px-3 py-2 text-sm text-slate-300 transition-colors hover:border-blue-400 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
        >
          {title}
        </Link>
      ))}
    </nav>
  );
}
