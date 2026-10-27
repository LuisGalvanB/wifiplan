"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/store/auth";
import api from "@/lib/api";
import type { Project } from "@/types";
import { PlusIcon, BuildingOffice2Icon, FolderIcon } from "@heroicons/react/24/outline";
import Link from "next/link";

interface MembershipInfo {
  organization_id: string;
  organization_name: string;
  organization_slug: string;
  role: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const { user, status, logout, orgId, org, setOrg } = useAuthStore();
  const qc = useQueryClient();
  const [newProject, setNewProject] = useState({ name: "", description: "" });
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    if (status === "unauthenticated") router.replace("/auth/login");
  }, [status, router]);

  // Fetch memberships to auto-resolve org if not set
  const { data: memberships } = useQuery({
    queryKey: ["my-memberships"],
    queryFn: () => api.get<MembershipInfo[]>("/auth/me/memberships").then((r) => r.data),
    enabled: status === "authenticated",
  });

  useEffect(() => {
    if (!orgId && memberships && memberships.length > 0) {
      const first = memberships[0];
      setOrg({
        id: first.organization_id,
        name: first.organization_name,
        slug: first.organization_slug,
        is_active: true,
      });
    }
  }, [memberships, orgId, setOrg]);

  const { data: projects = [], isLoading } = useQuery({
    queryKey: ["projects", orgId],
    queryFn: () =>
      api.get<Project[]>(`/orgs/${orgId}/projects`).then((r) => r.data),
    enabled: status === "authenticated" && !!orgId,
  });

  const createProject = useMutation({
    mutationFn: (data: { name: string; description: string }) =>
      api.post<Project>(`/orgs/${orgId}/projects`, data).then((r) => r.data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["projects", orgId] });
      setShowForm(false);
      setNewProject({ name: "", description: "" });
    },
  });

  if (status !== "authenticated") return null;

  // Org switcher (if user belongs to multiple orgs)
  const otherOrgs = (memberships ?? []).filter((m) => m.organization_id !== orgId);

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Topbar */}
      <header className="border-b border-gray-800 bg-gray-900 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-xl font-bold">📡 WifiPlan</span>
          {org && (
            <div className="flex items-center gap-1">
              <span className="text-sm text-gray-400 bg-gray-800 px-2 py-0.5 rounded">
                {org.name}
              </span>
              {otherOrgs.length > 0 && (
                <select
                  className="bg-transparent text-xs text-gray-500 focus:outline-none cursor-pointer"
                  onChange={(e) => {
                    const m = memberships?.find((x) => x.organization_id === e.target.value);
                    if (m) setOrg({ id: m.organization_id, name: m.organization_name, slug: m.organization_slug, is_active: true });
                  }}
                  defaultValue=""
                >
                  <option value="" disabled>Switch…</option>
                  {otherOrgs.map((m) => (
                    <option key={m.organization_id} value={m.organization_id}>{m.organization_name}</option>
                  ))}
                </select>
              )}
            </div>
          )}
        </div>
        <div className="flex items-center gap-4">
          <Link
            href="/learn"
            className="rounded-lg border border-blue-700/70 px-3 py-1.5 text-sm text-blue-300 transition-colors hover:border-blue-500 hover:text-white focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-400"
          >
            Aprende Wi-Fi
          </Link>
          <span className="text-sm text-gray-400">{user?.email}</span>
          <button
            onClick={logout}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-semibold">Projects</h1>
          <button
            onClick={() => setShowForm(true)}
            disabled={!orgId}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-40 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          >
            <PlusIcon className="w-4 h-4" />
            New Project
          </button>
        </div>

        {!orgId && (
          <div className="bg-yellow-900/30 border border-yellow-700 rounded-xl p-4 mb-6 text-sm text-yellow-300">
            Loading organization…
          </div>
        )}

        {/* Create project form */}
        {showForm && (
          <div className="mb-6 bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h2 className="font-medium mb-4">New Project</h2>
            <div className="space-y-3">
              <input
                value={newProject.name}
                onChange={(e) => setNewProject((f) => ({ ...f, name: e.target.value }))}
                placeholder="Project name (e.g. Bogotá HQ - Floor 3)"
                autoFocus
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
              <input
                value={newProject.description}
                onChange={(e) => setNewProject((f) => ({ ...f, description: e.target.value }))}
                placeholder="Description (optional)"
                className="w-full bg-gray-800 border border-gray-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-blue-500"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => createProject.mutate(newProject)}
                  disabled={!newProject.name || createProject.isPending}
                  className="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 px-4 py-2 rounded-lg text-sm font-medium transition-colors"
                >
                  {createProject.isPending ? "Creating…" : "Create Project"}
                </button>
                <button
                  onClick={() => { setShowForm(false); setNewProject({ name: "", description: "" }); }}
                  className="text-gray-400 hover:text-white px-4 py-2 rounded-lg text-sm"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Project grid */}
        {isLoading ? (
          <div className="text-gray-500 text-center py-16">Loading projects…</div>
        ) : projects.length === 0 ? (
          <div className="text-center py-16 text-gray-500">
            <FolderIcon className="w-12 h-12 mx-auto mb-3 opacity-30" />
            <p className="mb-1">No projects yet.</p>
            <p className="text-sm">Create one to start planning Wi-Fi coverage.</p>
          </div>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {projects.map((p) => (
              <button
                key={p.id}
                onClick={() => router.push(`/projects/${p.id}`)}
                className="text-left bg-gray-900 border border-gray-800 hover:border-blue-600 rounded-xl p-5 transition-colors group"
              >
                <BuildingOffice2Icon className="w-8 h-8 text-blue-500 mb-3 group-hover:text-blue-400 transition-colors" />
                <div className="font-medium group-hover:text-blue-300 transition-colors">{p.name}</div>
                {p.description && (
                  <p className="text-sm text-gray-500 mt-1 line-clamp-2">{p.description}</p>
                )}
                {p.address && (
                  <p className="text-xs text-gray-600 mt-1 truncate">📍 {p.address}</p>
                )}
                <p className="text-xs text-gray-600 mt-2">
                  {new Date(p.created_at).toLocaleDateString()}
                </p>
              </button>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
