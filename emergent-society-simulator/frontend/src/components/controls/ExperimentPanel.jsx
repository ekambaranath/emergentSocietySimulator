import { useState } from "react";
import { useSimStore } from "../../store/simStore";

const EXPERIMENTS = [
  {
    id:    "scarcity_shock",
    name:  "Scarcity Shock",
    icon:  "⚡",
    desc:  "Drop world resources 70%. Watch cooperation vs defection.",
    color: "amber",
    params: { magnitude: 0.3 },
  },
  {
    id:    "bad_actor_injection",
    name:  "Bad Actor Injection",
    icon:  "🎭",
    desc:  "Inject 5 misaligned agents. Does society stay aligned?",
    color: "red",
    params: { count: 5 },
  },
  {
    id:    "generational_reset",
    name:  "Generational Reset",
    icon:  "🔄",
    desc:  "Replace 20% of agents. Do norms persist?",
    color: "blue",
    params: { rate: 0.20 },
  },
  {
    id:    "info_asymmetry",
    name:  "Info Asymmetry",
    icon:  "📡",
    desc:  "Give 10% of agents a 3x knowledge advantage.",
    color: "purple",
    params: { fraction: 0.1, multiplier: 3.0 },
  },
  {
    id:    "alignment_dilution",
    name:  "Alignment Dilution",
    icon:  "🧪",
    desc:  "Shift all agents 10% toward defection.",
    color: "rose",
    params: { dilution: 0.1 },
  },
];

const colorMap = {
  amber:  "border-amber-700  hover:bg-amber-900/30",
  red:    "border-red-700    hover:bg-red-900/30",
  blue:   "border-blue-700   hover:bg-blue-900/30",
  purple: "border-purple-700 hover:bg-purple-900/30",
  rose:   "border-rose-700   hover:bg-rose-900/30",
};

export default function ExperimentPanel() {
  const { runExperiment } = useSimStore();
  const [running, setRunning] = useState(null);
  const [log, setLog] = useState([]);

  const handleRun = async (exp) => {
    setRunning(exp.id);
    await runExperiment(exp.id, exp.params);
    setLog((l) => [`${exp.icon} ${exp.name} triggered`, ...l.slice(0, 4)]);
    setTimeout(() => setRunning(null), 1200);
  };

  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
        Experiments
      </h2>
      <div className="flex flex-col gap-2">
        {EXPERIMENTS.map((exp) => (
          <button
            key={exp.id}
            onClick={() => handleRun(exp)}
            disabled={running === exp.id}
            className={`w-full text-left border rounded-lg px-3 py-2 transition
              ${colorMap[exp.color]} border-opacity-60
              ${running === exp.id ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
          >
            <div className="flex items-center gap-2 mb-0.5">
              <span>{exp.icon}</span>
              <span className="text-white text-xs font-semibold">{exp.name}</span>
            </div>
            <p className="text-gray-500 text-xs leading-tight">{exp.desc}</p>
          </button>
        ))}
      </div>
      {log.length > 0 && (
        <div className="mt-3 border-t border-gray-700 pt-2">
          {log.map((l, i) => (
            <p key={i} className="text-xs text-gray-500 truncate">{l}</p>
          ))}
        </div>
      )}
    </div>
  );
}
