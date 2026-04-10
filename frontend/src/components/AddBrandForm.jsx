import { useState } from "react";

export default function AddBrandForm({ userId }) {
  const [domain, setDomain] = useState("");
  const [brandName, setBrandName] = useState("");
  const [returnDays, setReturnDays] = useState(15);
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!domain || !brandName) return;
    setLoading(true);
    setStatus(null);
    try {
      const res = await fetch("/api/brands/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          domain,
          brand_name: brandName,
          user_id: userId,
          return_days: returnDays,
          category: "fashion",
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setStatus({ type: "success", msg: data.success || data.info });
        setDomain("");
        setBrandName("");
      } else {
        setStatus({ type: "error", msg: data.detail || "Something went wrong" });
      }
    } catch (err) {
      setStatus({ type: "error", msg: "Network error" });
    }
    setLoading(false);
  };

  return (
    <div style={{
      background: "#1A1A1A", borderRadius: "12px", padding: "24px",
      border: "1px solid #2A2A2A", maxWidth: "480px", marginTop: "24px",
    }}>
      <h3 style={{ color: "#D4AF37", fontSize: "16px", fontWeight: 600, marginBottom: "4px" }}>
        Add a shopping brand
      </h3>
      <p style={{ color: "#888", fontSize: "13px", marginBottom: "20px" }}>
        Shop from a brand we don't track yet? Add it here and it works for everyone.
      </p>
      <form onSubmit={handleSubmit}>
        <div style={{ marginBottom: "14px" }}>
          <label style={{ color: "#aaa", fontSize: "12px", display: "block", marginBottom: "4px" }}>
            Store website
          </label>
          <input type="text" placeholder="e.g. virgio.com" value={domain}
            onChange={(e) => setDomain(e.target.value)}
            style={{ width: "100%", background: "#0A0A0A", border: "1px solid #333",
              borderRadius: "8px", padding: "10px 14px", color: "#fff", fontSize: "14px", outline: "none" }}
          />
        </div>
        <div style={{ marginBottom: "14px" }}>
          <label style={{ color: "#aaa", fontSize: "12px", display: "block", marginBottom: "4px" }}>
            Brand name
          </label>
          <input type="text" placeholder="e.g. Virgio" value={brandName}
            onChange={(e) => setBrandName(e.target.value)}
            style={{ width: "100%", background: "#0A0A0A", border: "1px solid #333",
              borderRadius: "8px", padding: "10px 14px", color: "#fff", fontSize: "14px", outline: "none" }}
          />
        </div>
        <div style={{ marginBottom: "20px" }}>
          <label style={{ color: "#aaa", fontSize: "12px", display: "block", marginBottom: "4px" }}>
            Return window (days)
          </label>
          <input type="number" min={1} max={365} value={returnDays}
            onChange={(e) => setReturnDays(parseInt(e.target.value) || 15)}
            style={{ width: "100px", background: "#0A0A0A", border: "1px solid #333",
              borderRadius: "8px", padding: "10px 14px", color: "#fff", fontSize: "14px", outline: "none" }}
          />
        </div>
        <button type="submit" disabled={loading || !domain || !brandName}
          style={{ width: "100%", padding: "12px",
            background: loading ? "#333" : "#D4AF37",
            color: loading ? "#888" : "#0A0A0A",
            border: "none", borderRadius: "8px", fontSize: "14px", fontWeight: 600,
            cursor: loading ? "wait" : "pointer" }}>
          {loading ? "Adding..." : "Add brand"}
        </button>
      </form>
      {status && (
        <div style={{
          marginTop: "14px", padding: "10px 14px", borderRadius: "8px", fontSize: "13px",
          background: status.type === "success" ? "#22C55E22" : "#EF444422",
          color: status.type === "success" ? "#22C55E" : "#EF4444",
          border: "1px solid " + (status.type === "success" ? "#22C55E44" : "#EF444444"),
        }}>
          {status.msg}
        </div>
      )}
    </div>
  );
}
