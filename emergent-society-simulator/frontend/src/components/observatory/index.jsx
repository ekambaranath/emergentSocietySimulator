// ── GiniChart ──────────────────────────────────────────────────────────────
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from "recharts";
import { useSimStore } from "../../store/simStore";

export function GiniChart() {
  const { metricsHistory } = useSimStore();
  const data = metricsHistory.map((m) => ({
    tick: m.tick,
    gini: m.wealth?.gini ?? 0,
  }));

  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
        Wealth Inequality (Gini)
      </h2>
      <ResponsiveContainer width="100%" height={80}>
        <LineChart data={data}>
          <XAxis dataKey="tick" hide />
          <YAxis domain={[0, 1]} hide />
          <Tooltip
            contentStyle={{ background: "#1f2937", border: "none", fontSize: 11 }}
            formatter={(v) => [v.toFixed(3), "Gini"]}
          />
          <ReferenceLine y={0.5} stroke="#ef4444" strokeDasharray="3 3" strokeOpacity={0.5} />
          <Line
            type="monotone" dataKey="gini"
            stroke="#f59e0b" strokeWidth={2} dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
      <div className="flex justify-between text-xs text-gray-500 mt-1">
        <span>0 = Equal</span>
        <span className="text-amber-400 font-mono">
          {data.at(-1)?.gini?.toFixed(3) ?? "—"}
        </span>
        <span>1 = Unequal</span>
      </div>
    </div>
  );
}

// ── CooperationGauge ────────────────────────────────────────────────────────
export function CooperationGauge() {
  const { metrics, metricsHistory } = useSimStore();
  const coop = metrics?.cooperation_mean ?? 0.5;
  const dec  = metrics?.deception_mean  ?? 0.2;

  const data = metricsHistory.slice(-40).map((m) => ({
    tick: m.tick,
    coop: m.cooperation_mean ?? 0,
    dec:  m.deception_mean   ?? 0,
  }));

  const pct   = Math.round(coop * 100);
  const color = coop > 0.6 ? "#10b981" : coop > 0.4 ? "#f59e0b" : "#ef4444";

  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
        Cooperation vs Deception
      </h2>
      <div className="flex items-center gap-4 mb-3">
        <div className="flex flex-col items-center">
          <span className="text-2xl font-bold" style={{ color }}>{pct}%</span>
          <span className="text-xs text-gray-500">cooperative</span>
        </div>
        <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${pct}%`, background: color }}
          />
        </div>
        <div className="flex flex-col items-center">
          <span className="text-lg font-bold text-red-400">{Math.round(dec * 100)}%</span>
          <span className="text-xs text-gray-500">deceptive</span>
        </div>
      </div>
      <ResponsiveContainer width="100%" height={50}>
        <LineChart data={data}>
          <Line type="monotone" dataKey="coop" stroke="#10b981" strokeWidth={1.5} dot={false} />
          <Line type="monotone" dataKey="dec"  stroke="#ef4444" strokeWidth={1.5} dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

// ── AlignmentHeatmap ────────────────────────────────────────────────────────
export function AlignmentHeatmap() {
  const { agents } = useSimStore();

  const buckets = Array(10).fill(0);
  agents.forEach((a) => {
    const score = a.alignment?.score ?? 0.5;
    const idx   = Math.min(9, Math.floor(score * 10));
    buckets[idx]++;
  });
  const max = Math.max(...buckets, 1);

  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
        Alignment Distribution
      </h2>
      <div className="flex items-end gap-1 h-16">
        {buckets.map((count, i) => {
          const pct   = count / max;
          const score = i / 10;
          const color = score > 0.6 ? "#10b981" : score > 0.3 ? "#f59e0b" : "#ef4444";
          return (
            <div key={i} className="flex-1 flex flex-col items-center gap-1">
              <div
                className="w-full rounded-t-sm transition-all duration-300"
                style={{ height: `${Math.max(2, pct * 56)}px`, background: color, opacity: 0.8 }}
                title={`Score ${(score * 100).toFixed(0)}-${((score + 0.1) * 100).toFixed(0)}%: ${count} agents`}
              />
            </div>
          );
        })}
      </div>
      <div className="flex justify-between text-xs text-gray-600 mt-1">
        <span>Misaligned</span>
        <span className="text-white font-mono">
          avg {((agents.reduce((s, a) => s + (a.alignment?.score ?? 0.5), 0) / Math.max(1, agents.length)) * 100).toFixed(0)}%
        </span>
        <span>Aligned</span>
      </div>
    </div>
  );
}

// ── EventFeed ───────────────────────────────────────────────────────────────
export function EventFeed() {
  const { events } = useSimStore();
  const recent = [...events].reverse().slice(0, 15);

  const typeColor = {
    trade:              "text-blue-400",
    cooperate:          "text-emerald-400",
    defect:             "text-red-400",
    alliance_formed:    "text-purple-400",
    deception:          "text-orange-400",
    deception_caught:   "text-yellow-400",
    norm_emerged:       "text-cyan-400",
    experiment_start:   "text-pink-400",
    power_concentration:"text-amber-400",
    ostracism:          "text-rose-400",
    knowledge_shared:   "text-teal-400",
    generational_turnover: "text-indigo-400",
  };

  return (
    <div className="bg-gray-800 rounded-xl p-4 flex-1">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
        Event Feed
      </h2>
      <div className="flex flex-col gap-1.5 overflow-y-auto max-h-48">
        {recent.length === 0 && (
          <p className="text-gray-600 text-xs">No events yet. Start the simulation.</p>
        )}
        {recent.map((e, i) => (
          <div key={i} className="flex items-start gap-2">
            <span className="text-gray-600 font-mono text-xs min-w-[28px]">
              {e.tick}
            </span>
            <span className={`text-xs leading-snug ${typeColor[e.type] || "text-gray-400"}`}>
              {e.description}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── StabilityMeter ──────────────────────────────────────────────────────────
export function StabilityMeter() {
  const { metrics, norms, agents } = useSimStore();

  const gini      = metrics?.wealth?.gini         ?? 0;
  const coop      = metrics?.cooperation_mean      ?? 0.5;
  const alignment = metrics?.alignment?.mean        ?? 0.5;
  const defectionRate = 1 - coop;

  const stability = Math.max(0, Math.min(1,
    coop * 0.35 + alignment * 0.35 + (1 - gini) * 0.20 + (norms.length > 0 ? 0.10 : 0)
  ));

  const label =
    stability > 0.75 ? "Stable"     :
    stability > 0.50 ? "Fragile"    :
    stability > 0.25 ? "Unstable"   : "Collapsing";

  const color =
    stability > 0.75 ? "#10b981" :
    stability > 0.50 ? "#f59e0b" :
    stability > 0.25 ? "#f97316" : "#ef4444";

  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
        Society Stability
      </h2>
      <div className="flex items-center gap-3 mb-3">
        <div className="relative w-14 h-14">
          <svg viewBox="0 0 56 56" className="w-full h-full -rotate-90">
            <circle cx="28" cy="28" r="22" fill="none" stroke="#374151" strokeWidth="5" />
            <circle
              cx="28" cy="28" r="22" fill="none"
              stroke={color} strokeWidth="5"
              strokeDasharray={`${stability * 138} 138`}
              strokeLinecap="round"
              style={{ transition: "stroke-dasharray 0.5s" }}
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-xs font-bold" style={{ color }}>
              {Math.round(stability * 100)}
            </span>
          </div>
        </div>
        <div>
          <div className="text-base font-bold" style={{ color }}>{label}</div>
          <div className="text-xs text-gray-500 mt-0.5">
            {norms.length} active norm{norms.length !== 1 ? "s" : ""}
          </div>
        </div>
      </div>
      <div className="flex flex-col gap-1">
        {[
          { label: "Cooperation", value: coop,      color: "#10b981" },
          { label: "Alignment",   value: alignment,  color: "#3b82f6" },
          { label: "Equality",    value: 1 - gini,  color: "#8b5cf6" },
        ].map(({ label, value, color }) => (
          <div key={label} className="flex items-center gap-2 text-xs">
            <span className="text-gray-500 w-20">{label}</span>
            <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${value * 100}%`, background: color }}
              />
            </div>
            <span className="text-gray-400 w-8 text-right font-mono">
              {(value * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
