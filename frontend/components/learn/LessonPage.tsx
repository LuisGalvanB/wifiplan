import Link from "next/link";
import { WifiCanvasLesson, type WifiLessonScene } from "./WifiCanvasLesson";
import { LearnLayout } from "./LearnLayout";
import { LearnNavigation } from "./LearnNavigation";
import type { WifiBand, WallMaterial } from "./wallAttenuation";

const LESSONS: Record<WifiLessonScene, { eyebrow: string; title: string; intro: string; sections: { title: string; text: string }[] }> = {
  qam: {
    eyebrow: "01 · MODULACIÓN",
    title: "QAM: bits en amplitud y fase",
    intro: "La modulación en cuadratura combina dos señales portadoras para representar símbolos. Cada punto de la constelación codifica un grupo de bits; los órdenes mayores pueden transportar más bits, pero toleran menos ruido.",
    sections: [
      { title: "Constelación y tasa", text: "BPSK representa 1 bit por símbolo; 16-, 64-, 256- y 1024-QAM representan respectivamente 4, 6, 8 y 10 bits. La tasa útil también depende del ancho de canal, la codificación y el número de flujos espaciales." },
      { title: "SNR y adaptación", text: "Al aumentar el orden, los puntos quedan más próximos. Un nivel de ruido alto hace más probable que el receptor confunda símbolos, por lo que los equipos adaptan la modulación a la calidad del enlace." },
    ],
  },
  ofdm: {
    eyebrow: "02 · CANAL",
    title: "OFDM y OFDMA: muchas transmisiones a la vez",
    intro: "OFDM divide un canal en subportadoras ortogonales. Sus espectros pueden solaparse sin interferirse idealmente, aprovechando mejor el ancho disponible y haciendo el enlace más robusto frente a trayectos múltiples.",
    sections: [
      { title: "Prefijo cíclico", text: "El prefijo cíclico copia una parte final del símbolo al comienzo. Sirve como intervalo de guarda ante retardos de propagación; consume tiempo y no es una corrección ilimitada de cualquier interferencia." },
      { title: "De OFDM a OFDMA", text: "OFDMA asigna grupos de subportadoras (unidades de recursos) a varios clientes durante el mismo intervalo. Wi-Fi 6 (802.11ax) incorpora esta asignación para atender tráfico de forma más eficiente." },
    ],
  },
  csma: {
    eyebrow: "03 · ACCESO AL MEDIO",
    title: "CSMA/CA: escuchar antes de transmitir",
    intro: "Como varios equipos comparten el mismo canal inalámbrico, Wi-Fi coordina el acceso: cada estación comprueba si el medio está libre y espera un intervalo aleatorio antes de enviar.",
    sections: [
      { title: "Contención y backoff", text: "Si el canal está ocupado, la estación espera. Cuando queda libre, elige un contador aleatorio y lo reduce mientras el canal sigue disponible. Si otra estación transmite, el contador se congela y la espera se reanuda después." },
      { title: "Confirmación y reintento", text: "El emisor suele esperar un acuse de recibo. Si no lo recibe, puede reintentar con una ventana de contención mayor. CSMA/CA reduce la probabilidad de colisión; no puede eliminarla en todos los casos." },
    ],
  },
  spectrum: {
    eyebrow: "04 · RADIOFRECUENCIA",
    title: "¿Dónde están las bandas Wi-Fi?",
    intro: "Wi-Fi utiliza radiofrecuencias dentro de la región de microondas del espectro electromagnético. La vista interactiva muestra cómo las bandas de 2.4, 5 y 6 GHz ocupan una pequeña porción del espectro.",
    sections: [
      { title: "Frecuencia y longitud de onda", text: "La longitud de onda disminuye al aumentar la frecuencia. Esto afecta la propagación y la interacción con obstáculos, aunque el entorno, las antenas y la potencia también importan." },
      { title: "Regulación local", text: "La disponibilidad de canales, anchos y potencias permitidas cambia según el país. La selección de banda en la animación es una comparación educativa, no una recomendación regulatoria." },
    ],
  },
  transmission: {
    eyebrow: "05 · PROPAGACIÓN",
    title: "El viaje de una señal Wi-Fi",
    intro: "Un punto de acceso transmite una onda de radio modulada; el cliente la recibe y recupera la información. En interiores, la señal también se refleja, difracta y absorbe al interactuar con el espacio.",
    sections: [
      { title: "Bandas distintas, longitudes distintas", text: "A igual velocidad de propagación, una señal de 2.4 GHz tiene una longitud de onda mayor que una de 5 o 6 GHz. El alcance real también depende de la potencia, antenas, interferencia y materiales." },
      { title: "El canal no es una línea recta", text: "El multitrayecto puede reforzar o cancelar señales en distintas posiciones. Por eso una variación pequeña de ubicación puede cambiar la calidad del enlace." },
    ],
  },
  walls: {
    eyebrow: "06 · ATENUACIÓN",
    title: "Cómo afectan las paredes a la señal",
    intro: "Al atravesar un material, parte de la energía de radio puede absorberse o reflejarse. La pérdida depende del material, su espesor, la frecuencia y el ángulo de incidencia.",
    sections: [
      { title: "Compara materiales", text: "Selecciona vidrio, madera, concreto, metal o varias paredes para explorar una atenuación ilustrativa. Los valores son ejemplos didácticos y no equivalen a mediciones de una obra concreta." },
      { title: "Planificar con el entorno", text: "Al diseñar una red, modelar las paredes y validar la cobertura con mediciones ayuda a estimar niveles de señal. Una cifra única en dB no captura por completo la geometría ni todos los efectos de propagación." },
    ],
  },
  dataJourney: {
    eyebrow: "07 · VIAJE DEL DATO",
    title: "Del emisor al destino",
    intro: "Sigue un paquete desde un dispositivo a través del punto de acceso hasta otro equipo. Añade estaciones, controla una colisión, envía datos y avanza paso a paso para observar la contención, el envío y la confirmación.",
    sections: [
      { title: "Contender por el medio", text: "Antes de transmitir, una estación escucha el canal y espera el intervalo de contención. El backoff aleatorio ayuda a espaciar transmisiones de equipos que comparten el medio." },
      { title: "Transmitir y confirmar", text: "Cuando el canal queda disponible, el emisor envía una trama al punto de acceso y el receptor puede responder con un acuse (ACK). Una colisión o falta de ACK puede dar lugar a un reintento." },
    ],
  },
};

const LESSON_ORDER: WifiLessonScene[] = ["qam", "ofdm", "csma", "spectrum", "transmission", "walls"];
const LESSON_ROUTES: Record<WifiLessonScene, string> = {
  qam: "qam",
  ofdm: "ofdm",
  csma: "csma-ca",
  spectrum: "espectro",
  transmission: "transmision",
  walls: "muros",
  dataJourney: "data-journey",
};

export function LessonPage({
  scene,
  initialBand,
  initialMaterial,
}: {
  scene: WifiLessonScene;
  initialBand?: WifiBand;
  initialMaterial?: WallMaterial;
}) {
  const lesson = LESSONS[scene];
  const lessonIndex = LESSON_ORDER.indexOf(scene);
  const previous = lessonIndex > 0 ? LESSON_ORDER[lessonIndex - 1] : null;
  const next = lessonIndex >= 0 && lessonIndex < LESSON_ORDER.length - 1 ? LESSON_ORDER[lessonIndex + 1] : null;

  return (
    <LearnLayout>
      <div className="mb-8 space-y-6">
        <Link href="/learn" className="inline-flex items-center gap-2 text-sm text-blue-300 hover:text-white">
          <span aria-hidden="true">←</span> Todos los módulos
        </Link>
        <div className="max-w-3xl">
          <p className="mb-3 text-xs font-semibold tracking-[0.2em] text-blue-300">{lesson.eyebrow}</p>
          <h1 className="text-3xl font-bold tracking-tight text-white md:text-5xl">{lesson.title}</h1>
          <p className="mt-5 text-lg leading-relaxed text-slate-300">{lesson.intro}</p>
        </div>
        <WifiCanvasLesson
          key={`${scene}-${initialBand ?? ""}-${initialMaterial ?? ""}`}
          scene={scene}
          initialBand={initialBand}
          initialMaterial={initialMaterial}
        />
      </div>

      <section className="grid gap-4 md:grid-cols-2" aria-label="Conceptos clave">
        {lesson.sections.map((section) => (
          <article key={section.title} className="rounded-xl border border-slate-800 bg-slate-900/60 p-5">
            <h2 className="text-lg font-semibold text-white">{section.title}</h2>
            <p className="mt-2 leading-relaxed text-slate-300">{section.text}</p>
          </article>
        ))}
      </section>

      <section className="mt-10 border-t border-slate-800 pt-8">
        <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-slate-400">Explora los demás módulos</h2>
        <LearnNavigation />
      </section>
      <div className="mt-8 flex justify-between gap-4">
        {previous ? <Link href={`/learn/${LESSON_ROUTES[previous]}`} className="text-sm text-blue-300 hover:text-white">← Anterior</Link> : <span />}
        {next ? <Link href={`/learn/${LESSON_ROUTES[next]}`} className="text-sm text-blue-300 hover:text-white">Siguiente →</Link> : <Link href="/learn" className="text-sm text-blue-300 hover:text-white">Volver al inicio →</Link>}
      </div>
    </LearnLayout>
  );
}
