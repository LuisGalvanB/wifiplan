import { LessonPage } from "@/components/learn/LessonPage";
import { isWifiBand } from "@/components/learn/wallAttenuation";

interface SpectrumPageProps {
  searchParams: Promise<{ band?: string | string[] }>;
}

export default async function SpectrumPage({ searchParams }: SpectrumPageProps) {
  const { band } = await searchParams;
  return <LessonPage scene="spectrum" initialBand={isWifiBand(band) ? band : undefined} />;
}
