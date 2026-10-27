import { create } from "zustand";
import { persist } from "zustand/middleware";
import { isAxiosError } from "axios";
import type { User, Organization } from "@/types";
import api from "@/lib/api";

interface AuthState {
  user: User | null;
  org: Organization | null;
  orgId: string | null;
  status: "initializing" | "authenticated" | "unauthenticated";
  authError: string | null;
  initialize: () => Promise<void>;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string, orgName: string, orgSlug: string) => Promise<void>;
  logout: () => void;
  fetchMe: () => Promise<void>;
  setOrg: (org: Organization) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      org: null,
      orgId: null,
      status: "initializing",
      authError: null,

      login: async (email, password) => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, org: null, orgId: null, status: "unauthenticated", authError: null });
        const { data } = await api.post("/auth/login", { email, password });
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        set({ status: "initializing" });
        await get().fetchMe();
        if (get().status !== "authenticated") {
          throw new Error("No se pudo validar la sesión iniciada.");
        }
      },

      register: async (email, password, fullName, orgName, orgSlug) => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, org: null, orgId: null, status: "unauthenticated", authError: null });
        const { data } = await api.post("/auth/register", {
          email,
          password,
          full_name: fullName,
          org_name: orgName,
          org_slug: orgSlug,
        });
        localStorage.setItem("access_token", data.access_token);
        localStorage.setItem("refresh_token", data.refresh_token);
        set({ status: "initializing" });
        await get().fetchMe();
        if (get().status !== "authenticated") {
          throw new Error("No se pudo validar la cuenta creada.");
        }
      },

      logout: () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        set({ user: null, org: null, orgId: null, status: "unauthenticated", authError: null });
      },

      initialize: async () => {
        if (
          !localStorage.getItem("access_token")
          && !localStorage.getItem("refresh_token")
        ) {
          set({ user: null, status: "unauthenticated", authError: null });
          return;
        }
        await get().fetchMe();
      },

      fetchMe: async () => {
        set({ status: "initializing", authError: null });
        try {
          const { data: user } = await api.get<User>("/auth/me");
          set({ user, status: "authenticated", authError: null });
        } catch (error) {
          if (isAxiosError(error) && error.response?.status === 401) {
            if (typeof window !== "undefined") {
              localStorage.removeItem("access_token");
              localStorage.removeItem("refresh_token");
            }
            set({ user: null, status: "unauthenticated", authError: null });
            return;
          }
          set({ authError: "No se pudo comprobar la sesión. Comprueba la conexión e inténtalo de nuevo." });
          throw error;
        }
      },

      setOrg: (org) => set({ org, orgId: org.id }),
    }),
    {
      name: "wifiplan-auth",
      partialize: (s) => ({ orgId: s.orgId, org: s.org }),
    }
  )
);
