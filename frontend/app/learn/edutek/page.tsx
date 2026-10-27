import Link from "next/link";
import { LearnLayout } from "@/components/learn/LearnLayout";
import { WifiCanvasLesson } from "@/components/learn/WifiCanvasLesson";

const steps = [
  { title: "Codificar bits", detail: "QAM representa símbolos con amplitud y fase.", href: "/learn/qam" },
  { title: "Compartir el canal", detail: "OFDM y OFDMA organizan subportadoras y usuarios.", href: "/learn/ofdm" },
  { title: "Acceder al medio", detail: "CSMA/CA coordina cuándo transmite cada estación.", href: "/learn/csma-ca" },
  { title: "Propagar la señal", detail: "Bandas, distancia y materiales afectan la recepción.", href: "/learn/transmision" },
];

export default function EdutekCoursePage() {
  return (
    <LearnLayout>
      <Link href="/learn" className="text-sm text-blue-300 hover:text-white">← Todos los módulos</Link>
      <header className="mt-6 max-w-3xl">
        <p className="text-xs font-semibold tracking-[0.2em] text-blue-300">RECORRIDO · WI-FI 6</p>
        <h1 className="mt-3 text-4xl font-bold tracking-tight text-white md:text-5xl">De los bits al enlace inalámbrico</h1>
        <p className="mt-5 text-lg leading-relaxed text-slate-300">
          Un recorrido interactivo en español desde la codificación hasta la señal recibida. Controla dispositivos, envíos y colisiones, y avanza paso a paso para ver cómo se comparte el canal inalámbrico.
        </p>
      </header>
      <section className="mt-8" aria-labelledby="journey-heading">
        <h2 id="journey-heading" className="mb-4 text-xl font-semibold text-white">Simula el viaje del dato</h2>
        <WifiCanvasLesson scene="dataJourney" showJourneyControls />
      </section>
      <ol className="mt-10 grid gap-4 md:grid-cols-2">
        {steps.map((step, index) => (
          <li key={step.href} className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6">
            <span className="font-mono text-sm text-blue-300">PASO 0{index + 1}</span>
            <h2 className="mt-3 text-xl font-semibold text-white">{step.title}</h2>
            <p className="mt-2 text-slate-400">{step.detail}</p>
            <Link href={step.href} className="mt-5 inline-block text-sm text-blue-300 hover:text-white">Abrir animación →</Link>
          </li>
        ))}
      </ol>
      <section className="mt-8 rounded-2xl border border-slate-800 p-6">
        <h2 className="text-xl font-semibold text-white">Dos conceptos más para planificar</h2>
        <p className="mt-2 text-slate-400">El espectro y los obstáculos completan el panorama radioeléctrico.</p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link href="/learn/espectro" className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-blue-200 hover:border-blue-400">Explorar bandas Wi-Fi</Link>
          <Link href="/learn/muros" className="rounded-lg border border-slate-700 px-4 py-2 text-sm text-blue-200 hover:border-blue-400">Explorar pérdida en paredes</Link>
        </div>
      </section>
      <section className="mt-8 rounded-2xl border border-slate-800 p-6">
        <h2 className="text-xl font-semibold text-white">Practica los controles</h2>
        <p className="mt-2 leading-relaxed text-slate-400">
          Reinicia el escenario, añade dispositivos, fuerza una colisión o envía datos. El modo paso a paso te permite revisar escucha, backoff, transmisión, recepción y ACK; Normal y Rápido cambian el ritmo de la animación.
        </p>
      </section>
    </LearnLayout>
  );
}
