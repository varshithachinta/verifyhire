"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { authAPI } from "@/lib/api";
import { saveTokens } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await authAPI.login(form);
      const { access_token, refresh_token } = res.data;
      const payload = JSON.parse(atob(access_token.split(".")[1]));
      saveTokens(access_token, refresh_token, payload.role);
      if (payload.role === "employer") {
        router.push("/employer/dashboard");
      } else if (payload.role === "admin") {
        router.push("/admin");
      } else {
        router.push("/worker/dashboard");
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 24 }}>
      <div className="card" style={{ width: "100%", maxWidth: 420 }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: 24, fontWeight: 800, color: "var(--accent)" }}>VerifyHire</div>
          <div style={{ color: "var(--muted)", marginTop: 8 }}>Sign in to your account</div>
        </div>
        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" placeholder="you@example.com"
              value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} required />
          </div>
          <div>
            <label className="label">Password</label>
            <input className="input" type="password" placeholder="········"
              value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required />
          </div>
          {error && (
            <div style={{ color: "var(--error)", fontSize: 13, background: "#450a0a", padding: "10px 14px", borderRadius: 8 }}>
              {error}
            </div>
          )}
          <button className="btn btn-primary" type="submit" disabled={loading} style={{ width: "100%", padding: "12px" }}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
        <div style={{ textAlign: "center", marginTop: 20, fontSize: 13, color: "var(--muted)" }}>
          Don't have an account?{" "}
          <Link href="/register" style={{ color: "var(--accent)" }}>Register</Link>
        </div>
      </div>
    </div>
  );
}