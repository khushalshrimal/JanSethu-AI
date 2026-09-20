import React from 'react';

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-400 text-xs py-6 border-t border-slate-800 mt-12">
      <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <p className="font-bold text-slate-200">JanSethu AI 2.0 — Healthcare Access Platform</p>
          <p className="text-[11px] text-slate-400 mt-0.5">
            Designed for feature phone voice IVR and smartphone PWA access.
          </p>
        </div>
        <div className="text-[11px] text-slate-400">
          Database-First Architecture | Non-Diagnostic Safety Triage
        </div>
      </div>
    </footer>
  );
}
