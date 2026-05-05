import { useState, useEffect } from "react";
import axios from "axios";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import "leaflet/dist/leaflet.css";

const API = "https://disaster-lens-api.onrender.com/api";

const CATEGORY_COLORS = {
  "Wildfires": "#e05c2a",
  "Sea and Lake Ice": "#4a9eda",
  "Severe Storms": "#8b5cf6",
  "Volcanoes": "#ef4444",
  "Earthquakes": "#f59e0b",
  "Floods": "#06b6d4",
  "Landslides": "#84cc16",
  "Drought": "#d97706",
};

const categoryColor = (cat) => CATEGORY_COLORS[cat] || "#888";

export default function App() {
  const [events, setEvents] = useState([]);
  const [forgotten, setForgotten] = useState([]);
  const [stats, setStats] = useState(null);
  const [categories, setCategories] = useState([]);
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [activeTab, setActiveTab] = useState("map");

  useEffect(() => {
    axios.get(`${API}/events`).then(r => setEvents(r.data));
    axios.get(`${API}/events/forgotten?limit=20`).then(r => setForgotten(r.data));
    axios.get(`${API}/stats`).then(r => setStats(r.data));
    axios.get(`${API}/categories`).then(r => setCategories(r.data));
  }, []);

  const selectEvent = (ev) => {
    setSelected(ev);
    axios.get(`${API}/events/${ev.id}`).then(r => setDetail(r.data));
  };

  return (
    <div style={{ fontFamily: "system-ui, sans-serif", minHeight: "100vh", background: "#0f1117", color: "#e2e8f0" }}>

      {/* Header */}
      <div style={{ background: "#1a1d27", borderBottom: "1px solid #2d3148", padding: "1rem 2rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: "1.3rem", fontWeight: 600, color: "#fff" }}>
            DisasterLens
          </h1>
          <p style={{ margin: 0, fontSize: "0.75rem", color: "#94a3b8" }}>NASA EONET × News Media Coverage Gap</p>
        </div>
        {stats && (
          <div style={{ display: "flex", gap: "2rem" }}>
            {[
              { label: "Events tracked", value: stats.total_events },
              { label: "Articles found", value: stats.total_articles },
              { label: "Forgotten", value: stats.forgotten_events, color: "#f87171" },
              { label: "Covered", value: stats.covered_events, color: "#4ade80" },
            ].map(s => (
              <div key={s.label} style={{ textAlign: "center" }}>
                <div style={{ fontSize: "1.4rem", fontWeight: 700, color: s.color || "#fff" }}>{s.value}</div>
                <div style={{ fontSize: "0.7rem", color: "#94a3b8" }}>{s.label}</div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 0, background: "#1a1d27", borderBottom: "1px solid #2d3148", padding: "0 2rem" }}>
        {["map", "forgotten", "chart"].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            background: "none", border: "none", borderBottom: activeTab === tab ? "2px solid #6366f1" : "2px solid transparent",
            color: activeTab === tab ? "#fff" : "#94a3b8", padding: "0.75rem 1.25rem", cursor: "pointer",
            fontSize: "0.85rem", fontWeight: activeTab === tab ? 600 : 400, textTransform: "capitalize"
          }}>
            {tab === "map" ? "Event Map" : tab === "forgotten" ? "Forgotten Disasters" : "Coverage Chart"}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={{ display: "flex", height: "calc(100vh - 120px)" }}>

        {/* Main panel */}
        <div style={{ flex: 1, overflow: "hidden", position: "relative" }}>

          {activeTab === "map" && (
            <MapContainer center={[39.5, -98.35]} zoom={4} style={{ height: "100%", width: "100%", background: "#0f1117" }}>
              <TileLayer
                url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
                attribution='&copy; OpenStreetMap &copy; CARTO'
              />
              {events.filter(e => e.latitude && e.longitude).map(ev => (
                <CircleMarker
                  key={ev.id}
                  center={[ev.latitude, ev.longitude]}
                  radius={ev.coverage_score > 0 ? 7 : 5}
                  pathOptions={{
                    color: ev.coverage_score > 0 ? "#4ade80" : "#f87171",
                    fillColor: ev.coverage_score > 0 ? "#4ade80" : "#f87171",
                    fillOpacity: 0.8,
                    weight: 1,
                  }}
                  eventHandlers={{ click: () => selectEvent(ev) }}
                >
                  <Popup>
                    <div style={{ minWidth: 180 }}>
                      <strong>{ev.title}</strong><br />
                      <span style={{ color: categoryColor(ev.category) }}>{ev.category}</span><br />
                      Articles: {ev.article_count} | Score: {ev.coverage_score.toFixed(2)}
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          )}

          {activeTab === "forgotten" && (
            <div style={{ padding: "1.5rem", overflowY: "auto", height: "100%" }}>
              <p style={{ color: "#94a3b8", fontSize: "0.85rem", marginBottom: "1rem" }}>
                These {forgotten.length} events were tracked by NASA satellites but received little to no news coverage.
              </p>
              {forgotten.map((ev, i) => (
                <div key={ev.id} onClick={() => { selectEvent(ev); setActiveTab("map"); }}
                  style={{
                    background: "#1a1d27", border: "1px solid #2d3148", borderRadius: 8,
                    padding: "0.9rem 1rem", marginBottom: "0.6rem", cursor: "pointer",
                    borderLeft: `3px solid ${categoryColor(ev.category)}`,
                    transition: "border-color 0.15s"
                  }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                    <div>
                      <div style={{ fontWeight: 500, fontSize: "0.9rem", marginBottom: 3 }}>
                        #{i + 1} {ev.title}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "#94a3b8" }}>
                        {ev.category} · {ev.event_date ? new Date(ev.event_date).toLocaleDateString() : "Unknown date"}
                      </div>
                    </div>
                    <div style={{ textAlign: "right", flexShrink: 0, marginLeft: "1rem" }}>
                      <div style={{ fontSize: "1rem", fontWeight: 700, color: ev.article_count === 0 ? "#f87171" : "#fbbf24" }}>
                        {ev.article_count} articles
                      </div>
                      <div style={{ fontSize: "0.7rem", color: "#64748b" }}>coverage score: {ev.coverage_score.toFixed(3)}</div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {activeTab === "chart" && (
            <div style={{ padding: "2rem", height: "100%", overflowY: "auto" }}>
              <h3 style={{ marginTop: 0, color: "#cbd5e1" }}>Events by category</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={categories}>
                  <XAxis dataKey="category" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: "#1a1d27", border: "1px solid #2d3148", borderRadius: 6 }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {categories.map((c, i) => <Cell key={i} fill={categoryColor(c.category)} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>

              <h3 style={{ color: "#cbd5e1", marginTop: "2rem" }}>Coverage score distribution</h3>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={[
                  { label: "No coverage", count: stats?.forgotten_events || 0 },
                  { label: "Some coverage", count: stats?.covered_events || 0 },
                ]}>
                  <XAxis dataKey="label" tick={{ fill: "#94a3b8", fontSize: 12 }} />
                  <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} />
                  <Tooltip contentStyle={{ background: "#1a1d27", border: "1px solid #2d3148", borderRadius: 6 }} />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    <Cell fill="#f87171" />
                    <Cell fill="#4ade80" />
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>

        {/* Side panel — event detail */}
        {selected && (
          <div style={{
            width: 300, background: "#1a1d27", borderLeft: "1px solid #2d3148",
            padding: "1.25rem", overflowY: "auto", flexShrink: 0
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "1rem" }}>
              <h3 style={{ margin: 0, fontSize: "0.9rem", lineHeight: 1.4 }}>{selected.title}</h3>
              <button onClick={() => { setSelected(null); setDetail(null); }}
                style={{ background: "none", border: "none", color: "#64748b", cursor: "pointer", fontSize: "1.1rem", padding: 0 }}>✕</button>
            </div>

            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", marginBottom: "1rem" }}>
              {[
                { label: selected.category, color: categoryColor(selected.category) },
                { label: selected.status, color: selected.status === "open" ? "#4ade80" : "#94a3b8" },
              ].map(b => (
                <span key={b.label} style={{
                  fontSize: "0.7rem", padding: "2px 8px", borderRadius: 20,
                  background: b.color + "22", color: b.color, border: `1px solid ${b.color}44`
                }}>{b.label}</span>
              ))}
            </div>

            <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginBottom: "1rem", lineHeight: 1.6 }}>
              <div>Date: {selected.event_date ? new Date(selected.event_date).toLocaleString() : "—"}</div>
              <div>Lat: {selected.latitude?.toFixed(4)}, Lon: {selected.longitude?.toFixed(4)}</div>
              <div style={{ marginTop: "0.5rem", fontSize: "1rem", fontWeight: 600, color: selected.article_count === 0 ? "#f87171" : "#4ade80" }}>
                {selected.article_count} news articles found
              </div>
              <div>Coverage score: {selected.coverage_score?.toFixed(3)}</div>
            </div>

            {detail?.articles?.length > 0 ? (
              <div>
                <div style={{ fontSize: "0.75rem", fontWeight: 600, color: "#64748b", marginBottom: "0.5rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>Related articles</div>
                {detail.articles.map((a, i) => (
                  <a key={i} href={a.url} target="_blank" rel="noreferrer" style={{
                    display: "block", background: "#0f1117", borderRadius: 6, padding: "0.6rem 0.75rem",
                    marginBottom: "0.5rem", textDecoration: "none", border: "1px solid #2d3148"
                  }}>
                    <div style={{ fontSize: "0.78rem", color: "#e2e8f0", lineHeight: 1.4, marginBottom: 3 }}>{a.title}</div>
                    <div style={{ fontSize: "0.7rem", color: "#6366f1" }}>{a.source}</div>
                  </a>
                ))}
              </div>
            ) : (
              <div style={{
                background: "#f8717122", border: "1px solid #f8717144", borderRadius: 6,
                padding: "0.75rem", fontSize: "0.8rem", color: "#f87171", textAlign: "center"
              }}>
                No news coverage found for this event.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}