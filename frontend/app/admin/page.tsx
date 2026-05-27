"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { getRole, clearTokens } from "@/lib/auth";
import Link from "next/link";

export default function AdminPage() {
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [users, setUsers] = useState<any[]>([]);
  const [videos, setVideos] = useState<any[]>([]);
  const [tab, setTab] = useState<"overview" | "users" | "videos">("overview");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (getRole() !== "admin") { router.push("/login"); return; }
    Promise.all([
      api.get("/admin/stats"),
      api.get("/admin/users"),
      api.get("/admin/videos"),
    ]).then(([s, u, v]) => {
      setStats(s.data);
      setUsers(u.data);
      setVideos(v.data);
    }).catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, []);

  const deactivateUser = async (userId: string) => {
    if (!confirm("Deactivate this user?")) return;
    try {
      await api.patch(`/admin/users/${userId}/deactivate`);
      setUsers(users.map(u => u.id === userId ? { ...u, is_active: false } : u));
    } catch {}
  };

  const logout = () => { clearTokens(); router.push("/login"); };

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", color: "var(--muted)" }}>
      Loading...
    </div>
  );

  return (
    <div>
      <nav className="nav">
        <span style={{ fontSize: 18, fontWeight: 700, color: "var(--accent)" }}>VerifyHire Admin</span>
        <button className="btn btn-outline" onClick={logout} style={{ padding: "6px 14px", fontSize: 13 }}>Logout</button>
      </nav>

      <div className="page">
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 32 }}>Admin Panel</h1>

        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 16, marginBottom: 32 }}>
          {[
            { label: "Total Users", value: stats?.total_users, icon: "👥" },
            { label: "Workers", value: stats?.total_workers, icon: "👷" },
            { label: "Employers", value: stats?.total_employers, icon: "🏢" },
            { label: "Active Jobs", value: stats?.active_jobs, icon: "💼" },
            { label: "Videos", value: stats?.total_videos, icon: "🎥" },
            { label: "Completed", value: stats?.completed_videos, icon: "✅" },
            { label: "Failed", value: stats?.failed_videos, icon: "❌" },
          ].map((s) => (
            <div key={s.label} className="card" style={{ textAlign: "center" }}>
              <div style={{ fontSize: 24 }}>{s.icon}</div>
              <div style={{ fontSize: 24, fontWeight: 800, marginTop: 8 }}>{s.value ?? 0}</div>
              <div style={{ fontSize: 12, color: "var(--muted)" }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 4, marginBottom: 24, background: "var(--surface)", borderRadius: 8, padding: 4 }}>
          {(["overview", "users", "videos"] as const).map((t) => (
            <button key={t} onClick={() => setTab(t)}
              style={{
                flex: 1, padding: "8px", borderRadius: 6, border: "none", cursor: "pointer",
                background: tab === t ? "var(--accent)" : "transparent",
                color: tab === t ? "white" : "var(--muted)",
                fontWeight: 600, fontSize: 13, textTransform: "capitalize",
              }}>
              {t === "overview" ? "📊 Overview" : t === "users" ? "👥 Users" : "🎥 Videos"}
            </button>
          ))}
        </div>

        {/* Overview Tab */}
        {tab === "overview" && (
          <div className="card">
            <h2 style={{ fontWeight: 700, marginBottom: 16 }}>System Health</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {[
                { label: "Video success rate", value: stats?.total_videos > 0 ? `${((stats.completed_videos / stats.total_videos) * 100).toFixed(0)}%` : "N/A" },
                { label: "Total job postings", value: stats?.total_jobs },
                { label: "Active job postings", value: stats?.active_jobs },
              ].map((r) => (
                <div key={r.label} style={{ display: "flex", justifyContent: "space-between", padding: "10px 0", borderBottom: "1px solid var(--border)" }}>
                  <span style={{ color: "var(--muted)", fontSize: 14 }}>{r.label}</span>
                  <span style={{ fontWeight: 600 }}>{r.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Users Tab */}
        {tab === "users" && (
          <div className="card">
            <h2 style={{ fontWeight: 700, marginBottom: 16 }}>All Users ({users.length})</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {users.map((u) => (
                <div key={u.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", background: "var(--bg)", borderRadius: 8 }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{u.email}</div>
                    <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
                      {u.role} · joined {new Date(u.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                    <span className={`badge ${u.is_active ? "badge-green" : "badge-red"}`}>
                      {u.is_active ? "Active" : "Inactive"}
                    </span>
                    {u.is_active && u.role !== "admin" && (
                      <button className="btn btn-danger" onClick={() => deactivateUser(u.id)}
                        style={{ padding: "4px 10px", fontSize: 12 }}>
                        Deactivate
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Videos Tab */}
        {tab === "videos" && (
          <div className="card">
            <h2 style={{ fontWeight: 700, marginBottom: 16 }}>Recent Videos (last 50)</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {videos.map((v) => (
                <div key={v.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", background: "var(--bg)", borderRadius: 8 }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{v.file_name || "unnamed"}</div>
                    <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
                      {new Date(v.created_at).toLocaleString()}
                      {v.face_verified ? " · ✅ face verified" : v.face_detected === false ? " · ❌ no face" : ""}
                    </div>
                  </div>
                  <span className={`badge ${v.status === "completed" ? "badge-green" : v.status === "failed" ? "badge-red" : "badge-yellow"}`}>
                    {v.status}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}