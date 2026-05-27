"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { workerAPI } from "@/lib/api";
import { getRole } from "@/lib/auth";

export default function MatchesPage() {
  const router = useRouter();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (getRole() !== "worker") { router.push("/login"); return; }
    workerAPI.getMatches()
      .then((res) => setData(res.data))
      .catch(() => router.push("/login"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", color: "var(--muted)" }}>Loading matches...</div>;

  return (
    <div>
      <nav className="nav">
        <Link href="/worker/dashboard" style={{ fontSize: 18, fontWeight: 700, color: "var(--accent)", textDecoration: "none" }}>VerifyHire</Link>
        <Link href="/worker/dashboard"><button className="btn btn-outline" style={{ padding: "6px 14px", fontSize: 13 }}>← Dashboard</button></Link>
      </nav>

      <div className="page">
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Job Matches</h1>
        <p style={{ color: "var(--muted)", marginBottom: 32 }}>
          {data?.total_jobs_evaluated || 0} jobs evaluated · {data?.matches?.length || 0} matches found
        </p>

        {data?.matches?.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: 48 }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>🎯</div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>No matches yet</div>
            <div style={{ color: "var(--muted)", fontSize: 14, marginBottom: 24 }}>
              Add skills to your profile or upload a video to get matched with jobs.
            </div>
            <div style={{ display: "flex", gap: 12, justifyContent: "center" }}>
              <Link href="/worker/upload"><button className="btn btn-primary">Upload Video</button></Link>
              <Link href="/worker/profile"><button className="btn btn-outline">Add Skills</button></Link>
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {data.matches.map((m: any, i: number) => (
              <div key={m.job.id} className="card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                      <span style={{ fontSize: 13, color: "var(--muted)" }}>#{i + 1}</span>
                      <h3 style={{ fontWeight: 700, fontSize: 18 }}>{m.job.title}</h3>
                    </div>
                    <div style={{ fontSize: 13, color: "var(--muted)" }}>
                      {m.job.location} · {m.job.employment_type?.replace("_", " ")} · ₹{m.job.salary_min?.toLocaleString()}–{m.job.salary_max?.toLocaleString()}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 28, fontWeight: 800, color: "var(--accent)" }}>
                      {(m.final_score * 100).toFixed(0)}%
                    </div>
                    <div style={{ fontSize: 11, color: "var(--muted)" }}>match score</div>
                  </div>
                </div>

                <p style={{ fontSize: 14, color: "var(--muted)", marginBottom: 12, lineHeight: 1.6 }}>
                  {m.job.description}
                </p>

                {/* Score breakdown */}
                <div style={{ display: "flex", gap: 16, marginBottom: 12, fontSize: 12 }}>
                  <div>
                    <span style={{ color: "var(--muted)" }}>Semantic: </span>
                    <span style={{ fontWeight: 600 }}>{(m.semantic_score * 100).toFixed(0)}%</span>
                  </div>
                  <div>
                    <span style={{ color: "var(--muted)" }}>Skill overlap: </span>
                    <span style={{ fontWeight: 600 }}>{(m.skill_score * 100).toFixed(0)}%</span>
                  </div>
                </div>

                {m.matched_skills?.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                    {m.matched_skills.map((s: string) => (
                      <span key={s} className="badge badge-green">✓ {s}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}