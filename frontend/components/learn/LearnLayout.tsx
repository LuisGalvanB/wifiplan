import Link from "next/link";
import { LearnNavigation } from "./LearnNavigation";

export function LearnLayout({ children }: { children: React.ReactNode }) {
  return (
    <div lang="es" className="h-screen overflow-y-auto bg-slate-950 text-slate-100">
      <header className="border-b border-slate-800 bg-slate-900/90">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-5 py-4">
          <Link href="/learn" className="text-lg font-bold tracking-tight text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400">
            <span aria-hidden="true">📡</span> WifiPlan · Aprende Wi-Fi
          </Link>
          <Link href="/dashboard" className="text-sm text-slate-300 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400">
            Volver al panel
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-5 py-8 md:py-12">
        {children}
      </main>
      <footer className="mx-auto max-w-6xl border-t border-slate-800 px-5 py-6 text-sm text-slate-500">
        <p>Material educativo conceptual · Wi-Fi, propagación y planificación inalámbrica</p>
        <div className="mt-4">
          <LearnNavigation />
        </div>
      </footer>
    </div>
  );
}
