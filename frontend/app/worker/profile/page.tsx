"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { workerAPI } from "@/lib/api";
import { getRole } from "@/lib/auth";

export default function WorkerProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [skills, setSkills] = useState<any[]>([]);
  const [form, setForm] = useState({ full_name: "", bio: "", location: "", phone: "", years_experience: "" });
  const [newSkill, setNewSkill] = useState("");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (getRole() !== "worker") { router.push("/login"); return; }
    Promise.all([workerAPI.getProfile(), workerAPI.getSkills()]).then(([p, s]) => {
      setProfile(p.data);
      setSkills(s.data);
      setForm({
        full_name: p.data.full_name || "",
        bio: p.data.bio || "",
        location: p.data.location || "",
        phone: p.data.phone || "",
        years_experience: p.data.years_experience || "",
      });
    });
  }, []);

  const saveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await workerAPI.updateProfile({
        ...form,
        years_experience: form.years_experience ? parseInt(form.years_experience) : null,
      });
      setMsg("Profile saved!");
      setTimeout(() => setMsg(""), 3000);
    } catch { setMsg("Save failed"); }
    finally { setSaving(false); }
  };

  const addSkill = async () => {
    if (!newSkill.trim()) return;
    try {
      const res = await workerAPI.addSkill({ skill_name: newSkill.trim() });
      setSkills([...skills, res.data]);
      setNewSkill("");
    } catch {}
  };

  const deleteSkill = async (id: string) => {
    try {
      await workerAPI.deleteSkill(id);
      setSkills(skills.filter((s) => s.id !== id));
    } catch {}
  };

  return (
    <div>
      <nav className="nav">
        <Link href="/worker/dashboard" style={{ fontSize: 18, fontWeight: 700, color: "var(--accent)", textDecoration: "none" }}>VerifyHire</Link>
        <Link href="/worker/dashboard"><button className="btn btn-outline" style={{ padding: "6px 14px", fontSize: 13 }}>← Dashboard</button></Link>
      </nav>

      <div className="page" style={{ maxWidth: 700 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 24 }}>My Profile</h1>

        <form onSubmit={saveProfile} className="card" style={{ marginBottom: 24 }}>
          <h2 style={{ fontWeight: 700, marginBottom: 20 }}>Personal Information</h2>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {[
              { key: "full_name", label: "Full Name", placeholder: "Ravi Kumar" },
              { key: "phone", label: "Phone", placeholder: "+91 98765 43210" },
              { key: "location", label: "Location", placeholder: "Hyderabad, India" },
              { key: "years_experience", label: "Years Experience", placeholder: "5", type: "number" },
            ].map((f) => (
              <div key={f.key}>
                <label className="label">{f.label}</label>
                <input className="input" type={f.type || "text"} placeholder={f.placeholder}
                  value={(form as any)[f.key]}
                  onChange={(e) => setForm({ ...form, [f.key]: e.target.value })} />
              </div>
            ))}
          </div>
          <div style={{ marginTop: 16 }}>
            <label className="label">Bio</label>
            <textarea className="input" rows={3} placeholder="Describe your experience and skills..."
              value={form.bio} onChange={(e) => setForm({ ...form, bio: e.target.value })}
              style={{ resize: "vertical" }} />
          </div>
          {msg && <div style={{ color: msg.includes("failed") ? "var(--error)" : "var(--success)", fontSize: 13, marginTop: 12 }}>{msg}</div>}
          <button className="btn btn-primary" type="submit" disabled={saving} style={{ marginTop: 16 }}>
            {saving ? "Saving..." : "Save Profile"}
          </button>
        </form>

        {/* Skills */}
        <div className="card">
          <h2 style={{ fontWeight: 700, marginBottom: 16 }}>Skills</h2>
          <div style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            <input className="input" placeholder="Add a skill (e.g. welding)"
              value={newSkill} onChange={(e) => setNewSkill(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addSkill())} />
            <button className="btn btn-primary" onClick={addSkill} style={{ whiteSpace: "nowrap" }}>Add</button>
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
            {skills.map((s) => (
              <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 6, background: "var(--bg)", border: "1px solid var(--border)", borderRadius: 999, padding: "4px 12px" }}>
                <span style={{ fontSize: 13 }}>{s.skill_name}</span>
                {s.is_ai_extracted && <span style={{ fontSize: 10, color: "var(--accent)" }}>AI</span>}
                <button onClick={() => deleteSkill(s.id)} style={{ background: "none", border: "none", color: "var(--muted)", cursor: "pointer", fontSize: 14, lineHeight: 1 }}>×</button>
              </div>
            ))}
            {skills.length === 0 && <span style={{ color: "var(--muted)", fontSize: 13 }}>No skills added yet</span>}
          </div>
        </div>
      </div>
    </div>
  );
}