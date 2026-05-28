import { useEffect } from "react";
import { useSimStore } from "../store/simStore";
import Header from "../components/layout/Header";
import SocietyCanvas from "../components/canvas/SocietyCanvas";
import SimulationControls from "../components/controls/SimulationControls";
import ExperimentPanel from "../components/controls/ExperimentPanel";
import GiniChart from "../components/observatory/GiniChart";
import CooperationGauge from "../components/observatory/CooperationGauge";
import EventFeed from "../components/observatory/EventFeed";
import AlignmentHeatmap from "../components/observatory/AlignmentHeatmap";
import AgentInspector from "../components/controls/AgentInspector";
import StabilityMeter from "../components/observatory/StabilityMeter";

export default function Dashboard() {
  const { connectWS, disconnectWS } = useSimStore();

  useEffect(() => {
    connectWS();
    return () => disconnectWS();
  }, []);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col">
      <Header />

      <div className="flex flex-1 overflow-hidden">
        {/* ── LEFT SIDEBAR ── */}
        <aside className="w-72 bg-gray-900 border-r border-gray-800 flex flex-col gap-3 p-3 overflow-y-auto">
          <SimulationControls />
          <ExperimentPanel />
          <StabilityMeter />
        </aside>

        {/* ── MAIN CANVAS ── */}
        <main className="flex-1 flex flex-col overflow-hidden">
          <SocietyCanvas />
        </main>

        {/* ── RIGHT SIDEBAR ── */}
        <aside className="w-80 bg-gray-900 border-l border-gray-800 flex flex-col gap-3 p-3 overflow-y-auto">
          <CooperationGauge />
          <AlignmentHeatmap />
          <GiniChart />
          <EventFeed />
          <AgentInspector />
        </aside>
      </div>
    </div>
  );
}
