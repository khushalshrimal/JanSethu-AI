import React from 'react';
import { Play, AlertTriangle, Languages, Sparkles, CheckCircle2 } from 'lucide-react';

export default function DemoPresetBar({ onTriggerDemo, activeDemo }) {
  return (
    <div className="bg-slate-900 text-white px-4 py-2.5 rounded-2xl shadow-lg border border-slate-800 space-y-2 mb-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-2">
        <div className="flex items-center gap-2">
          <span className="bg-amber-400 text-slate-950 font-black text-[10px] uppercase px-2 py-0.5 rounded-full flex items-center gap-1">
            <Sparkles className="w-3 h-3 text-slate-950" />
            DEMO MODE
          </span>
          <span className="text-xs font-bold text-slate-300">
            Quick 1-Click Scenario Preset Switcher
          </span>
        </div>

        {/* Simulation Badges */}
        <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400">
          <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded-md border border-slate-700">
            Demo Simulation
          </span>
          <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded-md border border-slate-700">
            Mock Telephony
          </span>
          <span className="bg-slate-800 text-slate-300 px-2 py-0.5 rounded-md border border-slate-700">
            Mock SMS Gateway
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
        {/* DEMO 1 */}
        <button
          onClick={() => onTriggerDemo('demo1')}
          className={`p-2.5 rounded-xl border text-left transition flex items-center justify-between gap-2 ${
            activeDemo === 'demo1'
              ? 'bg-sky-950/80 border-sky-400 text-white ring-1 ring-sky-400'
              : 'bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-800'
          }`}
        >
          <div className="space-y-0.5">
            <div className="text-xs font-black text-sky-400 flex items-center gap-1">
              <Play className="w-3 h-3 fill-sky-400" />
              DEMO 1: Normal Rural Patient
            </div>
            <div className="text-[10px] text-slate-400 leading-tight">
              Hindi ➔ Fever ➔ Baramati Routing ➔ Doctor ➔ Token A-104 ➔ Tracking
            </div>
          </div>
          {activeDemo === 'demo1' && <CheckCircle2 className="w-4 h-4 text-sky-400 flex-shrink-0" />}
        </button>

        {/* DEMO 2 */}
        <button
          onClick={() => onTriggerDemo('demo2')}
          className={`p-2.5 rounded-xl border text-left transition flex items-center justify-between gap-2 ${
            activeDemo === 'demo2'
              ? 'bg-rose-950/80 border-rose-400 text-white ring-1 ring-rose-400'
              : 'bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-800'
          }`}
        >
          <div className="space-y-0.5">
            <div className="text-xs font-black text-rose-400 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3 text-rose-400" />
              DEMO 2: Emergency Screening
            </div>
            <div className="text-[10px] text-slate-400 leading-tight">
              Breathing Difficulty ➔ Safety Pause ➔ 108 Call ➔ Emergency Ward
            </div>
          </div>
          {activeDemo === 'demo2' && <CheckCircle2 className="w-4 h-4 text-rose-400 flex-shrink-0" />}
        </button>

        {/* DEMO 3 */}
        <button
          onClick={() => onTriggerDemo('demo3')}
          className={`p-2.5 rounded-xl border text-left transition flex items-center justify-between gap-2 ${
            activeDemo === 'demo3'
              ? 'bg-amber-950/80 border-amber-400 text-white ring-1 ring-amber-400'
              : 'bg-slate-800/80 border-slate-700 text-slate-200 hover:bg-slate-800'
          }`}
        >
          <div className="space-y-0.5">
            <div className="text-xs font-black text-amber-400 flex items-center gap-1">
              <Languages className="w-3 h-3 text-amber-400" />
              DEMO 3: Marathi Spoken Flow
            </div>
            <div className="text-[10px] text-slate-400 leading-tight">
              मराठी ➔ मला डॉक्टरांना भेटायचे आहे ➔ बारामती ➔ Marathi SMS
            </div>
          </div>
          {activeDemo === 'demo3' && <CheckCircle2 className="w-4 h-4 text-amber-400 flex-shrink-0" />}
        </button>
      </div>
    </div>
  );
}
