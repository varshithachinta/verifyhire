"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { employerAPI } from "@/lib/api";
import { getRole } from "@/lib/auth";

export default function NewJobPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    title: "", description: "", location: "",
    employment_type: "full_time", salary_min: "", salary_max: "",
  });
  const [skills, setSkills] = useState<string[]>([]);
  const [skillInput, setSkillInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (getRole() !== "employer") router.push("/login");
  }, []);

  const addSkill = () => {
    const s = skillInput.trim().toLowerCase();
    if (s && !skills.includes(s)) { setSkills([...skills, s]); setSkillInput(""); }
  };

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.title || !form.description) { setError("Title and description are required"); return; }
    setSaving(true);
    try {
      await employerAPI.createJob({
        ...form,
        required_skills: skills,
        salary_min: form.salary_min ? parseFloat(form.salary_min) : null,
        salary_max: form.salary_max ? parseFloat(form.salary_max) : null,
      });
      router.push("/employer/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to create job");
    } finally { setSaving(false); }
  };

  return (
    <div>
      <nav className="nav">
        <Link href="/employer/dashboard" style={{ fontSize: 18, fontWeight: 700, color: "var(--accent)", textDecoration: "none" }}>VerifyHire</Link>
        <Link href="/employer/dashboard"><button className="btn btn-outline" style={{ padding: "6px 14px", fontSize: 13 }}>← Dashboard</button></Link>
      </nav>

      <div className="page" style={{ maxWidth: 680 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Post a New Job</h1>
        <form onSubmit={submit} className="card" style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div>
            <label className="label">Job Title *</label>
            <input className="input" placeholder="e.g. Electrician Needed"
              value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} required />
          </div>
          <div>
            <label className="label">Description *</label>
            <textarea className="input" rows={4} placeholder="Describe the role, requirements, and responsibilities..."
              value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              style={{ resize: "vertical" }} required />
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <div>
              <label className="label">Location</label>
              <input className="input" placeholder="Hyderabad, India"
                value={form.location} onChange={(e) => setForm({ ...form, location: e.target.value })} />
            </div>
            <div>
              <label className="label">Employment Type</label>
              <select className="input" value={form.employment_type}
                onChange={(e) => setForm({ ...form, employment_type: e.target.value })}>
                <option value="full_time">Full Time</option>
                <option value="part_time">Part Time</option>
                <option value="contract">Contract</option>
                <option value="daily_wage">Daily Wage</option>
              </select>
            </div>
            <div>
              <label className="label">Min Salary (₹)</label>
              <input className="input" type="number" placeholder="20000"
                value={form.salary_min} onChange={(e) => setForm({ ...form, salary_min: e.target.value })} />
            </div>
            <div>
              <label className="label">Max Salary (₹)</label>
              <input className="input" type="number" placeholder="40000"
                value={form.salary_max} onChange={(e) => setForm({ ...form, salary_max: e.target.value })} />
            </div>
          </div>

          {/* Required Skills */}
          <div>
            <label className="label">Required Skills</label>
            <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
              <input className="input" placeholder="e.g. electrician"
                value={skillInput} onChange={(e) => setSkillInput(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addSkill())} />
              <button type="button" className="btn btn-outline" onClick={addSkill}>Add</button>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
              {skills.map((s) => (
                <div key={s} style={{ display: "flex", alignItems: "center", gap: 6, background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 999, padding: "4px 12px" }}>
                  <span style={{ fontSize: 13 }}>{s}</span>
                  <button type="button" onClick={() => setSkills(skills.filter((x) => x !== s))}
                    style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: 14 }}>×</button>
                </div>
              ))}
            </div>
          </div>

          {error && <div style={{ color: "var(--error)", fontSize: 13, background: "#450a0a", padding: "10px 14px", borderRadius: 8 }}>{error}</div>}

          <button className="btn btn-primary" type="submit" disabled={saving} style={{ padding: 12 }}>
            {saving ? "Posting..." : "Post Job →"}
          </button>
        </form>
      </div>
    </div>
  );
}