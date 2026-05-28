import { useSimStore } from "../../store/simStore";

export default function Header() {
  const { tick, running, paused, wsConnected, agents, coalitions, norms } = useSimStore();

  const status = !running ? "stopped" : paused ? "paused" : "running";
  const statusColor = {
    running: "text-emerald-400",
    paused:  "text-yellow-400",
    stopped: "text-gray-500",
  }[status];

  const statusDot = {
    running: "bg-emerald-400 animate-pulse",
    paused:  "bg-yellow-400",
    stopped: "bg-gray-600",
  }[status];

  return (
    <header className="h-14 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <div className="text-lg font-bold tracking-tight text-white">
          🧬 Emergent Society Simulator
        </div>
        <span className="text-xs text-gray-500 font-mono">v1.0</span>
      </div>

      <div className="flex items-center gap-6 text-sm">
        {/* WS Status */}
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${wsConnected ? "bg-emerald-400" : "bg-red-500"}`} />
          <span className="text-gray-400 text-xs">{wsConnected ? "Live" : "Disconnected"}</span>
        </div>

        {/* Tick */}
        <div className="font-mono text-gray-300">
          Tick <span className="text-white font-bold">{tick}</span>
        </div>

        {/* Status */}
        <div className="flex items-center gap-1.5">
          <div className={`w-2 h-2 rounded-full ${statusDot}`} />
          <span className={`capitalize font-medium ${statusColor}`}>{status}</span>
        </div>

        {/* Stats */}
        <div className="flex items-center gap-4 text-gray-400 text-xs">
          <span><span className="text-white font-semibold">{agents.length}</span> agents</span>
          <span><span className="text-white font-semibold">{Object.keys(coalitions).length}</span> coalitions</span>
          <span><span className="text-white font-semibold">{norms.length}</span> norms</span>
        </div>
      </div>
    </header>
  );
}
