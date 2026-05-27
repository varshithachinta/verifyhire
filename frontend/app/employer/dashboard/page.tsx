"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { employerAPI } from "@/lib/api";
import { clearTokens, getRole } from "@/lib/auth";

export default function EmployerDashboard() {
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (getRole() !== "employer") { router.push("/login"); return; }
    Promise.all([employerAPI.getProfile(), employerAPI.getJobs()])
      .then(([p, j]) => { setProfile(p.data); setJobs(j.data); })
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, []);

  const logout = () => { clearTokens(); router.push("/login"); };

  if (loading) return <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", color: "var(--muted)" }}>Loading...</div>;

  return (
    <div>
      <nav className="nav">
        <span style={{ fontSize: 18, fontWeight: 700, color: "var(--accent)" }}>VerifyHire</span>
        <div style={{ display: "flex", gap: 16, alignItems: "center" }}>
          <Link href="/employer/profile" style={{ color: "var(--muted)", fontSize: 14 }}>Company Profile</Link>
          <Link href="/employer/jobs/new" style={{ color: "var(--muted)", fontSize: 14 }}>Post Job</Link>
          <button className="btn btn-outline" onClick={logout} style={{ padding: "6px 14px", fontSize: 13 }}>Logout</button>
        </div>
      </nav>

      <div className="page">
        <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 8 }}>
          {profile?.company_name || "Your Company"} Dashboard
        </h1>
        <p style={{ color: "var(--muted)", marginBottom: 32 }}>{profile?.industry} · {profile?.location}</p>

        {/* Stats */}
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 16, marginBottom: 32 }}>
          {[
            { label: "Active Jobs", value: jobs.filter((j) => j.is_active).length, icon: "💼" },
            { label: "Total Jobs", value: jobs.length, icon: "📋" },
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
          <div style={{ display: "flex", gap: 12 }}>
            <Link href="/employer/jobs/new"><button className="btn btn-primary">+ Post New Job</button></Link>
            <Link href="/employer/profile"><button className="btn btn-outline">Edit Company Profile</button></Link>
          </div>
        </div>

        {/* Jobs List */}
        <div className="card">
          <h2 style={{ fontWeight: 700, marginBottom: 16 }}>Your Job Postings</h2>
          {jobs.length === 0 ? (
            <div style={{ textAlign: "center", padding: 32, color: "var(--muted)" }}>
              No jobs posted yet. <Link href="/employer/jobs/new" style={{ color: "var(--accent)" }}>Post your first job →</Link>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {jobs.map((j) => (
                <div key={j.id} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "16px", background: "var(--bg)", borderRadius: 8 }}>
  <div>
    <div style={{ fontWeight: 600 }}>{j.title}</div>
    <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4 }}>
      {j.location} · {j.employment_type?.replace("_", " ")} · ₹{j.salary_min?.toLocaleString()}–{j.salary_max?.toLocaleString()}
    </div>
    <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
      {j.required_skills?.map((s: string) => (
        <span key={s} className="badge badge-blue">{s}</span>
      ))}
    </div>
  </div>
  <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: 8 }}>
    <span className={`badge ${j.is_active ? "badge-green" : "badge-red"}`}>
      {j.is_active ? "Active" : "Closed"}
    </span>
    <Link href={`/employer/jobs/${j.id}/candidates`}>
      <button className="btn btn-outline" style={{ padding: "4px 12px", fontSize: 12 }}>
        View Candidates →
      </button>
    </Link>
  </div>
</div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}