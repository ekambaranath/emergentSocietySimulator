import { create } from "zustand";

const BASE = window.location.hostname.includes("github.dev") ? `https://${window.location.hostname.replace("-5173", "-8000")}` : "http://localhost:8000";
const WS_BASE = BASE.replace("https://", "wss://").replace("http://", "ws://");
const API = BASE;
const WS  = `${WS_BASE}/ws`;

export const useSimStore = create((set, get) => ({
  // ── State ──
  tick:        0,
  running:     false,
  paused:      false,
  agents:      [],
  coalitions:  {},
  norms:       [],
  events:      [],
  metrics:     {},
  metricsHistory: [],
  selectedAgent:  null,
  wsConnected:    false,
  speed:          3.0,

  // ── WebSocket ──
  ws: null,

  connectWS: () => {
    const ws = new WebSocket(WS);
    ws.onopen    = () => set({ wsConnected: true });
    ws.onclose   = () => set({ wsConnected: false });
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "ping") return;
      set({
        tick:       data.tick,
        running:    data.running,
        paused:     data.paused,
        agents:     data.agents      || [],
        coalitions: data.coalitions  || {},
        norms:      data.norms       || [],
        events:     data.events      || [],
        metrics:    data.metrics     || {},
      });
      // Append metrics history
      if (data.metrics?.tick) {
        set((s) => ({
          metricsHistory: [
            ...s.metricsHistory.slice(-200),
            data.metrics,
          ],
        }));
      }
    };
    set({ ws });
  },

  disconnectWS: () => {
    get().ws?.close();
    set({ ws: null, wsConnected: false });
  },

  // ── Controls ──
  startSim:  () => fetch(`${API}/api/sim/start`,  { method: "POST" }),
  pauseSim:  () => fetch(`${API}/api/sim/pause`,  { method: "POST" }),
  resumeSim: () => fetch(`${API}/api/sim/resume`, { method: "POST" }),
  stopSim:   () => fetch(`${API}/api/sim/stop`,   { method: "POST" }),
  resetSim:  () => {
    fetch(`${API}/api/sim/reset`, { method: "POST" });
    set({ metricsHistory: [], events: [], tick: 0 });
  },

  setSpeed: (interval) => {
    fetch(`${API}/api/sim/speed`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ interval }),
    });
    set({ speed: interval });
  },

  // ── Agent Inspector ──
  selectAgent: async (agentId) => {
    if (!agentId) { set({ selectedAgent: null }); return; }
    const res  = await fetch(`${API}/api/agents/${agentId}`);
    const data = await res.json();
    set({ selectedAgent: data });
  },

  // ── Experiments ──
  runExperiment: (id, params = {}) =>
    fetch(`${API}/api/experiments/run`, {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ experiment: id, params }),
    }),
}));
