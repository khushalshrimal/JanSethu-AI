import React, { useState, useEffect } from 'react';
import { Phone, PhoneOff, Mic, Volume2, MessageSquare, Signal, Battery, Play, ShieldAlert, AlertTriangle, Activity, CheckCircle, Clock, MapPin, User } from 'lucide-react';
import DemoBadge from '../components/DemoBadge';
import { speakText } from '../utils/speechEngine';
import axios from 'axios';

export default function PhoneSimulatorScreen({ lang: appLang }) {
  const [activeLang, setActiveLang] = useState('hi'); // 'hi' | 'mr' | 'en'
  const [callState, setCallState] = useState('idle'); // 'idle' | 'calling' | 'connected' | 'ended'
  const [callTimer, setCallTimer] = useState(0);
  const [showKeypad, setShowKeypad] = useState(false);
  
  const [callerPhone, setCallerPhone] = useState('+91-9876543210');
  const [lcdText, setLcdText] = useState('JanSethu AI Call Channel\nDial 1800-JANSETHU');
  const [currentStep, setCurrentStep] = useState('welcome');
  const [speechInput, setSpeechInput] = useState('');
  const [receivedSms, setReceivedSms] = useState(null);

  // Live Transcript history
  const [transcript, setTranscript] = useState([]);

  // Live AI Understanding Panel State
  const [aiPanel, setAiPanel] = useState({
    intent: 'None',
    symptoms: 'Not detected',
    duration: 'Not specified',
    location: 'Not specified',
    urgency: 'Low',
    nextAction: 'Ready for Call',
    isEmergency: false
  });

  // Call duration timer effect
  useEffect(() => {
    let interval = null;
    if (callState === 'connected') {
      interval = setInterval(() => {
        setCallTimer(prev => prev + 1);
      }, 1000);
    } else {
      setCallTimer(0);
    }
    return () => clearInterval(interval);
  }, [callState]);

  const formatTimer = (secs) => {
    const m = Math.floor(secs / 60).toString().padStart(2, '0');
    const s = (secs % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  const addTranscript = (sender, text, language = activeLang) => {
    setTranscript(prev => [...prev, {
      sender,
      text,
      language,
      time: new Date().toLocaleTimeString()
    }]);
  };

  const startCall = async () => {
    setCallState('connected');
    setCurrentStep('welcome');
    setReceivedSms(null);
    setTranscript([]);
    setAiPanel({
      intent: 'Greeting & Welcome',
      symptoms: 'Awaiting User Speech',
      duration: 'Initial Turn',
      location: 'System IVR',
      urgency: 'Low',
      nextAction: 'Language & Query Gathering',
      isEmergency: false
    });

    try {
      const res = await axios.post('http://localhost:8000/api/telephony/voice', {
        Caller: callerPhone,
        Step: 'welcome',
        Language: activeLang
      });
      const data = res.data;
      
      const text = activeLang === 'mr' ? (data.speech_text_mr || data.speech_text) : (activeLang === 'hi' ? data.speech_text_hi : data.speech_text);
      setLcdText(`[JANSETHU AI]\n"${text}"`);
      speakText(text, activeLang);
      addTranscript('JanSethu AI', text);
    } catch (err) {
      console.warn("Backend telephony fallback:", err);
      const fallbackText = activeLang === 'mr'
        ? 'जनसेतु AI मध्ये आपले स्वागत आहे. मराठीसाठी 2 किंवा हिंदीसाठी 1 दाबा.'
        : activeLang === 'hi'
        ? 'जनसेतु AI में आपका स्वागत है। हिंदी के लिए 1 दबाएं, मराठी के लिए 2 दबाएं।'
        : 'Welcome to JanSethu AI. Press 1 for Hindi, Press 2 for Marathi, Press 3 for English.';
      setLcdText(`[JANSETHU AI]\n"${fallbackText}"`);
      speakText(fallbackText, activeLang);
      addTranscript('JanSethu AI', fallbackText);
    }
  };

  const handleKeypadPress = async (digit) => {
    if (callState !== 'connected') return;

    addTranscript('Caller (DTMF)', `Pressed Key [ ${digit} ]`);
    setLcdText(`Keypad DTMF Pressed: [ ${digit} ]\nProcessing...`);

    // Quick Language Shortcuts
    let targetLang = activeLang;
    if (digit === '1') targetLang = 'hi';
    if (digit === '2') targetLang = 'mr';
    if (digit === '3') targetLang = 'en';
    if (targetLang !== activeLang) setActiveLang(targetLang);

    try {
      const res = await axios.post('http://localhost:8000/api/telephony/gather', {
        Caller: callerPhone,
        Digits: String(digit),
        Step: currentStep,
        Language: targetLang
      });
      const data = res.data;
      const text = targetLang === 'mr' ? (data.speech_text_mr || data.speech_text) : (targetLang === 'hi' ? data.speech_text_hi : data.speech_text);
      
      setLcdText(`[JANSETHU AI]\n"${text}"`);
      speakText(text, targetLang);
      addTranscript('JanSethu AI', text, targetLang);

      setAiPanel({
        intent: data.intent || 'DTMF Navigation',
        symptoms: data.symptoms || 'Language Selected',
        duration: data.duration || 'In Progress',
        location: data.location || 'System IVR',
        urgency: data.urgency || 'Low',
        nextAction: data.next_action || 'Awaiting Speech Query',
        isEmergency: data.is_emergency || false
      });

      if (data.sms_sent && data.sms_body) {
        setReceivedSms(data.sms_body);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSpokenPhraseSubmit = async (phrase) => {
    const textToSpeak = phrase || speechInput;
    if (!textToSpeak || callState !== 'connected') return;

    addTranscript('Caller (Voice)', `"${textToSpeak}"`, activeLang);
    setLcdText(`Caller Spoke:\n"${textToSpeak}"`);
    setSpeechInput('');

    try {
      const res = await axios.post('http://localhost:8000/api/telephony/gather', {
        Caller: callerPhone,
        SpeechResult: textToSpeak,
        Language: activeLang
      });
      const data = res.data;
      const text = activeLang === 'mr' ? (data.speech_text_mr || data.speech_text) : (activeLang === 'hi' ? data.speech_text_hi : data.speech_text);

      setLcdText(`[JANSETHU AI]\n"${text}"`);
      speakText(text, activeLang);
      addTranscript('JanSethu AI', text, activeLang);

      setAiPanel({
        intent: data.intent || 'Healthcare Query',
        symptoms: data.symptoms || 'Extracted Symptoms',
        duration: data.duration || 'Not specified',
        location: data.location || 'Detected Location',
        urgency: data.urgency || 'Medium',
        nextAction: data.next_action || 'Routing Facility',
        isEmergency: data.is_emergency || false
      });

      if (data.sms_sent && data.sms_body) {
        setReceivedSms(data.sms_body);
      }
    } catch (err) {
      console.error(err);
    }
  };

  // Predefined Hackathon Demo 1 (Fever in Baramati)
  const runHackathonDemo1 = () => {
    startCall();
    setTimeout(() => {
      const demoSpeech = activeLang === 'mr' 
        ? "मला तीन दिवसांपासून ताप आहे बारामतीमध्ये." 
        : activeLang === 'hi' 
        ? "मुझे तीन दिन से बारामती में बुखार है।" 
        : "I have fever for 3 days in Baramati.";
      handleSpokenPhraseSubmit(demoSpeech);
    }, 1500);
  };

  // Predefined Hackathon Demo 2 (Emergency Safety Trigger)
  const runHackathonDemo2 = () => {
    startCall();
    setTimeout(() => {
      const emergencySpeech = activeLang === 'mr' 
        ? "रुग्णाला श्वास घेण्यास खूप त्रास होत आहे आणि छातीत दुखत आहे." 
        : activeLang === 'hi' 
        ? "मरीज को सांस लेने में बहुत तकलीफ हो रही है।" 
        : "The patient has severe breathing difficulty and chest pain.";
      handleSpokenPhraseSubmit(emergencySpeech);
    }, 1500);
  };

  const endCall = () => {
    setCallState('ended');
    setLcdText('Call Ended\nThank you for calling JanSethu AI');
    addTranscript('System', 'Call terminated.');
    setTimeout(() => {
      setCallState('idle');
      setLcdText('JanSethu AI Call Channel\nDial 1800-JANSETHU');
    }, 2000);
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Phone className="w-6 h-6 text-sky-600" />
            {activeLang === 'hi' ? 'जनसेतु AI टेलीफोनी सिम्युलेटर' : activeLang === 'mr' ? 'जनसेतु AI टेलीफोनी सिम्युलेटर' : 'JanSethu AI IVR Phone Simulator'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {activeLang === 'hi'
              ? 'कीपैड/बेसिक फोन के लिए वॉयस-फर्स्ट IVR और सुरक्षा स्क्रीनिंग'
              : 'Voice-first phone call simulator with safety screening & tri-lingual AI extraction'}
          </p>
        </div>
        <DemoBadge lang={activeLang} />
      </div>

      {/* 2-MINUTE HACKATHON DEMO SHORTCUT BANNER */}
      <div className="bg-slate-900 text-white p-4 rounded-3xl border-2 border-amber-400 shadow-xl space-y-3">
        <div className="flex items-center justify-between border-b border-slate-800 pb-2">
          <div className="flex items-center gap-2">
            <Play className="w-5 h-5 text-amber-400 fill-amber-400 animate-pulse" />
            <span className="font-extrabold text-sm text-amber-300">
              {activeLang === 'hi' ? 'हैकाथॉन 2-मिनट लाइव डेमो मोड (Quick Scenarios)' : 'SIH Hackathon 2-Minute Demo Scenarios'}
            </span>
          </div>
          
          {/* Tri-Lingual Toggle */}
          <div className="flex items-center gap-1 bg-slate-800 p-1 rounded-xl text-xs">
            <button
              onClick={() => setActiveLang('hi')}
              className={`px-2.5 py-1 rounded-lg font-bold transition ${activeLang === 'hi' ? 'bg-amber-400 text-slate-950' : 'text-slate-400 hover:text-white'}`}
            >
              हिंदी
            </button>
            <button
              onClick={() => setActiveLang('mr')}
              className={`px-2.5 py-1 rounded-lg font-bold transition ${activeLang === 'mr' ? 'bg-amber-400 text-slate-950' : 'text-slate-400 hover:text-white'}`}
            >
              मराठी
            </button>
            <button
              onClick={() => setActiveLang('en')}
              className={`px-2.5 py-1 rounded-lg font-bold transition ${activeLang === 'en' ? 'bg-amber-400 text-slate-950' : 'text-slate-400 hover:text-white'}`}
            >
              English
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <button
            onClick={runHackathonDemo1}
            className="p-3 bg-slate-800 hover:bg-slate-700 border border-amber-400/40 rounded-2xl text-left transition flex items-center justify-between group"
          >
            <div>
              <div className="font-extrabold text-amber-300 flex items-center gap-1.5">
                <span>Demo 1: Normal Consultation Flow</span>
              </div>
              <p className="text-[11px] text-slate-300 mt-0.5">
                "Fever for 3 days in Baramati" ➔ Facility Routing & SMS
              </p>
            </div>
            <Play className="w-4 h-4 text-amber-400 group-hover:scale-110 transition" />
          </button>

          <button
            onClick={runHackathonDemo2}
            className="p-3 bg-slate-800 hover:bg-slate-700 border border-rose-400/40 rounded-2xl text-left transition flex items-center justify-between group"
          >
            <div>
              <div className="font-extrabold text-rose-300 flex items-center gap-1.5">
                <span>Demo 2: Safety Screening Emergency</span>
              </div>
              <p className="text-[11px] text-slate-300 mt-0.5">
                "Breathing difficulty & chest pain" ➔ 108 Emergency Trigger
              </p>
            </div>
            <ShieldAlert className="w-4 h-4 text-rose-400 group-hover:scale-110 transition" />
          </button>
        </div>
      </div>

      {/* Main Grid Layout: Phone Screen (Left) + AI Understanding Panel & Transcript (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT COLUMN: NOKIA/FEATURE PHONE MOCKUP (5 Cols) */}
        <div className="lg:col-span-5 bg-slate-900 text-white rounded-3xl p-5 shadow-2xl border-4 border-slate-800 max-w-sm mx-auto w-full space-y-4 relative">
          
          {/* Phone Top Status Bar */}
          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono border-b border-slate-800 pb-2">
            <span className="flex items-center gap-1"><Signal className="w-3 h-3 text-emerald-400" /> 4G VOLTE</span>
            <span className="font-bold text-amber-300">JanSethu AI IVR</span>
            <span className="flex items-center gap-1">100% <Battery className="w-3 h-3 text-emerald-400" /></span>
          </div>

          {/* Phone Screen Banner & Call Timer */}
          <div className="bg-emerald-950/90 border-2 border-emerald-500/70 p-4 rounded-2xl min-h-[160px] flex flex-col justify-between font-mono shadow-inner text-emerald-300 relative overflow-hidden">
            <div className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 border-b border-emerald-800/60 pb-1 flex justify-between">
              <span>{callState === 'connected' ? `🔴 LIVE (${formatTimer(callTimer)})` : 'STATUS: READY'}</span>
              <span>1800-JANSETHU</span>
            </div>

            {/* LCD System Prompt Display */}
            <div className="py-2 space-y-1">
              <p className="text-xs font-bold leading-relaxed whitespace-pre-line text-white">
                {lcdText}
              </p>
            </div>

            {/* Pulsing Voice Indicator */}
            {callState === 'connected' && (
              <div className="flex items-center justify-between border-t border-emerald-800/60 pt-1.5 text-[10px]">
                <span className="flex items-center gap-1 text-amber-300 animate-pulse">
                  <Mic className="w-3 h-3 text-amber-400" />
                  JanSethu Listening ({activeLang.toUpperCase()})
                </span>
                <span className="font-bold text-emerald-400">{callerPhone}</span>
              </div>
            )}
          </div>

          {/* EMERGENCY ALERT SCREEN OVERLAY */}
          {aiPanel.isEmergency && (
            <div className="bg-rose-950 border-2 border-rose-500 text-rose-100 p-4 rounded-2xl shadow-xl space-y-3 animate-pulse">
              <div className="flex items-center gap-2 border-b border-rose-800 pb-2">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                <span className="font-black text-xs text-amber-300 uppercase tracking-wide">POTENTIAL EMERGENCY DETECTED</span>
              </div>
              <p className="text-xs font-semibold leading-relaxed">
                Emergency medical assistance is recommended immediately.
              </p>
              <div className="grid grid-cols-2 gap-2 pt-1">
                <a
                  href="tel:108"
                  className="bg-rose-600 hover:bg-rose-700 text-white font-extrabold text-[11px] py-2 px-2 rounded-xl text-center shadow flex items-center justify-center gap-1"
                >
                  <Phone className="w-3 h-3" /> Call 108
                </a>
                <button
                  onClick={() => alert("Routing to nearest Emergency Casualty Ward...")}
                  className="bg-slate-800 hover:bg-slate-700 text-white font-bold text-[11px] py-2 px-2 rounded-xl text-center"
                >
                  Find Emergency
                </button>
              </div>
            </div>
          )}

          {/* Call Control Green/Red Buttons */}
          <div className="grid grid-cols-2 gap-2">
            <button
              onClick={startCall}
              disabled={callState === 'connected'}
              className={`py-3 rounded-2xl font-black text-xs shadow flex items-center justify-center gap-2 transition active:scale-95 ${
                callState === 'connected'
                  ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white animate-bounce'
              }`}
            >
              <Phone className="w-4 h-4" />
              <span>{activeLang === 'hi' ? 'कॉल करें' : activeLang === 'mr' ? 'कॉल करा' : 'CALL'}</span>
            </button>

            <button
              onClick={endCall}
              disabled={callState !== 'connected'}
              className={`py-3 rounded-2xl font-black text-xs shadow flex items-center justify-center gap-2 transition active:scale-95 ${
                callState !== 'connected'
                  ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
                  : 'bg-rose-600 hover:bg-rose-500 text-white'
              }`}
            >
              <PhoneOff className="w-4 h-4" />
              <span>{activeLang === 'hi' ? 'कॉल काटें' : activeLang === 'mr' ? 'कॉल थांबवा' : 'END CALL'}</span>
            </button>
          </div>

          {/* DTMF Keypad Toggle & Input Form */}
          <div className="pt-2 border-t border-slate-800 space-y-2">
            <button
              onClick={() => setShowKeypad(!showKeypad)}
              className="w-full bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold text-xs py-2 rounded-xl flex items-center justify-center gap-2"
            >
              <span>{showKeypad ? 'Hide Keypad' : 'Show DTMF Keypad (1=Hindi, 2=Marathi, 3=English)'}</span>
            </button>

            {showKeypad && (
              <div className="grid grid-cols-3 gap-2 text-center pt-1">
                {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map(digit => (
                  <button
                    key={digit}
                    onClick={() => handleKeypadPress(digit)}
                    className="bg-slate-800 hover:bg-slate-700 active:bg-sky-600 text-white font-mono font-extrabold text-base py-2.5 rounded-xl border border-slate-700 shadow transition active:scale-95"
                  >
                    {digit}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Spoken Voice Input Field */}
          <div className="pt-2 border-t border-slate-800 space-y-2">
            <label className="block text-[11px] font-bold text-slate-400">
              {activeLang === 'hi' ? 'फोन माइक्रोफोन में बोलें:' : activeLang === 'mr' ? 'फोन मायक्रोफोनमध्ये बोला:' : 'Speak Spoken Query:'}
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={speechInput}
                onChange={(e) => setSpeechInput(e.target.value)}
                placeholder={activeLang === 'mr' ? 'उदा. मला तीन दिवसांपासून ताप आहे' : 'e.g. Fever for 3 days in Baramati'}
                className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-semibold text-white focus:outline-none focus:ring-1 focus:ring-amber-400"
              />
              <button
                onClick={() => handleSpokenPhraseSubmit()}
                className="bg-amber-400 hover:bg-amber-300 text-slate-950 font-black px-4 py-2 rounded-xl text-xs transition"
              >
                Speak
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: AI UNDERSTANDING PANEL & LIVE TRANSCRIPT (7 Cols) */}
        <div className="lg:col-span-7 space-y-4">
          
          {/* LIVE AI UNDERSTANDING PANEL */}
          <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
                <Activity className="w-5 h-5 text-sky-600" />
                JanSethu Real-Time AI Extraction Panel
              </h3>
              <span className={`text-[10px] font-black px-2.5 py-1 rounded-full uppercase ${
                aiPanel.isEmergency ? 'bg-rose-100 text-rose-800 animate-pulse' : 'bg-emerald-100 text-emerald-800'
              }`}>
                URGENCY: {aiPanel.urgency}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Intent Detected</span>
                <span className="font-extrabold text-slate-900 text-sm mt-0.5 block">{aiPanel.intent}</span>
              </div>

              <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Extracted Symptoms</span>
                <span className="font-extrabold text-sky-800 text-sm mt-0.5 block">{aiPanel.symptoms}</span>
              </div>

              <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Symptom Duration</span>
                <span className="font-extrabold text-amber-800 text-sm mt-0.5 block">{aiPanel.duration}</span>
              </div>

              <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Location / Area</span>
                <span className="font-extrabold text-emerald-800 text-sm mt-0.5 block">{aiPanel.location}</span>
              </div>

              <div className="bg-slate-50 p-3 rounded-2xl border border-slate-200 sm:col-span-2">
                <span className="text-[10px] font-bold text-slate-400 uppercase block">Next System Action</span>
                <span className="font-extrabold text-purple-800 text-sm mt-0.5 block">{aiPanel.nextAction}</span>
              </div>
            </div>
          </div>

          {/* SMS RECEIPT NOTIFICATION TOAST */}
          {receivedSms && (
            <div className="bg-amber-100 border-2 border-amber-400 text-amber-950 p-4 rounded-3xl shadow-md space-y-1 animate-bounce">
              <div className="flex items-center justify-between text-xs font-extrabold text-amber-900">
                <span className="flex items-center gap-1.5">
                  <MessageSquare className="w-4 h-4 text-amber-700" />
                  REALTIME SMS DISPATCH
                </span>
                <span>To: {callerPhone}</span>
              </div>
              <p className="text-xs font-mono font-bold text-amber-950 pt-1">
                "{receivedSms}"
              </p>
            </div>
          )}

          {/* LIVE CONVERSATION TRANSCRIPT BOX */}
          <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-3">
            <h3 className="font-extrabold text-slate-900 text-sm flex items-center justify-between border-b border-slate-100 pb-2">
              <span className="flex items-center gap-2">
                <Mic className="w-4 h-4 text-sky-600" />
                Live Call Conversation Transcript
              </span>
              <span className="text-xs font-normal text-slate-400">{transcript.length} turns</span>
            </h3>

            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-1">
              {transcript.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-xs italic">
                  Click 'CALL' or a Demo Scenario button to begin live phone conversation.
                </div>
              ) : (
                transcript.map((t, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-2xl text-xs space-y-1 ${
                      t.sender.includes('Caller')
                        ? 'bg-sky-50 border border-sky-100 ml-6 text-slate-800'
                        : 'bg-slate-100 border border-slate-200 mr-6 text-slate-900'
                    }`}
                  >
                    <div className="flex items-center justify-between text-[10px] font-bold text-slate-500">
                      <span>{t.sender}</span>
                      <span>{t.time}</span>
                    </div>
                    <p className="font-medium text-xs leading-relaxed">{t.text}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
