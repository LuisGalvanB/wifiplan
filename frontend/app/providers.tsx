"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect } from "react";
import { useAuthStore } from "@/store/auth";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
});

export function Providers({ children }: { children: React.ReactNode }) {
  const fetchMe = useAuthStore((s) => s.fetchMe);
  const initialize = useAuthStore((s) => s.initialize);
  const status = useAuthStore((s) => s.status);
  const authError = useAuthStore((s) => s.authError);
  const logout = useAuthStore((s) => s.logout);

  useEffect(() => {
    const expireSession = () => logout();
    window.addEventListener("wifiplan:session-expired", expireSession);
    void initialize().catch(() => undefined);
    return () => window.removeEventListener("wifiplan:session-expired", expireSession);
  }, [initialize, logout]);

  if (status === "initializing") {
    return (
      <main className="flex min-h-screen items-center justify-center bg-gray-950 p-6 text-center text-gray-200">
        <div role="status" aria-live="polite">
          <p>{authError ?? "Comprobando la sesión…"}</p>
          {authError && (
            <button
              type="button"
              onClick={() => void fetchMe().catch(() => undefined)}
              className="mt-4 rounded-lg border border-blue-500 px-4 py-2 text-blue-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-300"
            >
              Reintentar
            </button>
          )}
        </div>
      </main>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
}
