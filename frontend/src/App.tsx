import React, { useEffect, useState } from 'react';

interface SystemStatus {
  status: string;
  app_name: string;
  environment: string;
}

export const App: React.FC = () => {
  const [health, setHealth] = useState<SystemStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/health')
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        return res.json();
      })
      .then((data) => setHealth(data))
      .catch((err) => setError(err.message));
  }, []);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col items-center justify-center p-6">
      <div className="max-w-xl w-full bg-slate-900 border border-slate-800 rounded-xl p-8 shadow-2xl space-y-6">
        <div className="flex items-center space-x-3">
          <div className="h-4 w-4 rounded-full bg-emerald-500 animate-pulse" />
          <h1 className="text-2xl font-bold tracking-tight text-white">
            NIDS Platform V2.0 Foundation
          </h1>
        </div>

        <p className="text-slate-400 text-sm leading-relaxed">
          Production Infrastructure & Architecture Foundation (Phase B.1) initialized.
        </p>

        <div className="bg-slate-950 border border-slate-850 rounded-lg p-4 font-mono text-xs space-y-2">
          <div className="flex justify-between border-b border-slate-800 pb-2">
            <span className="text-slate-500">Backend API Liveness:</span>
            <span className={health ? "text-emerald-400 font-semibold" : "text-amber-400 font-semibold"}>
              {health ? health.status.toUpperCase() : error ? "UNREACHABLE" : "CONNECTING..."}
            </span>
          </div>
          <div className="flex justify-between border-b border-slate-800 py-2">
            <span className="text-slate-500">System Name:</span>
            <span className="text-slate-300">{health?.app_name || "NIDS-Platform"}</span>
          </div>
          <div className="flex justify-between pt-2">
            <span className="text-slate-500">Environment:</span>
            <span className="text-slate-300">{health?.environment || "development"}</span>
          </div>
        </div>

        <div className="flex justify-between items-center text-xs text-slate-500 border-t border-slate-800/80 pt-4">
          <span>Clean Architecture Skeleton</span>
          <span className="px-2 py-1 bg-slate-800 rounded text-slate-300">Phase B.1 Ready</span>
        </div>
      </div>
    </div>
  );
};

export default App;
