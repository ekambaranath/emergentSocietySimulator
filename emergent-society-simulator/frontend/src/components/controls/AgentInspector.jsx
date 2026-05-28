import { useSimStore } from "../../store/simStore";

export default function AgentInspector() {
  const { selectedAgent, selectAgent } = useSimStore();

  if (!selectedAgent) return null;

  const a = selectedAgent;
  const ValueBar = ({ label, value, color }) => (
    <div className="flex items-center gap-2 text-xs">
      <span className="text-gray-500 w-20 shrink-0">{label}</span>
      <div className="flex-1 h-1.5 bg-gray-700 rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${value * 100}%`, background: color }} />
      </div>
      <span className="text-gray-300 font-mono w-7 text-right">{(value * 100).toFixed(0)}</span>
    </div>
  );

  return (
    <div className="bg-gray-800 rounded-xl p-4 border border-blue-800">
      <div className="flex items-center justify-between mb-3">
        <div>
          <h2 className="text-sm font-bold text-white">{a.name}</h2>
          <p className="text-xs text-gray-500">Gen {a.generation} · {a.social?.strategy}</p>
        </div>
        <button
          onClick={() => selectAgent(null)}
          className="text-gray-600 hover:text-white text-lg leading-none"
        >×</button>
      </div>

      {/* Resources */}
      <div className="grid grid-cols-3 gap-2 mb-3">
        {[
          { label: "Wealth",    value: a.resources?.wealth,    color: "#f59e0b", fmt: (v) => Math.round(v) },
          { label: "Knowledge", value: a.resources?.knowledge, color: "#3b82f6", fmt: (v) => v.toFixed(1) },
          { label: "Influence", value: a.resources?.influence, color: "#8b5cf6", fmt: (v) => v.toFixed(1) },
        ].map(({ label, value, color, fmt }) => (
          <div key={label} className="bg-gray-700 rounded-lg p-2 text-center">
            <div className="text-xs text-gray-400">{label}</div>
            <div className="text-sm font-bold" style={{ color }}>{fmt(value ?? 0)}</div>
          </div>
        ))}
      </div>

      {/* Values */}
      <div className="flex flex-col gap-1.5 mb-3">
        <ValueBar label="Cooperation"  value={a.values?.cooperation  ?? 0} color="#10b981" />
        <ValueBar label="Deception"    value={a.values?.deception    ?? 0} color="#ef4444" />
        <ValueBar label="Time Horizon" value={a.values?.time_horizon ?? 0} color="#3b82f6" />
        <ValueBar label="Risk"         value={a.values?.risk_appetite?? 0} color="#f97316" />
        <ValueBar label="Collectivism" value={a.values?.collectivism ?? 0} color="#8b5cf6" />
      </div>

      {/* Alignment */}
      <div className="bg-gray-700 rounded-lg p-2 mb-3 flex items-center justify-between">
        <span className="text-xs text-gray-400">Alignment Score</span>
        <span className={`text-sm font-bold ${
          (a.alignment?.score ?? 0.5) > 0.6 ? "text-emerald-400" :
          (a.alignment?.score ?? 0.5) > 0.3 ? "text-amber-400" : "text-red-400"
        }`}>
          {((a.alignment?.score ?? 0.5) * 100).toFixed(0)}%
        </span>
        {(a.alignment?.drift ?? 0) > 0.2 && (
          <span className="text-xs text-amber-400">⚠️ drift {((a.alignment?.drift ?? 0) * 100).toFixed(0)}%</span>
        )}
      </div>

      {/* Social */}
      <div className="flex gap-3 text-xs text-gray-500 mb-3">
        <span>🤝 {a.social?.allies ?? 0} allies</span>
        <span>⚔️ {a.social?.enemies ?? 0} enemies</span>
        <span>🛡️ {a.social?.coalitions ?? 0} coalitions</span>
      </div>

      {/* Memory */}
      {a.memory?.episodes?.length > 0 && (
        <div>
          <p className="text-xs text-gray-500 mb-1.5">Recent Memory</p>
          <div className="flex flex-col gap-1 max-h-28 overflow-y-auto">
            {[...a.memory.episodes].reverse().map((ep, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="text-gray-600 font-mono w-6">{ep.tick}</span>
                <span className={`
                  ${ep.outcome === "success"  ? "text-emerald-400" :
                    ep.outcome === "betrayal" ? "text-red-400"     :
                    ep.outcome === "caught"   ? "text-amber-400"   : "text-gray-400"}
                `}>
                  {ep.type} → {ep.outcome}
                </span>
                <span className={`ml-auto font-mono ${ep.delta >= 0 ? "text-emerald-500" : "text-red-500"}`}>
                  {ep.delta >= 0 ? "+" : ""}{ep.delta?.toFixed(1)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
