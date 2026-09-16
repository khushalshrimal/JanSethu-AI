import React, { useState } from 'react';
import { Mic, MicOff, Volume2, Sparkles, ArrowRight, RefreshCw, CheckCircle2 } from 'lucide-react';
import DemoBadge from '../components/DemoBadge';
import { MOCK_VOICE_PROMPTS } from '../mockData';

export default function VoiceAssistantScreen({ setActiveScreen, lang }) {
  const [voiceState, setVoiceState] = useState('idle'); // 'idle' | 'listening' | 'processing' | 'responded'
  const [transcript, setTranscript] = useState('');
  const [response, setResponse] = useState(null);

  const handleSimulateVoice = (promptText) => {
    setVoiceState('listening');
    setTranscript(promptText || (lang === 'hi' ? 'मुझे कल सांगानेर में डॉक्टर को दिखाना है।' : 'I need to see a doctor tomorrow in Sanganer.'));
    
    // Simulate listening -> processing -> responded
    setTimeout(() => {
      setVoiceState('processing');
      setTimeout(() => {
        setVoiceState('responded');
        setResponse({
          intent: 'find_facility',
          text: lang === 'hi'
            ? 'मैंने सांगानेर में 2 सरकारी अस्पताल पाए हैं। जिला नागरिक अस्पताल में कल सुबह 9:00 बजे से स्लॉट उपलब्ध हैं।'
            : 'I found 2 government facilities in Sanganer. District Civil Hospital has available slots starting tomorrow at 9:00 AM.',
          matchedFacilityId: 1
        });
      }, 1200);
    }, 1500);
  };

  const handleReset = () => {
    setVoiceState('idle');
    setTranscript('');
    setResponse(null);
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Mic className="w-6 h-6 text-sky-600" />
            {lang === 'hi' ? 'आवाज सहायता (वॉयस प्रोटोटाइप)' : 'Voice Assistant Simulation'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'hi'
              ? 'आवाज द्वारा स्वास्थ्य सेवा खोज एवं स्लॉट बुकिंग'
              : 'Voice-first navigation simulation for healthcare access'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Main Interactive Mic Box */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm text-center flex flex-col items-center justify-center min-h-[300px] relative overflow-hidden">
        
        {/* Animated Mic Circle */}
        <div className="relative mb-6">
          {voiceState === 'listening' && (
            <div className="absolute inset-0 rounded-full bg-amber-400 animate-ping opacity-75"></div>
          )}
          <button
            onClick={() => handleSimulateVoice()}
            disabled={voiceState === 'listening' || voiceState === 'processing'}
            className={`relative z-10 w-24 h-24 rounded-full flex items-center justify-center shadow-xl transition transform active:scale-95 ${
              voiceState === 'listening'
                ? 'bg-amber-400 text-slate-950 scale-110'
                : voiceState === 'processing'
                ? 'bg-sky-600 text-white animate-pulse'
                : voiceState === 'responded'
                ? 'bg-emerald-600 text-white'
                : 'bg-sky-600 hover:bg-sky-700 text-white'
            }`}
            aria-label="Toggle Voice Recording"
          >
            {voiceState === 'listening' ? (
              <Mic className="w-12 h-12 animate-pulse" />
            ) : voiceState === 'processing' ? (
              <RefreshCw className="w-10 h-10 animate-spin" />
            ) : voiceState === 'responded' ? (
              <Volume2 className="w-10 h-10" />
            ) : (
              <Mic className="w-12 h-12" />
            )}
          </button>
        </div>

        {/* State Label */}
        <div className="mb-4">
          {voiceState === 'idle' && (
            <span className="text-slate-600 font-bold text-sm bg-slate-100 px-4 py-1.5 rounded-full">
              {lang === 'hi' ? 'बोलने के लिए माइक बटन दबाएं' : 'Tap Mic to Speak'}
            </span>
          )}
          {voiceState === 'listening' && (
            <span className="text-amber-900 font-black text-sm bg-amber-100 px-4 py-1.5 rounded-full flex items-center gap-2">
              <span className="w-2.5 h-2.5 bg-amber-600 rounded-full animate-ping"></span>
              {lang === 'hi' ? 'सुन रहा है... बोलिए' : 'Listening... Speak now'}
            </span>
          )}
          {voiceState === 'processing' && (
            <span className="text-sky-900 font-bold text-sm bg-sky-100 px-4 py-1.5 rounded-full">
              {lang === 'hi' ? 'प्रोसेस हो रहा है...' : 'Processing intent...'}
            </span>
          )}
          {voiceState === 'responded' && (
            <span className="text-emerald-900 font-bold text-sm bg-emerald-100 px-4 py-1.5 rounded-full flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              {lang === 'hi' ? 'उत्तर प्राप्त हुआ' : 'Response Ready'}
            </span>
          )}
        </div>

        {/* Live Transcript Display */}
        {transcript && (
          <div className="w-full bg-slate-50 border border-slate-200 p-4 rounded-2xl mb-4 text-left">
            <div className="text-[11px] font-extrabold text-slate-400 uppercase tracking-wider mb-1">
              {lang === 'hi' ? 'आपकी आवाज (ट्रांसक्रिप्ट)' : 'User Voice Input (Transcript)'}
            </div>
            <p className="text-sm font-semibold text-slate-800 italic">
              "{transcript}"
            </p>
          </div>
        )}

        {/* JanSethu Response Box */}
        {response && (
          <div className="w-full bg-sky-50 border-2 border-sky-200 p-4 rounded-2xl text-left space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-500" />
                <span className="font-extrabold text-sky-900 text-sm">
                  {lang === 'hi' ? 'जनसेतु उत्तर' : 'JanSethu Response'}
                </span>
              </div>
              <button
                onClick={handleReset}
                className="text-xs text-sky-700 underline font-medium hover:text-sky-900"
              >
                {lang === 'hi' ? 'पुनः प्रयास' : 'Try Again'}
              </button>
            </div>
            <p className="text-sm text-slate-800 font-medium leading-relaxed">
              {response.text}
            </p>
            <div className="pt-2 flex justify-end">
              <button
                onClick={() => setActiveScreen('facilities')}
                className="bg-sky-700 hover:bg-sky-800 text-white font-extrabold text-xs px-4 py-2.5 rounded-xl shadow flex items-center gap-2 transition"
              >
                <span>{lang === 'hi' ? 'अस्पताल और स्लॉट देखें' : 'View Matching Facilities'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Quick Example Prompt Chips */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="text-xs font-extrabold text-slate-500 uppercase tracking-wider mb-3">
          {lang === 'hi' ? 'उदाहरणात्मक वॉयस कमांड (क्लिक करें)' : 'Sample Voice Inputs (Tap to simulate)'}
        </h3>
        <div className="flex flex-col gap-2">
          {MOCK_VOICE_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleSimulateVoice(lang === 'hi' ? p.hi : p.en)}
              className="text-left p-3 bg-slate-50 hover:bg-amber-50/60 border border-slate-200 hover:border-amber-300 rounded-xl text-xs font-semibold text-slate-800 transition flex items-center justify-between"
            >
              <span>🗣️ "{lang === 'hi' ? p.hi : p.en}"</span>
              <span className="text-sky-600 font-bold">Simulate</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
