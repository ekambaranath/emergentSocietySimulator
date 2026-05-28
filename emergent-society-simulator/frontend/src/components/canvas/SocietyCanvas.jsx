import { useEffect, useRef, useState } from "react";
import { useSimStore } from "../../store/simStore";

const AGENT_RADIUS = 8;

function agentColor(agent) {
  const coop = agent.values?.cooperation ?? 0.5;
  const dec  = agent.values?.deception   ?? 0.2;
  if (dec > 0.6)  return "#ef4444";   // red — deceptive
  if (coop > 0.7) return "#10b981";   // emerald — cooperative
  if (coop > 0.5) return "#3b82f6";   // blue — moderate
  if (coop < 0.3) return "#f59e0b";   // amber — competitive
  return "#8b5cf6";                   // purple — opportunistic
}

function strategyIcon(strategy) {
  const icons = {
    cooperative:   "🤝",
    competitive:   "⚔️",
    deceptive:     "🎭",
    isolationist:  "🏔️",
    coalition:     "🛡️",
    opportunistic: "🎲",
  };
  return icons[strategy] || "❓";
}

export default function SocietyCanvas() {
  const canvasRef   = useRef(null);
  const { agents, coalitions, events, selectAgent } = useSimStore();
  const [positions, setPositions] = useState({});
  const [hovered,   setHovered]   = useState(null);

  // Assign stable positions to agents
  useEffect(() => {
    setPositions((prev) => {
      const next = { ...prev };
      agents.forEach((a) => {
        if (!next[a.id]) {
          next[a.id] = {
            x: 80 + Math.random() * (800 - 160),
            y: 60 + Math.random() * (500 - 120),
            vx: (Math.random() - 0.5) * 0.3,
            vy: (Math.random() - 0.5) * 0.3,
          };
        }
      });
      // Remove dead agents
      Object.keys(next).forEach((id) => {
        if (!agents.find((a) => a.id === id)) delete next[id];
      });
      return next;
    });
  }, [agents]);

  // Gentle drift animation
  useEffect(() => {
    const interval = setInterval(() => {
      setPositions((prev) => {
        const next = {};
        Object.entries(prev).forEach(([id, pos]) => {
          let { x, y, vx, vy } = pos;
          x  += vx; y += vy;
          vx += (Math.random() - 0.5) * 0.05;
          vy += (Math.random() - 0.5) * 0.05;
          vx  = Math.max(-0.5, Math.min(0.5, vx));
          vy  = Math.max(-0.5, Math.min(0.5, vy));
          x   = Math.max(20, Math.min(860, x));
          y   = Math.max(20, Math.min(540, y));
          next[id] = { x, y, vx, vy };
        });
        return next;
      });
    }, 80);
    return () => clearInterval(interval);
  }, []);

  const handleClick = (e) => {
    const rect   = e.currentTarget.getBoundingClientRect();
    const mx     = e.clientX - rect.left;
    const my     = e.clientY - rect.top;
    const scaleX = 880 / rect.width;
    const scaleY = 560 / rect.height;
    const wx = mx * scaleX;
    const wy = my * scaleY;

    for (const agent of agents) {
      const pos = positions[agent.id];
      if (!pos) continue;
      const dx = pos.x - wx;
      const dy = pos.y - wy;
      if (Math.sqrt(dx*dx + dy*dy) <= AGENT_RADIUS + 4) {
        selectAgent(agent.id);
        return;
      }
    }
    selectAgent(null);
  };

  const handleMouseMove = (e) => {
    const rect   = e.currentTarget.getBoundingClientRect();
    const mx     = e.clientX - rect.left;
    const my     = e.clientY - rect.top;
    const scaleX = 880 / rect.width;
    const scaleY = 560 / rect.height;
    const wx = mx * scaleX;
    const wy = my * scaleY;

    for (const agent of agents) {
      const pos = positions[agent.id];
      if (!pos) continue;
      const dx = pos.x - wx;
      const dy = pos.y - wy;
      if (Math.sqrt(dx*dx + dy*dy) <= AGENT_RADIUS + 6) {
        setHovered(agent);
        return;
      }
    }
    setHovered(null);
  };

  // Build alliance lines from coalitions
  const allianceLines = [];
  Object.values(coalitions).forEach((members) => {
    for (let i = 0; i < members.length - 1; i++) {
      const a = positions[members[i]];
      const b = positions[members[i + 1]];
      if (a && b) {
        allianceLines.push({ x1: a.x, y1: a.y, x2: b.x, y2: b.y });
      }
    }
  });

  return (
    <div className="flex-1 relative bg-gray-950 overflow-hidden">
      <svg
        viewBox="0 0 880 560"
        className="w-full h-full cursor-crosshair"
        onClick={handleClick}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHovered(null)}
      >
        {/* Grid */}
        <defs>
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#1f2937" strokeWidth="0.5" />
          </pattern>
        </defs>
        <rect width="880" height="560" fill="url(#grid)" />

        {/* Alliance lines */}
        {allianceLines.map((l, i) => (
          <line
            key={i}
            x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2}
            stroke="#3b82f6" strokeWidth="1" strokeOpacity="0.3"
            strokeDasharray="4 4"
          />
        ))}

        {/* Agents */}
        {agents.map((agent) => {
          const pos = positions[agent.id];
          if (!pos) return null;
          const color   = agentColor(agent);
          const isHover = hovered?.id === agent.id;
          const wealth  = agent.resources?.wealth ?? 100;
          const r = Math.max(5, Math.min(14, AGENT_RADIUS + wealth / 200));

          return (
            <g key={agent.id} transform={`translate(${pos.x},${pos.y})`}>
              {/* Glow for cooperative agents */}
              {agent.values?.cooperation > 0.7 && (
                <circle r={r + 4} fill={color} opacity="0.15" />
              )}
              <circle
                r={r}
                fill={color}
                stroke={isHover ? "#fff" : "rgba(255,255,255,0.2)"}
                strokeWidth={isHover ? 2 : 1}
              />
              {/* Alignment drift indicator */}
              {agent.alignment?.drift > 0.3 && (
                <circle r={r + 2} fill="none" stroke="#f59e0b" strokeWidth="1.5" strokeDasharray="3 2" />
              )}
            </g>
          );
        })}

        {/* Hover tooltip */}
        {hovered && positions[hovered.id] && (() => {
          const pos = positions[hovered.id];
          const tx  = pos.x + 14;
          const ty  = pos.y - 10;
          return (
            <g transform={`translate(${tx},${ty})`}>
              <rect x={0} y={0} width={160} height={72} rx={6}
                fill="#1f2937" stroke="#374151" strokeWidth={1} />
              <text x={8} y={16} fill="white" fontSize={11} fontWeight="bold">{hovered.name}</text>
              <text x={8} y={30} fill="#9ca3af" fontSize={9}>
                {strategyIcon(hovered.social?.strategy)} {hovered.social?.strategy}
              </text>
              <text x={8} y={44} fill="#9ca3af" fontSize={9}>
                💰 {Math.round(hovered.resources?.wealth ?? 0)} wealth
              </text>
              <text x={8} y={58} fill="#9ca3af" fontSize={9}>
                🤝 {((hovered.values?.cooperation ?? 0.5) * 100).toFixed(0)}% coop |
                🎭 {((hovered.values?.deception ?? 0) * 100).toFixed(0)}% dec
              </text>
              <text x={8} y={70} fill="#6b7280" fontSize={8}>Click to inspect</text>
            </g>
          );
        })()}
      </svg>

      {/* Legend */}
      <div className="absolute bottom-3 left-3 flex items-center gap-3 bg-gray-900/80 rounded-lg px-3 py-2 text-xs">
        {[
          { color: "#10b981", label: "Cooperative" },
          { color: "#3b82f6", label: "Moderate" },
          { color: "#f59e0b", label: "Competitive" },
          { color: "#ef4444", label: "Deceptive" },
          { color: "#8b5cf6", label: "Opportunistic" },
        ].map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ background: color }} />
            <span className="text-gray-400">{label}</span>
          </div>
        ))}
      </div>

      {/* Agent count overlay */}
      <div className="absolute top-3 left-3 bg-gray-900/80 rounded-lg px-3 py-1.5 text-xs text-gray-400">
        {agents.length} active agents
      </div>
    </div>
  );
}
