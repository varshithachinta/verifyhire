"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { workerAPI } from "@/lib/api";
import { clearTokens, getRole } from "@/lib/auth";

export default function WorkerDashboard() {
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [videos, setVideos] = useState<any[]>([]);
  const [matches, setMatches] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (getRole() !== "worker") { router.push("/login"); return; }
    Promise.all([
      workerAPI.getProfile(),
      workerAPI.getVideos(),
      workerAPI.getMatches(),
    ]).then(([p, v, m]) => {
      setProfile(p.data);
      setVideos(v.data);
      setMatches(m.data.matches || []);
    }).catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, []);

  const logout = () => { clearTokens(); router.push("/login"); };

  if (loading) return <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", color: "var(--muted)" }}>Loading...</div>;

  const completedVideos = videos.filter((v) => v.status === "completed");

  return (
    <div>
      <nav className="nav">
        <span style={{ fontSize: 18, fontWeight: 700, color: "var(--accent)" }}>VerifyHire</span>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <Link href="/worker/profile" style={{ color: "var(--muted)", fontSize: 14 }}>Profile</Link>
          <Link href="/worker/upload" style={{ color: "var(--muted)", fontSize: 14 }}>Upload Video</Link>
          <Link href="/worker/matches" style={{ color: "var(--muted)", fontSize: 14 }}>Matches</Link>
          <button className="btn btn-outline" onClick={logout} style={{ padding: "6px 14px", fontSize: 13 }}>Logout</button>
        </div>
      </nav>

      <div className="page">
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>
          Welcome back, {profile?.full_name || "Worker"} 👋
        </h1>
        <p style={{ color: "var(--muted)", marginBottom: 32 }}>
          {profile?.face_verified ? "✅ Identity verified" : "⚠️ Upload a video to verify your identity"}
        </p>

        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 32 }}>
          {[
            { label: "Skills", value: profile?.skills?.length || 0, icon: "🛠️" },
            { label: "Videos", value: videos.length, icon: "🎥" },
            { label: "Job Matches", value: matches.length, icon: "🎯" },
            { label: "Face Verified", value: profile?.face_verified ? "Yes" : "No", icon: "🔐" },
          ].map((s) => (
            <div key={s.label} className="card" style={{ textAlign: "center" }}>
              <div style={{ fontSize: 28 }}>{s.icon}</div>
              <div style={{ fontSize: 28, fontWeight: 800, marginTop: 8 }}>{s.value}</div>
              <div style={{ fontSize: 13, color: "var(--muted)" }}>{s.label}</div>
            </div>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="card" style={{ marginBottom: 24 }}>
          <h2 style={{ fontWeight: 700, marginBottom: 16 }}>Quick Actions</h2>
          <div style={{ display: "flex", gap: 12, flexWrap: "wrap" }}>
            <Link href="/worker/upload"><button className="btn btn-primary">🎥 Upload Video</button></Link>
            <Link href="/worker/profile"><button className="btn btn-outline">👤 Edit Profile</button></Link>
            <Link href="/worker/matches"><button className="btn btn-outline">🎯 View Matches</button></Link>
          </div>
        </div>

        {/* Recent Videos */}
        <div className="card">
          <h2 style={{ fontWeight: 700, marginBottom: 16 }}>Recent Videos</h2>
          {videos.length === 0 ? (
            <div style={{ color: "var(--muted)", textAlign: "center", padding: 32 }}>
              No videos yet. <Link href="/worker/upload" style={{ color: "var(--accent)" }}>Upload your first video →</Link>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {videos.slice(0, 3).map((v) => (
                <div key={v.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 16px", background: "var(--bg)", borderRadius: 8 }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{v.file_name}</div>
                    <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 4 }}>
                      {v.transcript ? v.transcript.slice(0, 80) + "..." : "Processing..."}
                    </div>
                  </div>
                  <span className={`badge ${v.status === "completed" ? "badge-green" : v.status === "failed" ? "badge-red" : "badge-yellow"}`}>
                    {v.status}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}