// frontend/src/components/risk/SeverityBadge.jsx

const SEVERITY_STYLE = {
  CRITICAL: { color: "#B3261E", label: "Critical" },
  WARNING: { color: "#A15C00", label: "Warning" },
  INFO: { color: "#1D6F5C", label: "Safe" },
};

export default function SeverityBadge({ severity }) {
  const style = SEVERITY_STYLE[severity] || SEVERITY_STYLE.INFO;
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        fontFamily: "var(--font-mono)",
        fontSize: "12px",
        fontWeight: 600,
        letterSpacing: "0.02em",
        color: style.color,
        border: `1px solid ${style.color}`,
        borderRadius: "3px",
        padding: "2px 8px",
        whiteSpace: "nowrap",
      }}
    >
      <span
        style={{
          width: "6px",
          height: "6px",
          borderRadius: "50%",
          background: style.color,
          display: "inline-block",
        }}
      />
      {style.label}
    </span>
  );
}
