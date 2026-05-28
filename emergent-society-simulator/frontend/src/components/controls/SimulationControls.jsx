import { useSimStore } from "../../store/simStore";

export default function SimulationControls() {
  const {
    running, paused, speed,
    startSim, pauseSim, resumeSim, stopSim, resetSim, setSpeed,
  } = useSimStore();

  return (
    <div className="bg-gray-800 rounded-xl p-4">
      <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-widest mb-3">
        Simulation
      </h2>

      {/* Play / Pause / Stop */}
      <div className="flex gap-2 mb-4">
        {!running ? (
          <button
            onClick={startSim}
            className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold py-2 rounded-lg transition"
          >
            ▶ Start
          </button>
        ) : paused ? (
          <button
            onClick={resumeSim}
            className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold py-2 rounded-lg transition"
          >
            ▶ Resume
          </button>
        ) : (
          <button
            onClick={pauseSim}
            className="flex-1 bg-yellow-600 hover:bg-yellow-500 text-white text-sm font-semibold py-2 rounded-lg transition"
          >
            ⏸ Pause
          </button>
        )}
        <button
          onClick={stopSim}
          disabled={!running}
          className="px-3 bg-gray-700 hover:bg-gray-600 text-white text-sm py-2 rounded-lg transition disabled:opacity-40"
        >
          ⏹
        </button>
        <button
          onClick={resetSim}
          className="px-3 bg-red-900 hover:bg-red-800 text-white text-sm py-2 rounded-lg transition"
          title="Reset simulation"
        >
          ↺
        </button>
      </div>

      {/* Speed */}
      <div>
        <div className="flex justify-between text-xs text-gray-400 mb-1">
          <span>Speed</span>
          <span className="font-mono">{speed}s / tick</span>
        </div>
        <input
          type="range"
          min="0.5"
          max="10"
          step="0.5"
          value={speed}
          onChange={(e) => setSpeed(parseFloat(e.target.value))}
          className="w-full accent-emerald-500"
        />
        <div className="flex justify-between text-xs text-gray-600 mt-0.5">
          <span>Fast</span>
          <span>Slow</span>
        </div>
      </div>
    </div>
  );
}
