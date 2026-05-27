"use client";
import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { authAPI } from "@/lib/api";
import { saveTokens } from "@/lib/auth";
import { Suspense } from "react";

function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [form, setForm] = useState({
    email: "", password: "", role: params.get("role") || "worker"
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setLoading(true);
    setError("");
    try {
      const res = await authAPI.register(form);
      const { access_token, refresh_token } = res.data;
      const payload = JSON.parse(atob(access_token.split(".")[1]));
      saveTokens(access_token, refresh_token, payload.role);
      if (payload.role === "employer") router.push("/employer/dashboard");
      else router.push("/worker/dashboard");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div className="card" style={{ width: "100%", maxWidth: 420 }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: 24, fontWeight: 800, color: "var(--accent)" }}>VerifyHire</div>
          <div style={{ color: "var(--muted)", marginTop: 8 }}>Create your account</div>
        </div>

        {/* Role Toggle */}
        <div style={{ display: "flex", background: "var(--bg)", borderRadius: 8, padding: 4, marginBottom: 24 }}>
          {["worker", "employer"].map((r) => (
            <button key={r} type="button"
              onClick={() => setForm({ ...form, role: r })}
              style={{
                flex: 1, padding: "8px", borderRadius: 6, border: "none", cursor: "pointer",
                background: form.role === r ? "var(--accent)" : "transparent",
                color: form.role === r ? "white" : "var(--muted)",
                fontWeight: 600, fontSize: 14, textTransform: "capitalize"
              }}>
              {r === "worker" ? "👷 Worker" : "🏢 Employer"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" placeholder="you@example.com"
              value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </div>
          <div>
            <label className="label">Password</label>
            <input className="input" type="password" placeholder="Min 8 characters"
              value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          </div>

          {error && <div style={{ color: "var(--error)", fontSize: 13, background: "#450a0a", padding: "10px 14px", borderRadius: 8 }}>{error}</div>}

          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%", padding: "12px" }}>
            {loading ? "Creating account..." : `Create ${form.role} account`}
          </button>
        </form>

        <div style={{ textAlign: "center", marginTop: 20, fontSize: 13, color: "var(--muted)" }}>
          Already have an account?{" "}
          <Link href="/login" style={{ color: "var(--accent)" }}>Sign in</Link>
        </div>
      </div>
    </div>
  );
}

export default function RegisterPage() {
  return <Suspense><RegisterForm /></Suspense>;
}