import Link from "next/link";
import { LearnLayout } from "@/components/learn/LearnLayout";

const modules = [
  { href: "/learn/qam", number: "01", title: "Modulación QAM", summary: "Descubre cómo amplitud y fase representan bits, y por qué los símbolos densos necesitan buena señal." },
  { href: "/learn/ofdm", number: "02", title: "OFDM y OFDMA", summary: "Visualiza las subportadoras ortogonales, el prefijo cíclico y las unidades de recursos de Wi-Fi 6." },
  { href: "/learn/csma-ca", number: "03", title: "Acceso CSMA/CA", summary: "Sigue el proceso de escucha, backoff, transmisión y confirmación en un canal compartido." },
  { href: "/learn/espectro", number: "04", title: "Espectro Wi-Fi", summary: "Ubica 2.4, 5 y 6 GHz en el espectro electromagnético y amplía las bandas inalámbricas." },
  { href: "/learn/transmision", number: "05", title: "Viaje de la señal", summary: "Compara longitudes de onda y observa cómo viajan ondas y paquetes hasta el cliente." },
  { href: "/learn/muros", number: "06", title: "Pérdida en paredes", summary: "Explora de forma conceptual cómo diferentes materiales atenúan la señal recibida." },
  { href: "/learn/data-journey", number: "07", title: "Viaje del dato", summary: "Controla el envío, la contención y las colisiones mientras un paquete llega a su destino." },
];

export default function LearnPage() {
  return (
    <LearnLayout>
      <section className="max-w-3xl">
        <p className="mb-3 text-xs font-semibold tracking-[0.2em] text-blue-300">AULA INTERACTIVA · WIFI PLAN</p>
        <h1 className="text-4xl font-bold tracking-tight text-white md:text-6xl">Aprende cómo funciona el Wi-Fi</h1>
        <p className="mt-5 text-lg leading-relaxed text-slate-300">
          Recorre conceptos de modulación, acceso al medio y propagación mediante animaciones accesibles. Cambia los controles para explorar cada idea; no necesitas conectar equipos ni ejecutar simulaciones.
        </p>
        <Link href="/learn/edutek" className="mt-7 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-3 font-medium text-white transition hover:bg-blue-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-300">
          Empezar el recorrido <span aria-hidden="true">→</span>
        </Link>
      </section>

      <section className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-3" aria-label="Módulos educativos">
        {modules.map((module) => (
          <Link
            key={module.href}
            href={module.href}
            className="group rounded-2xl border border-slate-800 bg-slate-900/60 p-6 transition hover:-translate-y-0.5 hover:border-blue-500 hover:bg-slate-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
          >
            <span className="font-mono text-sm text-blue-300">{module.number} / WI-FI</span>
            <h2 className="mt-4 text-xl font-semibold text-white group-hover:text-blue-200">{module.title}</h2>
            <p className="mt-2 leading-relaxed text-slate-400">{module.summary}</p>
            <span className="mt-5 inline-block text-sm text-blue-300">Explorar módulo <span aria-hidden="true">→</span></span>
          </Link>
        ))}
      </section>
      <p className="mt-8 max-w-3xl text-sm leading-relaxed text-slate-500">
        Las gráficas y cifras de los módulos son ilustrativas. La cobertura real depende del equipo, el entorno, la configuración y las normas locales.
      </p>
    </LearnLayout>
  );
}
