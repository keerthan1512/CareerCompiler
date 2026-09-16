export default function HomePage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        background: "linear-gradient(135deg, #f0f4ff 0%, #fafafa 100%)",
      }}
    >
      {/* Logo / Badge */}
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: "0.5rem",
          background: "#eef2ff",
          color: "#4f46e5",
          borderRadius: "999px",
          padding: "0.35rem 1rem",
          fontSize: "0.8rem",
          fontWeight: 600,
          letterSpacing: "0.05em",
          textTransform: "uppercase",
          marginBottom: "2rem",
          border: "1px solid #c7d2fe",
        }}
      >
        <span>●</span>
        Phase 1 — Resume Foundation
      </div>

      {/* Headline */}
      <h1
        style={{
          fontSize: "clamp(2.5rem, 6vw, 4.5rem)",
          fontWeight: 800,
          letterSpacing: "-0.03em",
          lineHeight: 1.1,
          textAlign: "center",
          maxWidth: "800px",
          color: "#1a1a2e",
          marginBottom: "1.5rem",
        }}
      >
        Career
        <span style={{ color: "#4f46e5" }}>Compiler</span>
      </h1>

      {/* Subheadline */}
      <p
        style={{
          fontSize: "1.2rem",
          color: "#6b7280",
          maxWidth: "560px",
          textAlign: "center",
          lineHeight: 1.7,
          marginBottom: "3rem",
        }}
      >
        AI-powered resume engineering. One master LaTeX resume.
        Infinite factually-grounded, job-specific variants.
      </p>

      {/* Status cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "1rem",
          maxWidth: "760px",
          width: "100%",
          marginBottom: "3rem",
        }}
      >
        {[
          { label: "LaTeX Parser", status: "✅ Ready", detail: "TexSoup + pylatexenc" },
          { label: "FastAPI Backend", status: "✅ Ready", detail: "Python 3.12" },
          { label: "PostgreSQL", status: "⚡ Docker", detail: "pgvector/pgvector:pg16" },
          { label: "Job Intelligence", status: "🔜 Phase 2", detail: "JD ingestion" },
          { label: "Evidence Matching", status: "🔜 Phase 3", detail: "LangGraph agents" },
          { label: "ATS Engine", status: "🔜 Phase 5", detail: "Deterministic scoring" },
        ].map((card) => (
          <div
            key={card.label}
            style={{
              background: "#ffffff",
              borderRadius: "12px",
              padding: "1.25rem",
              border: "1px solid #e5e7eb",
              boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
            }}
          >
            <div style={{ fontSize: "0.75rem", color: "#9ca3af", marginBottom: "0.25rem" }}>
              {card.detail}
            </div>
            <div style={{ fontWeight: 600, fontSize: "0.9rem", marginBottom: "0.25rem" }}>
              {card.label}
            </div>
            <div style={{ fontSize: "0.85rem", color: "#4f46e5" }}>{card.status}</div>
          </div>
        ))}
      </div>

      {/* API links */}
      <div style={{ display: "flex", gap: "1rem", flexWrap: "wrap", justifyContent: "center" }}>
        <a
          href="http://localhost:8000/docs"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            background: "#4f46e5",
            color: "#fff",
            padding: "0.75rem 1.5rem",
            borderRadius: "8px",
            fontWeight: 600,
            fontSize: "0.9rem",
            textDecoration: "none",
            transition: "background 0.15s",
          }}
        >
          API Docs →
        </a>
        <a
          href="http://localhost:8000/api/v1/health"
          target="_blank"
          rel="noopener noreferrer"
          style={{
            background: "#f3f4f6",
            color: "#374151",
            padding: "0.75rem 1.5rem",
            borderRadius: "8px",
            fontWeight: 600,
            fontSize: "0.9rem",
            textDecoration: "none",
          }}
        >
          Health Check
        </a>
      </div>

      {/* Footer */}
      <p
        style={{
          marginTop: "4rem",
          fontSize: "0.8rem",
          color: "#9ca3af",
        }}
      >
        Full UI ships in Phase 7 · See{" "}
        <a href="https://github.com/keerthan1512/CareerCompiler" style={{ color: "#4f46e5" }}>
          GitHub
        </a>{" "}
        for progress
      </p>
    </main>
  );
}
