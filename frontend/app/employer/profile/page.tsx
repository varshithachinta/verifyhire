"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { employerAPI } from "@/lib/api";
import { getRole } from "@/lib/auth";

export default function EmployerProfilePage() {
  const router = useRouter();
  const [form, setForm] = useState({ company_name: "", industry: "", location: "", description: "", website: "" });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (getRole() !== "employer") { router.push("/login"); return; }
    employerAPI.getProfile().then((res) => {
      const d = res.data;
      setForm({ company_name: d.company_name || "", industry: d.industry || "", location: d.location || "", description: d.description || "", website: d.website || "" });
    });
  }, []);

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await employerAPI.updateProfile(form);
      setMsg("Saved!");
      setTimeout(() => setMsg(""), 3000);
    } catch { setMsg("Save failed"); }
    finally { setSaving(false); }
  };

  return (
    <div>
      <nav className="nav">
        <Link href="/employer/dashboard" style={{ fontSize: 18, fontWeight: 700, color: "var(--accent)", textDecoration: "none" }}>VerifyHire</Link>
        <Link href="/employer/dashboard"><button className="btn btn-outline" style={{ padding: "6px 14px", fontSize: 13 }}>← Dashboard</button></Link>
      </nav>

      <div className="page" style={{ maxWidth: 600 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>Company Profile</h1>
        <form onSubmit={save} className="card" style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {[
            { key: "company_name", label: "Company Name", placeholder: "BuildRight Construction" },
            { key: "industry", label: "Industry", placeholder: "Construction" },
            { key: "location", label: "Location", placeholder: "Hyderabad, India" },
            { key: "website", label: "Website", placeholder: "https://example.com" },
          ].map((f) => (
            <div key={f.key}>
              <label className="label">{f.label}</label>
              <input className="input" placeholder={f.placeholder}
                value={(form as any)[f.key]}
                onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} />
            </div>
          ))}
          <div>
            <label className="label">Description</label>
            <textarea className="input" rows={3} placeholder="Tell workers about your company..."
              value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })}
              style={{ resize: "vertical" }} />
          </div>
          {msg && <div style={{ color: msg === "Saved!" ? "var(--success)" : "var(--error)", fontSize: 13 }}>{msg}</div>}
          <button className="btn btn-primary" type="submit" disabled={saving}>{saving ? "Saving..." : "Save Profile"}</button>
        </form>
      </div>
    </div>
  );
}