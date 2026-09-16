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
          <button
            onClick={() => setLang(lang === 'hi' ? 'en' : 'hi')}
            className="flex items-center gap-1.5 bg-sky-800 hover:bg-sky-900 border border-sky-400/30 px-3 py-2 rounded-xl text-sm font-semibold transition active:scale-95 shadow-sm"
            aria-label="Toggle Language"
          >
            <Globe className="w-4 h-4 text-amber-300" />
            <span>{lang === 'hi' ? 'English' : 'हिंदी'}</span>
          </button>
        </div>
      </div>
    </header>
  );
}
