import React from 'react';
import { HeartPulse, Globe } from 'lucide-react';

export default function Header({ lang, setLang }) {
  return (
    <header className="bg-sky-700 text-white shadow-md sticky top-0 z-50">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        {/* Logo and title */}
        <div className="flex items-center gap-3">
          <div className="bg-white/20 p-2 rounded-xl flex items-center justify-center">
            <HeartPulse className="w-8 h-8 text-amber-300" />
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold tracking-tight">
              {lang === 'hi' ? 'जनसेतु AI' : 'JanSethu AI'}
            </h1>
            <p className="text-xs text-sky-100 font-medium">
              {lang === 'hi'
                ? 'आसान स्वास्थ्य सेवा पहुँच (डेमो)'
                : 'Accessible Healthcare Access (DEMO)'}
            </p>
          </div>
        </div>

        {/* Language selector toggle */}
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1.5 bg-sky-800 border border-sky-400/30 px-2.5 py-1.5 rounded-xl text-xs font-semibold shadow-sm">
            <Globe className="w-4 h-4 text-amber-300" />
            <select
              value={lang}
              onChange={(e) => setLang(e.target.value)}
              className="bg-transparent text-white font-bold outline-none cursor-pointer"
            >
              <option value="hi" className="bg-slate-900 text-white">हिंदी</option>
              <option value="mr" className="bg-slate-900 text-white">मराठी</option>
              <option value="en" className="bg-slate-900 text-white">English</option>
            </select>
          </div>
        </div>
      </div>
    </header>
  );
}
