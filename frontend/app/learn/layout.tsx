import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Aprende Wi-Fi | WifiPlan",
  description: "Módulos interactivos en español sobre Wi-Fi, radiofrecuencia y planificación inalámbrica.",
};

export default function LearnRootLayout({ children }: { children: React.ReactNode }) {
  return children;
}
