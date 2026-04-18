import { useState, useRef } from "react";

const COLORS = {
  high:   { bg: "#FEF2F2", border: "#FCA5A5", text: "#991B1B", badge: "#EF4444" },
  medium: { bg: "#FFFBEB", border: "#FCD34D", text: "#92400E", badge: "#F59E0B" },
  low:    { bg: "#F0FDF4", border: "#86EFAC", text: "#14532D", badge: "#22C55E" },
};

const API = "http://localhost:8000/api/v1";

const PATIENTS = [
  { id: "SCAN-A3F9B2", name: "James Okafor",    age: 67, gender: "M", risk: "high",   confidence: 0.91, tumor: true,  urgency: "Immediate", scan_date: "2025-04-18" },
  { id: "SCAN-B7D4E9", name: "Priya Menon",     age: 44, gender: "F", risk: "medium", confidence: 0.76, tumor: true,  urgency: "Moderate",  scan_date: "2025-04-18" },
  { id: "SCAN-C1F2D3", name: "Sofia Reyes",     age: 29, gender: "F", risk: "low",    confidence: 0.94, tumor: false, urgency: "Low",       scan_date: "2025-04-17" },
  { id: "SCAN-D8A1C5", name: "Daniel Hartmann", age: 72, gender: "M", risk: "high",   confidence: 0.88, tumor: true,  urgency: "Immediate", scan_date: "2025-04-17" },
  { id: "SCAN-E5B3F9", name: "Yuki Tanaka",     age: 38, gender: "F", risk: "low",    confidence: 0.89, tumor: false, urgency: "Low",       scan_date: "2025-04-16" },
  { id: "SCAN-F9C4E1", name: "Marcus Webb",     age: 55, gender: "M", risk: "medium", confidence: 0.73, tumor: true,  urgency: "Moderate",  scan_date: "2025-04-16" },
];

const RESOURCES = {
  icu_beds: { total: 10, occupied: 7, available: 3 },
  doctors:  { total: 5,  on_duty: 4,  available: 1 },
  ot_rooms: { total: 3,  in_use: 2,   available: 1 },
  waiting_queue: { patients_waiting: 2 },
};

const DECISION = {
  urgency: "Immediate",
  doctor_type: "Neurosurgeon (Senior)",
  suggested_action: "Emergency neurosurgical assessment and ICU admission.",
  next_steps: [
    "Activate emergency protocol immediately",
    "Transfer patient to ICU",
    "Order contrast-enhanced MRI within 2 hours",
    "Alert on-call neurosurgeon",
    "Initiate IV corticosteroids to reduce cerebral edema",
    "Consent for possible surgical intervention",
    "Notify next-of-kin",
  ],
  estimated_wait_hours: 0.5,
  alert_er: true,
};

const WEEKLY = [12, 19, 8, 24, 17, 21, 14];
const DAYS   = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"];

const rs = (r) => COLORS[r] ?? COLORS.low;
const initials = (n) => n.split(" ").map(x => x[0]).join("").slice(0,2).toUpperCase();

// ── RiskBadge ──────────────────────────────────────────────────────
function RiskBadge({ level }) {
  const s = rs(level);
  return (
    <span style={{ background: s.bg, color: s.text, border: `1px solid ${s.border}`,
      borderRadius: 20, fontSize: 10, fontWeight: 700, padding: "2px 10px",
      textTransform: "uppercase", letterSpacing: "0.05em" }}>
      {level}
    </span>
  );
}

// ── Avatar ─────────────────────────────────────────────────────────
function Avatar({ name, size = 38 }) {
  const bgs  = ["#DBEAFE","#DCFCE7","#FEF3C7","#FCE7F3","#EDE9FE"];
  const txts = ["#1E40AF","#166534","#92400E","#9D174D","#4C1D95"];
  const i    = name.charCodeAt(0) % 5;
  return (
    <div style={{ width: size, height: size, borderRadius: "50%", background: bgs[i],
      color: txts[i], display: "flex", alignItems: "center", justifyContent: "center",
      fontSize: size * 0.33, fontWeight: 800, flexShrink: 0 }}>
      {initials(name)}
    </div>
  );
}

// ── AlertBanner ────────────────────────────────────────────────────
function AlertBanner({ message, type = "warning", onDismiss }) {
  const c = {
    warning: { bg:"#FFFBEB", border:"#F59E0B", text:"#92400E", dot:"#F59E0B" },
    danger:  { bg:"#FEF2F2", border:"#EF4444", text:"#991B1B", dot:"#EF4444" },
    info:    { bg:"#EFF6FF", border:"#3B82F6", text:"#1E40AF", dot:"#3B82F6" },
  }[type];
  return (
    <div style={{ background: c.bg, border: `1px solid ${c.border}`, borderRadius: 10,
      padding: "10px 14px", display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
      <div style={{ width: 7, height: 7, borderRadius: "50%", background: c.dot, flexShrink: 0 }} />
      <span style={{ fontSize: 13, color: c.text, flex: 1 }}>{message}</span>
      {onDismiss && (
        <button onClick={onDismiss} style={{ background:"none", border:"none",
          color: c.text, cursor:"pointer", fontSize: 18, padding: 0, lineHeight: 1 }}>×</button>
      )}
    </div>
  );
}

// ── BarChart ───────────────────────────────────────────────────────
function BarChart({ data, labels }) {
  const max = Math.max(...data);
  return (
    <div style={{ display:"flex", alignItems:"flex-end", gap: 5, height: 72 }}>
      {data.map((v, i) => (
        <div key={i} style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", gap: 3 }}>
          <div style={{ width:"100%", background:"#818CF8", borderRadius:"3px 3px 0 0",
            height: `${(v/max)*58}px` }} />
          <span style={{ fontSize: 9, color:"#9CA3AF", fontWeight: 600 }}>{labels[i]}</span>
        </div>
      ))}
    </div>
  );
}

// ── DonutRing ──────────────────────────────────────────────────────
function DonutRing({ used, total, color, label }) {
  const r = 28, cx = 36, cy = 36, circ = 2 * Math.PI * r;
  const dash = circ * (total > 0 ? used / total : 0);
  return (
    <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap: 4 }}>
      <svg width="72" height="72" viewBox="0 0 72 72">
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="#F3F4F6" strokeWidth="9" />
        <circle cx={cx} cy={cy} r={r} fill="none" stroke={color} strokeWidth="9"
          strokeDasharray={`${dash} ${circ - dash}`} strokeDashoffset={circ * 0.25}
          strokeLinecap="round" />
        <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central"
          fontSize="13" fontWeight="800" fill="#111827">{used}</text>
        <text x={cx} y={cy+12} textAnchor="middle" dominantBaseline="central"
          fontSize="8" fill="#9CA3AF">/{total}</text>
      </svg>
      <span style={{ fontSize: 11, color:"#374151", fontWeight: 600 }}>{label}</span>
    </div>
  );
}

// ── ProgressBar ────────────────────────────────────────────────────
function ProgressBar({ pct, color }) {
  return (
    <div style={{ height: 6, background:"#F3F4F6", borderRadius: 3, overflow:"hidden" }}>
      <div style={{ height:"100%", width:`${pct}%`, background: color, borderRadius: 3 }} />
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// PAGE 1 — Dashboard
// ══════════════════════════════════════════════════════════════════
function DashboardPage({ onSelect }) {
  const [alerts, setAlerts] = useState([
    { id:1, msg:"SCAN-A3F9B2 — High-risk tumor detected. Immediate neurosurgery required.", type:"danger" },
    { id:2, msg:"ICU at 70% capacity — monitor resource levels closely.", type:"warning" },
    { id:3, msg:"2 patients in resource queue. Surge capacity may be needed.", type:"warning" },
  ]);
  const high   = PATIENTS.filter(p => p.risk === "high").length;
  const med    = PATIENTS.filter(p => p.risk === "medium").length;
  const low    = PATIENTS.filter(p => p.risk === "low").length;
  const icuPct = Math.round((RESOURCES.icu_beds.occupied / RESOURCES.icu_beds.total) * 100);

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ margin:"0 0 2px", fontSize: 22, fontWeight: 800, color:"#111827" }}>Clinical Overview</h2>
        <p style={{ margin: 0, fontSize: 13, color:"#6B7280" }}>Real-time neurology intelligence dashboard</p>
      </div>

      {alerts.map(a => (
        <AlertBanner key={a.id} message={a.msg} type={a.type}
          onDismiss={() => setAlerts(prev => prev.filter(x => x.id !== a.id))} />
      ))}

      {/* Stat cards */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap: 12, margin:"20px 0" }}>
        {[
          { label:"Total Patients", value: PATIENTS.length, accent:"#6366F1" },
          { label:"High Risk",      value: high,            accent:"#EF4444" },
          { label:"Medium Risk",    value: med,             accent:"#F59E0B" },
          { label:"Low Risk",       value: low,             accent:"#22C55E" },
          { label:"ICU Load",       value:`${icuPct}%`,     accent: icuPct >= 70 ? "#EF4444" : "#6366F1" },
        ].map(({ label, value, accent }) => (
          <div key={label} style={{ background:"#fff", border:"1px solid #E5E7EB",
            borderRadius: 12, padding:"14px 16px", borderTop:`3px solid ${accent}` }}>
            <p style={{ margin:"0 0 6px", fontSize: 10, color:"#6B7280", fontWeight: 700,
              textTransform:"uppercase", letterSpacing:"0.06em" }}>{label}</p>
            <p style={{ margin: 0, fontSize: 28, fontWeight: 800, color:"#111827", lineHeight: 1 }}>{value}</p>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1.6fr", gap: 16, marginBottom: 24 }}>
        <div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius: 14, padding: 20 }}>
          <p style={{ margin:"0 0 3px", fontSize: 12, fontWeight: 700, color:"#374151" }}>Scans this week</p>
          <p style={{ margin:"0 0 16px", fontSize: 10, color:"#9CA3AF" }}>MRI uploads per day</p>
          <BarChart data={WEEKLY} labels={DAYS} />
        </div>
        <div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius: 14, padding: 20 }}>
          <p style={{ margin:"0 0 3px", fontSize: 12, fontWeight: 700, color:"#374151" }}>Resource snapshot</p>
          <p style={{ margin:"0 0 16px", fontSize: 10, color:"#9CA3AF" }}>Real-time hospital capacity</p>
          <div style={{ display:"flex", gap: 28, justifyContent:"center" }}>
            <DonutRing used={RESOURCES.icu_beds.occupied} total={RESOURCES.icu_beds.total} color="#EF4444" label="ICU Beds" />
            <DonutRing used={RESOURCES.doctors.on_duty}   total={RESOURCES.doctors.total}   color="#6366F1" label="Doctors"  />
            <DonutRing used={RESOURCES.ot_rooms.in_use}   total={RESOURCES.ot_rooms.total}   color="#F59E0B" label="OT Rooms" />
          </div>
        </div>
      </div>

      {/* Patient cards */}
      <p style={{ margin:"0 0 12px", fontSize: 11, fontWeight: 700, color:"#9CA3AF",
        textTransform:"uppercase", letterSpacing:"0.06em" }}>Patient Records</p>
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(260px,1fr))", gap: 14 }}>
        {PATIENTS.map(p => {
          const s = rs(p.risk);
          return (
            <div key={p.id} onClick={() => onSelect(p)}
              style={{ background:"#fff", border:`1px solid ${s.border}`,
                borderLeft:`4px solid ${s.badge}`, borderRadius: 14, padding: 18,
                cursor:"pointer", transition:"transform 0.12s" }}
              onMouseEnter={e => e.currentTarget.style.transform = "translateY(-2px)"}
              onMouseLeave={e => e.currentTarget.style.transform = ""}
            >
              <div style={{ display:"flex", alignItems:"center", gap: 10, marginBottom: 12 }}>
                <Avatar name={p.name} />
                <div style={{ flex:1, minWidth:0 }}>
                  <p style={{ margin:0, fontWeight:700, fontSize:13, color:"#111827",
                    overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{p.name}</p>
                  <p style={{ margin:"1px 0 0", fontSize:11, color:"#9CA3AF" }}>Age {p.age} · {p.scan_date}</p>
                </div>
                <RiskBadge level={p.risk} />
              </div>
              <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap: 8 }}>
                <div style={{ background:"#F9FAFB", borderRadius:7, padding:"7px 10px" }}>
                  <p style={{ margin:"0 0 2px", fontSize:9, color:"#9CA3AF", fontWeight:700, textTransform:"uppercase" }}>Tumor</p>
                  <p style={{ margin:0, fontSize:12, fontWeight:700, color: p.tumor ? "#EF4444" : "#22C55E" }}>
                    {p.tumor ? "Detected" : "None"}
                  </p>
                </div>
                <div style={{ background:"#F9FAFB", borderRadius:7, padding:"7px 10px" }}>
                  <p style={{ margin:"0 0 2px", fontSize:9, color:"#9CA3AF", fontWeight:700, textTransform:"uppercase" }}>Confidence</p>
                  <p style={{ margin:0, fontSize:12, fontWeight:700, color:"#111827" }}>{(p.confidence*100).toFixed(1)}%</p>
                </div>
              </div>
              <div style={{ marginTop:10, paddingTop:10, borderTop:"1px solid #F3F4F6",
                display:"flex", justifyContent:"space-between" }}>
                <span style={{ fontSize:11, color:"#6B7280" }}>Urgency: <b style={{ color:"#111827" }}>{p.urgency}</b></span>
                <span style={{ fontSize:10, color:"#6366F1", fontWeight:700 }}>{p.id}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// PAGE 2 — MRI Upload
// ══════════════════════════════════════════════════════════════════
function MRIPage() {
  const [file, setFile]       = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState(null);
  const [dragging, setDragging] = useState(false);
  const [form, setForm]       = useState({ age:45, gender:"M", symptoms:"", history:"" });
  const fileRef               = useRef();

  const handleFile = (f) => {
    if (!f) return;
    setFile(f); setResult(null);
    const reader = new FileReader();
    reader.onload = e => setPreview(e.target.result);
    reader.readAsDataURL(f);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true); setResult(null);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("patient_age", form.age);
      fd.append("patient_gender", form.gender);
      fd.append("symptoms", form.symptoms);
      fd.append("medical_history", form.history);
      const res = await fetch(`${API}/upload-mri`, { method:"POST", body: fd });
      if (!res.ok) throw new Error();
      setResult(await res.json());
    } catch {
      await new Promise(r => setTimeout(r, 1600));
      setResult({
        scan_id:"SCAN-DEMO01", tumor_detected:true, confidence:0.914,
        risk_level:"High", risk_probability:0.873, urgency:"Immediate",
        doctor_type:"Neurosurgeon (Senior)",
        suggested_action:"Emergency neurosurgical assessment and ICU admission.",
        icu_bed_assigned:true, doctor_assigned:true, ot_room_assigned:true,
        resource_message:"ICU Bed 3 + DR-002 assigned.", _demo:true,
      });
    } finally { setLoading(false); }
  };

  const s = result ? rs(result.risk_level?.toLowerCase()) : null;

  return (
    <div>
      <div style={{ marginBottom: 20 }}>
        <h2 style={{ margin:"0 0 2px", fontSize:22, fontWeight:800, color:"#111827" }}>MRI Analysis</h2>
        <p style={{ margin:0, fontSize:13, color:"#6B7280" }}>Upload a scan for AI-powered tumor detection</p>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap: 20 }}>
        {/* Left — upload form */}
        <div>
          <div
            onDrop={e => { e.preventDefault(); setDragging(false); const f = e.dataTransfer.files[0]; if (f?.type.startsWith("image/")) handleFile(f); }}
            onDragOver={e => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onClick={() => fileRef.current.click()}
            style={{ border:`2px dashed ${dragging ? "#6366F1" : "#D1D5DB"}`, borderRadius:14,
              padding:28, textAlign:"center", cursor:"pointer",
              background: dragging ? "#EEF2FF" : "#FAFAFA", marginBottom:16,
              minHeight:180, display:"flex", flexDirection:"column",
              alignItems:"center", justifyContent:"center" }}
          >
            {preview
              ? <img src={preview} alt="preview"
                  style={{ maxHeight:200, maxWidth:"100%", borderRadius:8, objectFit:"contain" }} />
              : <>
                  <div style={{ width:48, height:48, borderRadius:"50%", background:"#EEF2FF",
                    margin:"0 auto 12px", display:"flex", alignItems:"center", justifyContent:"center" }}>
                    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6366F1" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12"/>
                    </svg>
                  </div>
                  <p style={{ margin:"0 0 4px", fontWeight:700, color:"#374151", fontSize:14 }}>Drop MRI image here</p>
                  <p style={{ margin:0, fontSize:12, color:"#9CA3AF" }}>or click to browse — JPEG, PNG</p>
                </>
            }
            <input ref={fileRef} type="file" accept="image/*" style={{ display:"none" }}
              onChange={e => handleFile(e.target.files[0])} />
          </div>

          <div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius:14, padding:18 }}>
            <p style={{ margin:"0 0 14px", fontWeight:700, fontSize:13, color:"#374151" }}>Patient information</p>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10, marginBottom:10 }}>
              <div>
                <label style={{ display:"block", fontSize:10, fontWeight:700, color:"#9CA3AF",
                  textTransform:"uppercase", marginBottom:5 }}>Age</label>
                <input type="number" value={form.age}
                  onChange={e => setForm({...form, age:e.target.value})}
                  style={{ width:"100%", border:"1px solid #E5E7EB", borderRadius:7,
                    padding:"7px 10px", fontSize:13, boxSizing:"border-box" }} />
              </div>
              <div>
                <label style={{ display:"block", fontSize:10, fontWeight:700, color:"#9CA3AF",
                  textTransform:"uppercase", marginBottom:5 }}>Gender</label>
                <select value={form.gender} onChange={e => setForm({...form, gender:e.target.value})}
                  style={{ width:"100%", border:"1px solid #E5E7EB", borderRadius:7,
                    padding:"7px 10px", fontSize:13, boxSizing:"border-box", background:"#fff" }}>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </div>
            <div style={{ marginBottom:10 }}>
              <label style={{ display:"block", fontSize:10, fontWeight:700, color:"#9CA3AF",
                textTransform:"uppercase", marginBottom:5 }}>Symptoms</label>
              <input value={form.symptoms} onChange={e => setForm({...form, symptoms:e.target.value})}
                placeholder="headache, nausea…"
                style={{ width:"100%", border:"1px solid #E5E7EB", borderRadius:7,
                  padding:"7px 10px", fontSize:13, boxSizing:"border-box" }} />
            </div>
            <div style={{ marginBottom:16 }}>
              <label style={{ display:"block", fontSize:10, fontWeight:700, color:"#9CA3AF",
                textTransform:"uppercase", marginBottom:5 }}>Medical history</label>
              <input value={form.history} onChange={e => setForm({...form, history:e.target.value})}
                placeholder="hypertension, diabetes…"
                style={{ width:"100%", border:"1px solid #E5E7EB", borderRadius:7,
                  padding:"7px 10px", fontSize:13, boxSizing:"border-box" }} />
            </div>
            <button onClick={handleSubmit} disabled={!file || loading}
              style={{ width:"100%", padding:"11px 0", borderRadius:9, border:"none",
                background: !file ? "#E5E7EB" : "#6366F1",
                color: !file ? "#9CA3AF" : "#fff",
                fontWeight:700, fontSize:14, cursor: !file ? "not-allowed" : "pointer" }}>
              {loading ? "Analyzing…" : "Run AI Analysis"}
            </button>
          </div>
        </div>

        {/* Right — result */}
        <div>
          {loading && (
            <div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius:14,
              padding:48, textAlign:"center" }}>
              <div style={{ width:44, height:44, border:"4px solid #EEF2FF",
                borderTop:"4px solid #6366F1", borderRadius:"50%",
                animation:"spin 0.8s linear infinite", margin:"0 auto 18px" }} />
              <p style={{ margin:"0 0 6px", fontWeight:700, color:"#374151" }}>Running CNN inference…</p>
              <p style={{ margin:0, fontSize:12, color:"#9CA3AF" }}>Preprocessing → Model → Risk Engine</p>
              <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
            </div>
          )}
          {!loading && !result && (
            <div style={{ background:"#F9FAFB", border:"2px dashed #E5E7EB", borderRadius:14,
              height:"100%", minHeight:300, display:"flex", flexDirection:"column",
              alignItems:"center", justifyContent:"center", gap:10 }}>
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#D1D5DB" strokeWidth="1.5">
                <path d="M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18"/>
              </svg>
              <p style={{ margin:0, color:"#9CA3AF", fontSize:13 }}>Analysis results appear here</p>
            </div>
          )}
          {result && !loading && (
            <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
              {result._demo && <AlertBanner message="Demo mode — API offline. Showing sample result." type="info" />}
              <div style={{ background:s.bg, border:`1px solid ${s.border}`, borderRadius:14, padding:20 }}>
                <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:16 }}>
                  <div>
                    <p style={{ margin:"0 0 3px", fontSize:10, fontWeight:700, color:"#6B7280", textTransform:"uppercase" }}>Scan ID</p>
                    <p style={{ margin:0, fontSize:13, color:"#374151" }}>{result.scan_id}</p>
                  </div>
                  <RiskBadge level={result.risk_level?.toLowerCase()} />
                </div>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:10 }}>
                  {[
                    { label:"Tumor",          value: result.tumor_detected ? "Detected" : "None",    color: result.tumor_detected ? "#EF4444" : "#22C55E" },
                    { label:"Confidence",     value:`${(result.confidence*100).toFixed(1)}%`,         color:"#111827" },
                    { label:"Risk Prob.",     value:`${(result.risk_probability*100).toFixed(1)}%`,   color: s.badge },
                    { label:"Urgency",        value: result.urgency,                                  color:"#111827" },
                  ].map(({ label, value, color }) => (
                    <div key={label} style={{ background:"rgba(255,255,255,0.75)", borderRadius:9, padding:"10px 14px" }}>
                      <p style={{ margin:"0 0 3px", fontSize:9, color:"#6B7280", fontWeight:700, textTransform:"uppercase" }}>{label}</p>
                      <p style={{ margin:0, fontSize:16, fontWeight:800, color }}>{value}</p>
                    </div>
                  ))}
                </div>
              </div>
              <div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius:14, padding:18 }}>
                <p style={{ margin:"0 0 12px", fontWeight:700, fontSize:13, color:"#374151" }}>Resource allocation</p>
                <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginBottom:10 }}>
                  {[
                    { label:"ICU Bed", ok: result.icu_bed_assigned },
                    { label:"Doctor",  ok: result.doctor_assigned },
                    { label:"OT Room", ok: result.ot_room_assigned },
                  ].map(({ label, ok }) => (
                    <div key={label} style={{ display:"flex", alignItems:"center", gap:6,
                      background: ok ? "#F0FDF4" : "#FEF2F2",
                      border:`1px solid ${ok ? "#86EFAC" : "#FCA5A5"}`, borderRadius:7, padding:"5px 12px" }}>
                      <div style={{ width:7, height:7, borderRadius:"50%", background: ok ? "#22C55E" : "#EF4444" }} />
                      <span style={{ fontSize:12, fontWeight:600, color: ok ? "#14532D" : "#991B1B" }}>{label}</span>
                    </div>
                  ))}
                </div>
                <p style={{ margin:0, fontSize:11, color:"#6B7280" }}>{result.resource_message}</p>
              </div>
              {/* Doctor Suggestion Card */}
<div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius:14, padding:18 }}>
  <p style={{ margin:"0 0 14px", fontWeight:700, fontSize:13, color:"#374151" }}>
    Doctor Suggestion
  </p>
  <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:12 }}>
    <div style={{ width:46, height:46, borderRadius:"50%", background:"#EEF2FF",
      display:"flex", alignItems:"center", justifyContent:"center",
      fontSize:14, fontWeight:800, color:"#6366F1", flexShrink:0 }}>
      {result.doctor_type?.split(" ").map(w => w[0]).join("").slice(0,2).toUpperCase()}
    </div>
    <div>
      <p style={{ margin:"0 0 2px", fontWeight:700, fontSize:14, color:"#111827" }}>
        {result.doctor_type}
      </p>
      <p style={{ margin:0, fontSize:12, color:"#22C55E", fontWeight:600 }}>
        ● Available · On Call
      </p>
    </div>
  </div>
  <div style={{ background:"#F9FAFB", borderRadius:9, padding:"10px 14px" }}>
    <div style={{ display:"flex", justifyContent:"space-between", marginBottom:6 }}>
      <span style={{ fontSize:11, color:"#6B7280" }}>Risk Level</span>
      <span style={{ fontSize:11, fontWeight:700, color: result.risk_level === "High" ? "#EF4444" : result.risk_level === "Medium" ? "#F59E0B" : "#22C55E" }}>
        {result.risk_level}
      </span>
    </div>
    <div style={{ display:"flex", justifyContent:"space-between", marginBottom:6 }}>
      <span style={{ fontSize:11, color:"#6B7280" }}>Estimated Wait</span>
      <span style={{ fontSize:11, fontWeight:700, color:"#111827" }}>
        {result.urgency === "Immediate" ? "30 minutes" : result.urgency === "Moderate" ? "4 hours" : "72 hours"}
      </span>
    </div>
    <div style={{ display:"flex", justifyContent:"space-between" }}>
      <span style={{ fontSize:11, color:"#6B7280" }}>Department</span>
      <span style={{ fontSize:11, fontWeight:700, color:"#111827" }}>Neurology</span>
    </div>
  </div>
</div>
              <div style={{ background:"#312E81", borderRadius:14, padding:18 }}>
                <p style={{ margin:"0 0 6px", fontSize:10, fontWeight:700, color:"#A5B4FC", textTransform:"uppercase" }}>Recommended Action</p>
                <p style={{ margin:"0 0 4px", fontSize:14, fontWeight:700, color:"#fff" }}>{result.suggested_action}</p>
                <p style={{ margin:0, fontSize:11, color:"#A5B4FC" }}>{result.doctor_type}</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// PAGE 3 — Decision Panel
// ══════════════════════════════════════════════════════════════════
function DecisionPage({ selectedPatient }) {
  const [active, setActive] = useState(selectedPatient || PATIENTS[0]);
  const d = DECISION;
  const s = rs(active?.risk || "low");
  const urgColor = { Immediate:"#EF4444", Moderate:"#F59E0B", Low:"#22C55E" };

  return (
    <div>
      <div style={{ marginBottom:20 }}>
        <h2 style={{ margin:"0 0 2px", fontSize:22, fontWeight:800, color:"#111827" }}>Decision Panel</h2>
        <p style={{ margin:0, fontSize:13, color:"#6B7280" }}>Clinical decision support — urgency, actions & routing</p>
      </div>
      <div style={{ display:"grid", gridTemplateColumns:"210px 1fr", gap:20 }}>
        {/* Sidebar */}
        <div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius:14, padding:14, alignSelf:"start" }}>
          <p style={{ margin:"0 0 10px", fontSize:10, fontWeight:700, color:"#9CA3AF",
            textTransform:"uppercase", letterSpacing:"0.05em" }}>Select Patient</p>
          {PATIENTS.map(p => {
            const ps = rs(p.risk); const isA = active?.id === p.id;
            return (
              <div key={p.id} onClick={() => setActive(p)}
                style={{ display:"flex", alignItems:"center", gap:8, padding:"8px 10px",
                  borderRadius:8, cursor:"pointer", marginBottom:4,
                  background: isA ? "#EEF2FF" : "transparent",
                  border: isA ? "1px solid #C7D2FE" : "1px solid transparent" }}>
                <div style={{ width:7, height:7, borderRadius:"50%", background:ps.badge, flexShrink:0 }} />
                <div style={{ minWidth:0 }}>
                  <p style={{ margin:0, fontSize:12, fontWeight:600, color:"#111827",
                    overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{p.name}</p>
                  <p style={{ margin:0, fontSize:10, color:"#9CA3AF" }}>{p.id}</p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Main content */}
        <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
          {active && (
            <div style={{ background:s.bg, border:`1px solid ${s.border}`, borderRadius:14,
              padding:20, display:"flex", alignItems:"center", gap:14 }}>
              <Avatar name={active.name} size={48} />
              <div style={{ flex:1 }}>
                <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:3 }}>
                  <h3 style={{ margin:0, fontSize:16, fontWeight:800, color:"#111827" }}>{active.name}</h3>
                  <RiskBadge level={active.risk} />
                </div>
                <p style={{ margin:0, fontSize:12, color:"#6B7280" }}>
                  Age {active.age} · {active.gender} · {active.id} · {active.scan_date}
                </p>
              </div>
              <div style={{ textAlign:"right" }}>
                <p style={{ margin:"0 0 2px", fontSize:10, color:"#9CA3AF", fontWeight:600 }}>CONFIDENCE</p>
                <p style={{ margin:0, fontSize:22, fontWeight:800, color:s.badge }}>{(active.confidence*100).toFixed(1)}%</p>
              </div>
            </div>
          )}

          <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14 }}>
            <div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius:14, padding:18 }}>
              <p style={{ margin:"0 0 5px", fontSize:10, fontWeight:700, color:"#9CA3AF", textTransform:"uppercase" }}>Urgency</p>
              <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:6 }}>
                <div style={{ width:10, height:10, borderRadius:"50%", background: urgColor[d.urgency] || "#9CA3AF" }} />
                <span style={{ fontSize:20, fontWeight:800, color: urgColor[d.urgency] || "#111827" }}>{d.urgency}</span>
              </div>
              <p style={{ margin:"0 0 8px", fontSize:11, color:"#6B7280" }}>Est. wait: {d.estimated_wait_hours}h</p>
              {d.alert_er && (
                <div style={{ background:"#FEF2F2", border:"1px solid #FCA5A5", borderRadius:6,
                  padding:"5px 10px", fontSize:11, color:"#991B1B", fontWeight:600 }}>ER Alert Active</div>
              )}
            </div>
            <div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius:14, padding:18 }}>
              <p style={{ margin:"0 0 5px", fontSize:10, fontWeight:700, color:"#9CA3AF", textTransform:"uppercase" }}>Specialist</p>
              <p style={{ margin:"0 0 6px", fontSize:14, fontWeight:800, color:"#111827" }}>{d.doctor_type}</p>
              <p style={{ margin:0, fontSize:11, color:"#22C55E", fontWeight:600 }}>Available · On call</p>
            </div>
          </div>

          <div style={{ background:"#1E1B4B", borderRadius:14, padding:20 }}>
            <p style={{ margin:"0 0 6px", fontSize:10, fontWeight:700, color:"#A5B4FC", textTransform:"uppercase" }}>Suggested Action</p>
            <p style={{ margin:0, fontSize:14, fontWeight:700, color:"#fff", lineHeight:1.5 }}>{d.suggested_action}</p>
          </div>

          <div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius:14, padding:20 }}>
            <p style={{ margin:"0 0 14px", fontWeight:700, fontSize:13, color:"#374151" }}>Clinical next steps</p>
            <ol style={{ margin:0, padding:0, listStyle:"none", display:"flex", flexDirection:"column", gap:9 }}>
              {d.next_steps.map((step, i) => (
                <li key={i} style={{ display:"flex", alignItems:"flex-start", gap:10 }}>
                  <span style={{ width:22, height:22, borderRadius:"50%", background:"#EEF2FF",
                    color:"#4338CA", fontSize:10, fontWeight:800, flexShrink:0,
                    display:"flex", alignItems:"center", justifyContent:"center" }}>{i+1}</span>
                  <span style={{ fontSize:13, color:"#374151", lineHeight:1.5, paddingTop:2 }}>{step}</span>
                </li>
              ))}
            </ol>
          </div>
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// PAGE 4 — Resource Monitor
// ══════════════════════════════════════════════════════════════════
function ResourcePage() {
  const [res, setRes]         = useState(RESOURCES);
  const [refreshing, setRef]  = useState(false);

  const refresh = async () => {
    setRef(true);
    try { const r = await fetch(`${API}/resources`); setRes(await r.json()); }
    catch {}
    finally { setRef(false); }
  };

  const beds = res.icu_beds, docs = res.doctors, ots = res.ot_rooms, q = res.waiting_queue;
  const bedPct = Math.round((beds.occupied / beds.total) * 100);
  const docPct = Math.round((docs.on_duty  / docs.total) * 100);
  const otPct  = Math.round((ots.in_use    / ots.total)  * 100);

  return (
    <div>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:20 }}>
        <div>
          <h2 style={{ margin:"0 0 2px", fontSize:22, fontWeight:800, color:"#111827" }}>Resource Monitor</h2>
          <p style={{ margin:0, fontSize:13, color:"#6B7280" }}>Live hospital capacity & allocation status</p>
        </div>
        <button onClick={refresh}
          style={{ display:"flex", alignItems:"center", gap:7, padding:"8px 16px",
            border:"1px solid #E5E7EB", borderRadius:9, background:"#fff",
            fontSize:13, fontWeight:600, color:"#374151", cursor:"pointer" }}>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            style={{ animation: refreshing ? "spin 0.8s linear infinite" : "none" }}>
            <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/>
          </svg>
          {refreshing ? "Refreshing…" : "Refresh"}
        </button>
      </div>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>

      {bedPct >= 70 && (
        <AlertBanner
          message={`ICU at ${bedPct}% capacity.${bedPct >= 90 ? " Activate surge protocol now." : " Monitor closely."}`}
          type={bedPct >= 90 ? "danger" : "warning"} />
      )}
      <div style={{ marginBottom:20 }} />

      {/* Resource cards */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:16, marginBottom:20 }}>
        {[
          { label:"ICU Beds", avail:beds.available, occ:beds.occupied, total:beds.total, pct:bedPct, color: bedPct>=90?"#EF4444":bedPct>=70?"#F59E0B":"#22C55E" },
          { label:"Doctors",  avail:docs.available, occ:docs.on_duty,  total:docs.total, pct:docPct, color:"#6366F1" },
          { label:"OT Rooms", avail:ots.available,  occ:ots.in_use,    total:ots.total,  pct:otPct,  color:"#F59E0B" },
        ].map(({ label, avail, occ, total, pct, color }) => (
          <div key={label} style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius:14, padding:20 }}>
            <p style={{ margin:"0 0 4px", fontSize:10, fontWeight:700, color:"#9CA3AF",
              textTransform:"uppercase", letterSpacing:"0.06em" }}>{label}</p>
            <p style={{ margin:"0 0 14px", fontSize:28, fontWeight:800, color:"#111827", lineHeight:1 }}>
              {avail} <span style={{ fontSize:13, fontWeight:400, color:"#9CA3AF" }}>free</span>
            </p>
            <ProgressBar pct={pct} color={color} />
            <div style={{ display:"flex", justifyContent:"space-between", marginTop:7, fontSize:11, color:"#6B7280" }}>
              <span>{occ} occupied</span><span>{total} total</span>
            </div>
          </div>
        ))}
      </div>

      {/* Bed grid */}
      <div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius:14, padding:20, marginBottom:16 }}>
        <p style={{ margin:"0 0 3px", fontWeight:700, fontSize:13, color:"#374151" }}>ICU Bed Grid</p>
        <p style={{ margin:"0 0 16px", fontSize:11, color:"#9CA3AF" }}>All {beds.total} beds — live status</p>
        <div style={{ display:"flex", flexWrap:"wrap", gap:8 }}>
          {Array.from({ length: beds.total }).map((_, i) => {
            const occ = i < beds.occupied;
            return (
              <div key={i} style={{ width:52, height:52, borderRadius:9,
                background: occ ? "#FEE2E2" : "#F0FDF4",
                border:`1px solid ${occ ? "#FCA5A5" : "#86EFAC"}`,
                display:"flex", flexDirection:"column", alignItems:"center",
                justifyContent:"center", gap:4 }}>
                <span style={{ fontSize:9, fontWeight:700, color: occ ? "#991B1B" : "#14532D" }}>
                  B{String(i+1).padStart(2,"0")}
                </span>
                <div style={{ width:7, height:7, borderRadius:"50%",
                  background: occ ? "#EF4444" : "#22C55E" }} />
              </div>
            );
          })}
        </div>
        <div style={{ display:"flex", gap:18, marginTop:14 }}>
          <div style={{ display:"flex", alignItems:"center", gap:5 }}>
            <div style={{ width:8, height:8, borderRadius:"50%", background:"#EF4444" }} />
            <span style={{ fontSize:11, color:"#6B7280" }}>Occupied ({beds.occupied})</span>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:5 }}>
            <div style={{ width:8, height:8, borderRadius:"50%", background:"#22C55E" }} />
            <span style={{ fontSize:11, color:"#6B7280" }}>Available ({beds.available})</span>
          </div>
        </div>
      </div>

      {/* Doctor roster */}
      <div style={{ background:"#fff", border:"1px solid #E5E7EB", borderRadius:14, padding:20 }}>
        <p style={{ margin:"0 0 14px", fontWeight:700, fontSize:13, color:"#374151" }}>Doctor roster</p>
        <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fill,minmax(190px,1fr))", gap:10 }}>
          {[
            { name:"Dr. Aiko Sato",      role:"Neurosurgeon",        status:"available" },
            { name:"Dr. Marco Ferretti", role:"Neurologist",         status:"assigned"  },
            { name:"Dr. Layla Hassan",   role:"Neurosurgeon",        status:"assigned"  },
            { name:"Dr. Chen Wei",       role:"Neurologist",         status:"assigned"  },
            { name:"Dr. Eva Müller",     role:"General Neurologist", status:"assigned"  },
          ].map(doc => (
            <div key={doc.name} style={{ display:"flex", alignItems:"center", gap:10,
              padding:"10px 14px",
              background: doc.status === "available" ? "#F0FDF4" : "#F9FAFB",
              border:`1px solid ${doc.status === "available" ? "#86EFAC" : "#E5E7EB"}`,
              borderRadius:10 }}>
              <Avatar name={doc.name} size={32} />
              <div style={{ flex:1, minWidth:0 }}>
                <p style={{ margin:0, fontSize:12, fontWeight:700, color:"#111827",
                  overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{doc.name}</p>
                <p style={{ margin:"1px 0 0", fontSize:10, color:"#6B7280" }}>{doc.role}</p>
              </div>
              <div style={{ width:7, height:7, borderRadius:"50%", flexShrink:0,
                background: doc.status === "available" ? "#22C55E" : "#EF4444" }} />
            </div>
          ))}
        </div>
      </div>

      {q.patients_waiting > 0 && (
        <div style={{ marginTop:16, background:"#FEF2F2", border:"1px solid #FCA5A5",
          borderRadius:14, padding:18 }}>
          <p style={{ margin:"0 0 6px", fontWeight:700, fontSize:13, color:"#991B1B" }}>
            Waiting Queue — {q.patients_waiting} patient(s)
          </p>
          <p style={{ margin:0, fontSize:12, color:"#991B1B" }}>
            Resource exhaustion detected. Activate surge capacity protocol immediately.
          </p>
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════════
// SIDEBAR NAV
// ══════════════════════════════════════════════════════════════════
const NAV = [
  { id:"dashboard", label:"Dashboard",    icon:"M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" },
  { id:"upload",    label:"MRI Analysis", icon:"M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" },
  { id:"decision",  label:"Decision",     icon:"M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" },
  { id:"resources", label:"Resources",    icon:"M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" },
];

// ══════════════════════════════════════════════════════════════════
// ROOT APP
// ══════════════════════════════════════════════════════════════════
export default function App() {
  const [page, setPage]             = useState("dashboard");
  const [selectedPatient, setSelP]  = useState(null);

  const goDecision = (p) => { setSelP(p); setPage("decision"); };

  return (
    <div style={{ display:"flex", minHeight:"100vh",
      fontFamily:"'DM Sans','Segoe UI',system-ui,sans-serif", background:"#F8FAFC" }}>

      {/* ── Sidebar ── */}
      <aside style={{ width:200, flexShrink:0, background:"#0F172A",
        display:"flex", flexDirection:"column", padding:"20px 0",
        position:"sticky", top:0, height:"100vh" }}>

        {/* Logo */}
        <div style={{ padding:"0 16px 24px" }}>
          <div style={{ display:"flex", alignItems:"center", gap:9 }}>
            <div style={{ width:34, height:34, borderRadius:9, background:"#6366F1",
              display:"flex", alignItems:"center", justifyContent:"center" }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.5">
                <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
              </svg>
            </div>
            <div>
              <p style={{ margin:0, fontSize:13, fontWeight:800, color:"#fff" }}>NeuroAI</p>
              <p style={{ margin:0, fontSize:9, color:"#64748B" }}>Healthcare System</p>
            </div>
          </div>
        </div>

        {/* Nav items */}
        <nav style={{ flex:1, padding:"0 10px", display:"flex", flexDirection:"column", gap:3 }}>
          {NAV.map(({ id, label, icon }) => {
            const active = page === id;
            return (
              <button key={id} onClick={() => setPage(id)}
                style={{ display:"flex", alignItems:"center", gap:10, padding:"9px 10px",
                  borderRadius:9, border:"none",
                  background: active ? "#6366F1" : "transparent",
                  color: active ? "#fff" : "#64748B",
                  cursor:"pointer", textAlign:"left", width:"100%",
                  fontSize:13, fontWeight: active ? 700 : 400,
                  transition:"background 0.12s, color 0.12s" }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                  stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d={icon} />
                </svg>
                {label}
              </button>
            );
          })}
        </nav>

        {/* Footer */}
        <div style={{ padding:"14px 16px", borderTop:"1px solid #1E293B" }}>
          <p style={{ margin:"0 0 4px", fontSize:10, color:"#64748B", fontWeight:600 }}>API Status</p>
          <div style={{ display:"flex", alignItems:"center", gap:5 }}>
            <div style={{ width:6, height:6, borderRadius:"50%", background:"#22C55E" }} />
            <span style={{ fontSize:10, color:"#475569" }}>localhost:8000</span>
          </div>
        </div>
      </aside>

      {/* ── Main content ── */}
      <main style={{ flex:1, padding:"32px 36px", overflowY:"auto" }}>
        {page === "dashboard" && <DashboardPage onSelect={goDecision} />}
        {page === "upload"    && <MRIPage />}
        {page === "decision"  && <DecisionPage selectedPatient={selectedPatient} />}
        {page === "resources" && <ResourcePage />}
      </main>
    </div>
  );
}