import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, MicOff, Volume2, Sparkles, ArrowRight, RefreshCw, CheckCircle2, 
  Send, AlertCircle, MessageSquare, PhoneCall, Building2, Calendar
} from 'lucide-react';
import DemoBadge from '../components/DemoBadge';
import { MOCK_VOICE_PROMPTS } from '../mockData';
import { sendVoiceIntent } from '../api';
import { createSpeechRecognizer, isSpeechRecognitionSupported, speakText } from '../utils/speechEngine';

export default function VoiceAssistantScreen({ setActiveScreen, setSelectedFacility, lang }) {
  const [voiceState, setVoiceState] = useState('idle'); // 'idle' | 'listening' | 'processing' | 'responded'
  const [transcript, setTranscript] = useState('');
  const [textInput, setTextInput] = useState('');
  const [response, setResponse] = useState(null);
  const [dialogContext, setDialogContext] = useState({
    location: null,
    service: null,
    date: 'Tomorrow'
  });
  const [speechSupported, setSpeechSupported] = useState(true);

  const recognizerRef = useRef(null);

  useEffect(() => {
    setSpeechSupported(isSpeechRecognitionSupported());
  }, []);

  const startVoiceRecording = () => {
    if (!isSpeechRecognitionSupported()) {
      alert(lang === 'hi'
        ? 'आपके ब्राउज़र में वॉयस रिकॉग्निशन समर्थित नहीं है। कृपया नीचे दिए गए टेक्स्ट बॉक्स का उपयोग करें।'
        : 'Browser speech recognition is not supported in this environment. Please use the text input fallback below.');
      return;
    }

    try {
      if (recognizerRef.current) {
        try { recognizerRef.current.stop(); } catch {}
      }

      const rec = createSpeechRecognizer(lang);
      recognizerRef.current = rec;

      rec.onstart = () => {
        setVoiceState('listening');
        setTranscript('');
      };

      rec.onresult = (event) => {
        const currentText = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        setTranscript(currentText);
      };

      rec.onerror = (err) => {
        console.warn("Speech recognition error:", err);
        setVoiceState('idle');
      };

      rec.onend = () => {
        if (transcript) {
          processTranscript(transcript);
        } else {
          setVoiceState('idle');
        }
      };

      rec.start();
    } catch (err) {
      console.error("Start recording error:", err);
      setVoiceState('idle');
    }
  };

  const stopVoiceRecording = () => {
    if (recognizerRef.current) {
      try { recognizerRef.current.stop(); } catch {}
    }
  };

  const processTranscript = async (inputQuery) => {
    const textToProcess = inputQuery || transcript || textInput;
    if (!textToProcess) return;

    setTranscript(textToProcess);
    setVoiceState('processing');

    try {
      const result = await sendVoiceIntent({
        transcript: textToProcess,
        lang: lang,
        context_location: dialogContext.location,
        context_service: dialogContext.service,
        context_date: dialogContext.date
      });

      setResponse(result);
      setVoiceState('responded');

      // Update dialog context if location/service matched
      if (result.facilities && result.facilities.length > 0) {
        const fac = result.facilities[0];
        setDialogContext(prev => ({
          ...prev,
          location: fac.area || fac.city,
          matchedFacility: fac
        }));
      }

      // Speak natural response
      const responseSpeech = (lang === 'hi' && result.response_text_hi) ? result.response_text_hi : result.response_text;
      speakText(responseSpeech, lang);

    } catch (err) {
      console.error(err);
      setVoiceState('idle');
    }
  };

  const handleTextInputSubmit = (e) => {
    e.preventDefault();
    if (!textInput.trim()) return;
    processTranscript(textInput);
    setTextInput('');
  };

  const handleReset = () => {
    setVoiceState('idle');
    setTranscript('');
    setResponse(null);
    setDialogContext({ location: null, service: null, date: 'Tomorrow' });
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header Bar */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Mic className="w-6 h-6 text-sky-600" />
            {lang === 'hi' ? 'आवाज सहायक' : 'Voice Assistant'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'hi'
              ? 'वेब स्पीच API और बैकएंड डेटाबेस द्वारा संचालित'
              : 'Powered by Web Speech API & SQLite Database Intent Engine'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Main Mic Recording & Display Container */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm text-center flex flex-col items-center justify-center min-h-[300px] relative overflow-hidden">
        
        {/* Mic Circle */}
        <div className="relative mb-6">
          {voiceState === 'listening' && (
            <div className="absolute inset-0 rounded-full bg-amber-400 animate-ping opacity-75"></div>
          )}
          <button
            onClick={voiceState === 'listening' ? stopVoiceRecording : startVoiceRecording}
            disabled={voiceState === 'processing'}
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
              <Mic className="w-12 h-12 animate-pulse text-slate-950" />
            ) : voiceState === 'processing' ? (
              <RefreshCw className="w-10 h-10 animate-spin" />
            ) : voiceState === 'responded' ? (
              <Volume2 className="w-10 h-10" />
            ) : (
              <Mic className="w-12 h-12" />
            )}
          </button>
        </div>

        {/* Voice State Label */}
        <div className="mb-4">
          {voiceState === 'idle' && (
            <span className="text-slate-700 font-extrabold text-sm bg-slate-100 px-4 py-1.5 rounded-full">
              {lang === 'hi' ? 'बोलने के लिए माइक दबाएं' : 'Tap Mic & Speak Now'}
            </span>
          )}
          {voiceState === 'listening' && (
            <span className="text-amber-950 font-black text-sm bg-amber-200 px-4 py-1.5 rounded-full flex items-center gap-2">
              <span className="w-2.5 h-2.5 bg-amber-700 rounded-full animate-ping"></span>
              {lang === 'hi' ? 'आपकी आवाज सुन रहा है...' : 'Listening to your voice...'}
            </span>
          )}
          {voiceState === 'processing' && (
            <span className="text-sky-900 font-bold text-sm bg-sky-100 px-4 py-1.5 rounded-full">
              {lang === 'hi' ? 'डेटाबेस से खोज हो रही है...' : 'Querying SQLite database...'}
            </span>
          )}
          {voiceState === 'responded' && (
            <span className="text-emerald-900 font-bold text-sm bg-emerald-100 px-4 py-1.5 rounded-full flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              {lang === 'hi' ? 'उत्तर प्राप्त हुआ' : 'Intent Processed'}
            </span>
          )}
        </div>

        {/* Live Transcript Display */}
        {transcript && (
          <div className="w-full bg-slate-50 border border-slate-200 p-4 rounded-2xl mb-4 text-left shadow-inner">
            <div className="text-[11px] font-extrabold text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1">
              <MessageSquare className="w-3.5 h-3.5 text-sky-600" />
              {lang === 'hi' ? 'आपकी आवाज (ट्रांसक्रिप्ट)' : 'Voice Input Transcript'}
            </div>
            <p className="text-sm font-bold text-slate-800 italic">
              "{transcript}"
            </p>
          </div>
        )}

        {/* JanSethu Response Box */}
        {response && (
          <div className="w-full bg-sky-50 border-2 border-sky-300 p-5 rounded-2xl text-left space-y-3 shadow-md">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-amber-500" />
                <span className="font-extrabold text-sky-950 text-sm">
                  JanSethu AI Response
                </span>
                <span className="bg-sky-200 text-sky-900 text-[10px] font-black uppercase px-2 py-0.5 rounded-full">
                  INTENT: {response.intent}
                </span>
              </div>
              <button
                onClick={handleReset}
                className="text-xs text-sky-700 underline font-extrabold hover:text-sky-900"
              >
                {lang === 'hi' ? 'पुनः बोलें' : 'Reset Voice'}
              </button>
            </div>

            <p className="text-sm text-slate-900 font-bold leading-relaxed">
              {lang === 'hi' && response.response_text_hi ? response.response_text_hi : response.response_text}
            </p>

            {/* Direct Action Buttons based on Intent */}
            <div className="pt-2 flex flex-wrap justify-end gap-2">
              {response.intent === 'emergency_help' && (
                <button
                  onClick={() => setActiveScreen('emergency')}
                  className="bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-xs px-4 py-2.5 rounded-xl shadow flex items-center gap-2 transition"
                >
                  <PhoneCall className="w-4 h-4" />
                  <span>{lang === 'hi' ? 'आपातकालीन सहायता खोलें' : 'Go to Emergency Services'}</span>
                </button>
              )}

              {response.facilities && response.facilities.length > 0 && (
                <button
                  onClick={() => {
                    if (response.matched_facility_id) {
                      const fac = response.facilities.find(f => f.id === response.matched_facility_id) || response.facilities[0];
                      setSelectedFacility(fac);
                      setActiveScreen('slots');
                    } else {
                      setActiveScreen('facilities');
                    }
                  }}
                  className="bg-sky-700 hover:bg-sky-800 text-white font-extrabold text-xs px-4 py-2.5 rounded-xl shadow flex items-center gap-2 transition"
                >
                  <Calendar className="w-4 h-4 text-amber-300" />
                  <span>{lang === 'hi' ? 'उपलब्ध स्लॉट देखें' : 'View Matching Slots'}</span>
                  <ArrowRight className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Visible Text Input Fallback */}
      <form onSubmit={handleTextInputSubmit} className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-2">
        <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center justify-between">
          <span>{lang === 'hi' ? 'टेक्स्ट द्वारा लिखें (वॉयस फ़ॉलबैक)' : 'Type Input Fallback'}</span>
          {!speechSupported && (
            <span className="text-amber-700 text-[10px] font-semibold flex items-center gap-1">
              <AlertCircle className="w-3 h-3 text-amber-600" />
              Speech API unavailable in this browser environment
            </span>
          )}
        </label>

        <div className="flex gap-2">
          <input
            type="text"
            value={textInput}
            onChange={(e) => setTextInput(e.target.value)}
            placeholder={lang === 'hi' ? 'उदा. मुझे कल सांगानेर में डॉक्टर दिखाना है...' : 'e.g. I need a fever doctor tomorrow in Sanganer...'}
            className="flex-1 bg-slate-50 border border-slate-300 rounded-xl px-4 py-2.5 text-xs font-bold text-slate-900 focus:outline-none focus:ring-2 focus:ring-sky-600"
          />
          <button
            type="submit"
            className="bg-sky-700 hover:bg-sky-800 text-white font-extrabold px-4 py-2.5 rounded-xl text-xs flex items-center gap-1.5 shadow transition"
          >
            <span>{lang === 'hi' ? 'भेजें' : 'Send'}</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </form>

      {/* Sample Voice Commands */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm">
        <h3 className="text-xs font-extrabold text-slate-500 uppercase tracking-wider mb-3">
          {lang === 'hi' ? 'उदाहरणात्मक वॉयस कमांड (टैप करें)' : 'Sample Voice Inputs (Tap to process)'}
        </h3>
        <div className="flex flex-col gap-2">
          {MOCK_VOICE_PROMPTS.map((p, idx) => (
            <button
              key={idx}
              onClick={() => processTranscript(lang === 'hi' ? p.hi : p.en)}
              className="text-left p-3 bg-slate-50 hover:bg-amber-50/60 border border-slate-200 hover:border-amber-300 rounded-xl text-xs font-bold text-slate-800 transition flex items-center justify-between"
            >
              <span>🗣️ "{lang === 'hi' ? p.hi : p.en}"</span>
              <span className="text-sky-700 font-extrabold">Process</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
