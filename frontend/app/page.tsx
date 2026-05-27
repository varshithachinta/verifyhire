"use client";
import Link from "next/link";

export default function Home() {
  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)" }}>
      {/* Nav */}
      <nav className="nav">
        <span style={{ fontSize: 20, fontWeight: 700, color: "var(--accent)" }}>
          VerifyHire
        </span>
        <div style={{ display: "flex", gap: 12 }}>
          <Link href="/login">
            <button className="btn btn-outline">Login</button>
          </Link>
          <Link href="/register">
            <button className="btn btn-primary">Get Started</button>
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <div style={{ textAlign: "center", padding: "80px 24px 40px" }}>
        <div className="badge badge-blue" style={{ marginBottom: 20 }}>
          AI-Powered Video Hiring
        </div>
        <h1 style={{ fontSize: 52, fontWeight: 800, lineHeight: 1.1, marginBottom: 20 }}>
          Get Hired Based on{" "}
          <span style={{ color: "var(--accent)" }}>Your Skills</span>
          <br />Not Your Resume
        </h1>
        <p style={{ fontSize: 18, color: "var(--muted)", maxWidth: 600, margin: "0 auto 40px" }}>
          Upload a short video. Our AI verifies your identity, transcribes your
          speech, extracts your skills, and matches you with the right jobs.
        </p>
        <div style={{ display: "flex", gap: 16, justifyContent: "center" }}>
          <Link href="/register">
            <button className="btn btn-primary" style={{ padding: "14px 32px", fontSize: 16 }}>
              Upload Video Resume →
            </button>
          </Link>
          <Link href="/register?role=employer">
            <button className="btn btn-outline" style={{ padding: "14px 32px", fontSize: 16 }}>
              Post a Job
            </button>
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: "flex", justifyContent: "center", gap: 48, padding: "40px 24px" }}>
        {[
          { n: "3B+", label: "Blue-collar workers globally" },
          { n: "AI", label: "Face + Speech verification" },
          { n: "SBERT", label: "Semantic job matching" },
        ].map((s) => (
          <div key={s.label} style={{ textAlign: "center" }}>
            <div style={{ fontSize: 32, fontWeight: 800, color: "var(--accent)" }}>{s.n}</div>
            <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Features */}
      <div style={{ maxWidth: 1000, margin: "0 auto", padding: "40px 24px", display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 20 }}>
        {[
          { icon: "🎥", title: "Video Resume", desc: "Record once, apply everywhere. No writing needed." },
          { icon: "🧠", title: "AI Face Verify", desc: "YOLOv8 + ArcFace ensure your identity is real." },
          { icon: "🗣️", title: "Speech to Skills", desc: "Whisper transcribes. spaCy extracts your skills." },
          { icon: "🎯", title: "Smart Matching", desc: "SBERT semantic matching finds the right jobs." },
        ].map((f) => (
          <div key={f.title} className="card">
            <div style={{ fontSize: 28, marginBottom: 12 }}>{f.icon}</div>
            <div style={{ fontWeight: 700, marginBottom: 8 }}>{f.title}</div>
            <div style={{ fontSize: 13, color: "var(--muted)" }}>{f.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}