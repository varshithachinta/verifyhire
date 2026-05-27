"use client";
import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { employerAPI } from "@/lib/api";
import { getRole } from "@/lib/auth";

export default function CandidatesPage() {
  const router = useRouter();
  const params = useParams();
  const jobId = params.id as string;
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (getRole() !== "employer") { router.push("/login"); return; }
    employerAPI.getJobCandidates(jobId)
      .then((res) => setData(res.data))
      .catch(() => setError("Failed to load candidates"))
      .finally(() => setLoading(false));
  }, [jobId]);

  if (loading) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", minHeight: "100vh", color: "var(--muted)" }}>
      Loading candidates...
    </div>
  );

  return (
    <div>
      <nav className="nav">
        <Link href="/employer/dashboard" style={{ fontSize: 18, fontWeight: 700, color: "var(--accent)", textDecoration: "none" }}>VerifyHire</Link>
        <Link href="/employer/dashboard"><button className="btn btn-outline" style={{ padding: "6px 14px", fontSize: 13 }}>← Dashboard</button></Link>
      </nav>

      <div className="page">
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Matched Candidates</h1>
        <p style={{ color: "var(--muted)", marginBottom: 32 }}>
          {data?.total_candidates || 0} candidates matched for this job · ranked by AI score
        </p>

        {error && (
          <div style={{ color: "var(--error)", background: "#450a0a", padding: "12px 16px", borderRadius: 8, marginBottom: 24 }}>{error}</div>
        )}

        {data?.candidates?.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: 48 }}>
            <div style={{ fontSize: 48, marginBottom: 16 }}>👷</div>
            <div style={{ fontWeight: 600, marginBottom: 8 }}>No candidates yet</div>
            <div style={{ color: "var(--muted)", fontSize: 14 }}>
              Workers who match this job's skills will appear here once they upload video resumes.
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {data?.candidates?.map((c: any, i: number) => (
              <div key={c.worker_id} className="card">
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                  <div>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                      <span style={{ fontSize: 13, color: "var(--muted)" }}>#{i + 1}</span>
                      <h3 style={{ fontWeight: 700, fontSize: 18 }}>{c.full_name || "Anonymous Worker"}</h3>
                      {c.face_verified && (
                        <span className="badge badge-green">✓ Verified</span>
                      )}
                    </div>
                    <div style={{ fontSize: 13, color: "var(--muted)" }}>
                      {c.location || "Location not set"}
                      {c.years_experience ? ` · ${c.years_experience} yrs experience` : ""}
                    </div>
                  </div>
                  <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 28, fontWeight: 800, color: "var(--accent)" }}>
                      {(c.final_score * 100).toFixed(0)}%
                    </div>
                    <div style={{ fontSize: 11, color: "var(--muted)" }}>match score</div>
                  </div>
                </div>

                <div style={{ display: "flex", gap: 16, marginBottom: 12, fontSize: 12 }}>
                  <div>
                    <span style={{ color: "var(--muted)" }}>Semantic: </span>
                    <span style={{ fontWeight: 600 }}>{(c.semantic_score * 100).toFixed(0)}%</span>
                  </div>
                  <div>
                    <span style={{ color: "var(--muted)" }}>Skill overlap: </span>
                    <span style={{ fontWeight: 600 }}>{(c.skill_score * 100).toFixed(0)}%</span>
                  </div>
                </div>

                {c.matched_skills?.length > 0 && (
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 6, marginBottom: 10 }}>
                    {c.matched_skills.map((s: string) => (
                      <span key={s} className="badge badge-green">✓ {s}</span>
                    ))}
                  </div>
                )}

                {c.skills?.length > 0 && (
                  <div>
                    <div style={{ fontSize: 12, color: "var(--muted)", marginBottom: 6 }}>All skills:</div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {c.skills.map((s: string) => (
                        <span key={s} className="badge badge-blue">{s}</span>
                      ))}
                    </div>
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