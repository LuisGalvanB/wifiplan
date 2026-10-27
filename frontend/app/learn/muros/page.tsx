import { LessonPage } from "@/components/learn/LessonPage";
import { isWallMaterial, isWifiBand } from "@/components/learn/wallAttenuation";

interface WallsPageProps {
  searchParams: Promise<{
    band?: string | string[];
    material?: string | string[];
  }>;
}

export default async function WallsPage({ searchParams }: WallsPageProps) {
  const { band, material } = await searchParams;
  return (
    <LessonPage
      scene="walls"
      initialBand={isWifiBand(band) ? band : undefined}
      initialMaterial={isWallMaterial(material) ? material : undefined}
    />
  );
}
