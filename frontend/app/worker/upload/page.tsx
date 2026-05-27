"use client";
import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { workerAPI } from "@/lib/api";
import { getRole } from "@/lib/auth";
import { useEffect } from "react";

export default function UploadPage() {
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<"idle" | "uploading" | "processing" | "done" | "error">("idle");
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (getRole() !== "worker") router.push("/login");
  }, []);

  const handleFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    if (f.size > 100 * 1024 * 1024) { setError("File too large. Max 100MB."); return; }
    setFile(f);
    setError("");
  };

  const handleUpload = async () => {
    if (!file) return;
    setStatus("uploading");
    setProgress(0);
    setError("");
    try {
      const res = await workerAPI.uploadVideo(file, setProgress);
      setStatus("processing");
      const videoId = res.data.id;

      // Poll for completion
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        try {
          const videos = await workerAPI.getVideos();
          const video = videos.data.find((v: any) => v.id === videoId);
          if (video?.status === "completed") {
            clearInterval(poll);
            setResult(video);
            setStatus("done");
          } else if (video?.status === "failed") {
            clearInterval(poll);
            setError("Processing failed. Make sure your face is visible and you're speaking clearly.");
            setStatus("error");
          } else if (attempts > 60) {
            clearInterval(poll);
            setError("Processing is taking too long. Check back later.");
            setStatus("error");
          }
        } catch {}
      }, 3000);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Upload failed");
      setStatus("error");
    }
  };

  return (
    <div>
      <nav className="nav">
        <Link href="/worker/dashboard" style={{ fontSize: 18, fontWeight: 700, color: "var(--accent)", textDecoration: "none" }}>VerifyHire</Link>
        <Link href="/worker/dashboard"><button className="btn btn-outline" style={{ padding: "6px 14px", fontSize: 13 }}>← Dashboard</button></Link>
      </nav>

      <div className="page" style={{ maxWidth: 700 }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, marginBottom: 8 }}>Upload Video Resume</h1>
        <p style={{ color: "var(--muted)", marginBottom: 32 }}>Record a 15-30 second video introducing yourself and your skills.</p>

        {/* Tips */}
        <div className="card" style={{ marginBottom: 24, borderColor: "var(--accent)" }}>
          <h3 style={{ fontWeight: 600, marginBottom: 12 }}>💡 Tips for a great video</h3>
          <ul style={{ color: "var(--muted)", fontSize: 13, paddingLeft: 20, lineHeight: 2 }}>
            <li>Face the camera clearly — good lighting helps</li>
            <li>Say your name, skills, and years of experience</li>
            <li>Example: "Hi, I'm Ravi. I'm an electrician with 5 years experience in wiring and installation."</li>
            <li>Keep it under 30 seconds for best results</li>
          </ul>
        </div>

        {/* Upload Area */}
        <div className="card" style={{ marginBottom: 24 }}>
          <div
            onClick={() => status === "idle" && fileRef.current?.click()}
            style={{
              border: "2px dashed var(--border)", borderRadius: 12, padding: 40,
              textAlign: "center", cursor: status === "idle" ? "pointer" : "default",
              transition: "border-color 0.2s",
            }}
            onDragOver={(e) => { e.preventDefault(); }}
            onDrop={(e) => {
              e.preventDefault();
              const f = e.dataTransfer.files[0];
              if (f) { setFile(f); setError(""); }
            }}
          >
            <div style={{ fontSize: 40, marginBottom: 12 }}>🎥</div>
            {file ? (
              <div>
                <div style={{ fontWeight: 600 }}>{file.name}</div>
                <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4 }}>
                  {(file.size / 1024 / 1024).toFixed(1)} MB
                </div>
              </div>
            ) : (
              <div>
                <div style={{ fontWeight: 600 }}>Drop video here or click to browse</div>
                <div style={{ fontSize: 13, color: "var(--muted)", marginTop: 4 }}>MP4, WebM, MOV up to 100MB</div>
              </div>
            )}
          </div>
          <input ref={fileRef} type="file" accept="video/*" onChange={handleFile} style={{ display: "none" }} />

          {/* Progress */}
          {(status === "uploading" || status === "processing") && (
            <div style={{ marginTop: 16 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: 13, marginBottom: 6 }}>
                <span style={{ color: "var(--muted)" }}>
                  {status === "uploading" ? `Uploading... ${progress}%` : "🤖 AI processing (face detection, transcription, skill extraction)..."}
                </span>
              </div>
              <div style={{ height: 6, background: "var(--border)", borderRadius: 999 }}>
                <div style={{
                  height: "100%", borderRadius: 999, background: "var(--accent)",
                  width: status === "uploading" ? `${progress}%` : "100%",
                  animation: status === "processing" ? "pulse 1.5s infinite" : "none",
                  transition: "width 0.3s",
                }} />
              </div>
            </div>
          )}

          {error && <div style={{ color: "var(--error)", fontSize: 13, background: "#450a0a", padding: "10px 14px", borderRadius: 8, marginTop: 12 }}>{error}</div>}

          {file && status === "idle" && (
            <button className="btn btn-primary" onClick={handleUpload} style={{ width: "100%", marginTop: 16, padding: 12 }}>
              Upload & Analyze Video →
            </button>
          )}
        </div>

        {/* Results */}
        {status === "done" && result && (
          <div className="card" style={{ borderColor: "var(--success)" }}>
            <h2 style={{ fontWeight: 700, marginBottom: 20, color: "var(--success)" }}>✅ Processing Complete!</h2>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 20 }}>
              <div style={{ padding: "12px 16px", background: "var(--bg)", borderRadius: 8 }}>
                <div style={{ fontSize: 12, color: "var(--muted)" }}>Face Detection</div>
                <div style={{ fontWeight: 600, marginTop: 4 }}>
                  {result.face_detected ? `✅ Detected (${(result.face_confidence * 100).toFixed(1)}% confidence)` : "❌ Not detected"}
                </div>
              </div>
              <div style={{ padding: "12px 16px", background: "var(--bg)", borderRadius: 8 }}>
                <div style={{ fontSize: 12, color: "var(--muted)" }}>Identity Verified</div>
                <div style={{ fontWeight: 600, marginTop: 4 }}>{result.face_verified ? "✅ Verified" : "❌ Not verified"}</div>
              </div>
              <div style={{ padding: "12px 16px", background: "var(--bg)", borderRadius: 8 }}>
                <div style={{ fontSize: 12, color: "var(--muted)" }}>Language</div>
                <div style={{ fontWeight: 600, marginTop: 4 }}>{result.detected_language?.toUpperCase() || "—"}</div>
              </div>
              <div style={{ padding: "12px 16px", background: "var(--bg)", borderRadius: 8 }}>
                <div style={{ fontSize: 12, color: "var(--muted)" }}>Duration</div>
                <div style={{ fontWeight: 600, marginTop: 4 }}>{result.audio_duration?.toFixed(1)}s</div>
              </div>
            </div>

            {result.transcript && (
              <div style={{ marginBottom: 16 }}>
                <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 8 }}>Transcript</div>
                <div style={{ padding: "12px 16px", background: "var(--bg)", borderRadius: 8, fontSize: 14, lineHeight: 1.6 }}>
                  {result.transcript}
                </div>
              </div>
            )}

            {result.processing_metadata?.skill_extraction?.detected_skills?.length > 0 && (
              <div>
                <div style={{ fontSize: 13, color: "var(--muted)", marginBottom: 8 }}>Skills Extracted</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
                  {result.processing_metadata.skill_extraction.detected_skills.map((s: string) => (
                    <span key={s} className="badge badge-blue">{s}</span>
                  ))}
                </div>
              </div>
            )}

            <div style={{ marginTop: 20, display: "flex", gap: 12 }}>
              <Link href="/worker/matches"><button className="btn btn-primary">View Job Matches →</button></Link>
              <button className="btn btn-outline" onClick={() => { setStatus("idle"); setFile(null); setResult(null); }}>Upload Another</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}