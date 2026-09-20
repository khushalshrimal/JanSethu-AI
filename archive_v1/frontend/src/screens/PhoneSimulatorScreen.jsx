import React, { useState, useEffect, useRef } from 'react';
import { 
  Phone, PhoneOff, Mic, MicOff, Volume2, MessageSquare, Signal, Battery, Play, 
  ShieldAlert, AlertTriangle, Activity, CheckCircle, Clock, MapPin, User, Sparkles, Keyboard, Radio
} from 'lucide-react';
import DemoBadge from '../components/DemoBadge';
import { 
  speakText, createSpeechRecognizer, isSpeechRecognitionSupported, isSpeechSynthesisSupported 
} from '../utils/speechEngine';
import axios from 'axios';

export default function PhoneSimulatorScreen({ lang: appLang }) {
  const [activeLang, setActiveLang] = useState('hi'); // 'hi' | 'mr' | 'en'
  const [callState, setCallState] = useState('idle'); // 'idle' | 'calling' | 'connected' | 'ended'
  const [voiceStatus, setVoiceStatus] = useState('ready'); // 'ready' | 'listening' | 'ai_speaking' | 'processing'
  
  const [callTimer, setCallTimer] = useState(0);
  const [showKeypad, setShowKeypad] = useState(false);
  const [showTypeFallback, setShowTypeFallback] = useState(false);
  const [showDemoVoiceMode, setShowDemoVoiceMode] = useState(false);

  const [callerPhone, setCallerPhone] = useState('+91-9876543210');
  const [lcdText, setLcdText] = useState('JanSethu AI Call Channel\nDial 1800-JANSETHU');
  const [currentStep, setCurrentStep] = useState('welcome');
  const [textInput, setTextInput] = useState('');
  const [interimTranscript, setInterimTranscript] = useState('');
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

  const recognizerRef = useRef(null);

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

  // Clean up speech recognition on unmount or call end
  useEffect(() => {
    return () => {
      if (recognizerRef.current) {
        try { recognizerRef.current.stop(); } catch {}
      }
      try { window.speechSynthesis.cancel(); } catch {}
    };
  }, []);

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

  const playAiResponse = (text, targetLang = activeLang, onComplete = null) => {
    setVoiceStatus('ai_speaking');
    speakText(
      text,
      targetLang,
      () => setVoiceStatus('ai_speaking'),
      () => {
        setVoiceStatus('ready');
        if (onComplete) onComplete();
      }
    );
  };

  const startCall = async () => {
    setCallState('connected');
    setCurrentStep('welcome');
    setReceivedSms(null);
    setTranscript([]);
    setInterimTranscript('');
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
      addTranscript('JanSethu AI 🔊', text);
      playAiResponse(text, activeLang);
    } catch (err) {
      console.warn("Backend telephony fallback:", err);
      const fallbackText = activeLang === 'mr'
        ? 'जनसेतु AI मध्ये आपले स्वागत आहे. मराठीसाठी 2 किंवा हिंदीसाठी 1 दाबा.'
        : activeLang === 'hi'
        ? 'जनसेतु AI में आपका स्वागत है। हिंदी के लिए 1 दबाएं, मराठी के लिए 2 दबाएं।'
        : 'Welcome to JanSethu AI. Press 1 for Hindi, Press 2 for Marathi, Press 3 for English.';
      setLcdText(`[JANSETHU AI]\n"${fallbackText}"`);
      addTranscript('JanSethu AI 🔊', fallbackText);
      playAiResponse(fallbackText, activeLang);
    }
  };

  // REAL BROWSER MICROPHONE SPEECH RECOGNITION
  const initiateMicListening = () => {
    if (!isSpeechRecognitionSupported()) {
      alert("Browser Speech Recognition API is not supported on this browser. Please use Demo Voice Mode or the Type Fallback below.");
      setShowTypeFallback(true);
      return;
    }

    try {
      window.speechSynthesis.cancel();
      const recognizer = createSpeechRecognizer(activeLang);
      recognizerRef.current = recognizer;

      setVoiceStatus('listening');
      setInterimTranscript('🎙️ Listening... (Speak into microphone)');
      setLcdText(`[LISTENING FOR VOICE...]\nSpeak in ${activeLang === 'hi' ? 'Hindi' : activeLang === 'mr' ? 'Marathi' : 'English'} now.`);

      recognizer.onresult = (event) => {
        let interim = '';
        let final = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            final += event.results[i][0].transcript;
          } else {
            interim += event.results[i][0].transcript;
          }
        }

        if (interim) setInterimTranscript(`"...${interim}"`);

        if (final) {
          setInterimTranscript('');
          handleSpokenPhraseSubmit(final.trim(), 'voice');
        }
      };

      recognizer.onerror = (err) => {
        console.warn("Speech recognition error:", err);
        setVoiceStatus('ready');
        setInterimTranscript('');
        
        let errMsg = `[VOICE NOTICE: ${err.error || 'Stopped'}]`;
        if (err.error === 'not-allowed' || err.error === 'permission-denied') {
          errMsg = "⚠️ Microphone access blocked.\nPlease allow microphone permission in browser settings, or use Demo Voice Mode below.";
        } else if (err.error === 'no-speech') {
          errMsg = "⚠️ No speech heard.\nTap '[ 🎙️ TAP TO SPEAK ]' again or select a Demo Voice phrase below.";
        }
        setLcdText(errMsg);
        setShowDemoVoiceMode(true);
      };

      recognizer.onend = () => {
        if (voiceStatus === 'listening') {
          setVoiceStatus('ready');
        }
      };

      recognizer.start();
    } catch (e) {
      console.error("Failed starting speech recognizer:", e);
      setVoiceStatus('ready');
      setLcdText("⚠️ Mic error. Click Demo Voice Mode phrases below.");
      setShowDemoVoiceMode(true);
    }
  };

  const handleStartListening = () => {
    if (callState !== 'connected') {
      startCall();
      setTimeout(() => {
        initiateMicListening();
      }, 1000);
      return;
    }
    initiateMicListening();
  };

  const handleSpokenPhraseSubmit = async (phrase, inputSource = 'voice') => {
    const textToProcess = phrase || textInput;
    if (!textToProcess || callState !== 'connected') return;

    setVoiceStatus('processing');
    const sourceLabel = inputSource === 'demo' ? 'You (Demo Voice)' : inputSource === 'type' ? 'You (Typed)' : 'You (Spoken Voice)';
    
    addTranscript(sourceLabel, `"${textToProcess}"`, activeLang);
    setLcdText(`User Spoke:\n"${textToProcess}"`);
    setTextInput('');
    setInterimTranscript('');

    try {
      const res = await axios.post('http://localhost:8000/api/telephony/gather', {
        Caller: callerPhone,
        SpeechResult: textToProcess,
        Language: activeLang
      });
      const data = res.data;
      const text = activeLang === 'mr' ? (data.speech_text_mr || data.speech_text) : (activeLang === 'hi' ? data.speech_text_hi : data.speech_text);

      setLcdText(`[JANSETHU AI]\n"${text}"`);
      addTranscript('JanSethu AI 🔊', text, activeLang);

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

      playAiResponse(text, activeLang);
    } catch (err) {
      console.error("Error processing spoken phrase:", err);
      setVoiceStatus('ready');
    }
  };

  const handleKeypadPress = async (digit) => {
    if (callState !== 'connected') return;

    addTranscript('Caller (DTMF)', `Pressed Key [ ${digit} ]`);
    setLcdText(`Keypad DTMF Pressed: [ ${digit} ]\nProcessing...`);

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
      addTranscript('JanSethu AI 🔊', text, targetLang);

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

      playAiResponse(text, targetLang);
    } catch (err) {
      console.error(err);
      setVoiceStatus('ready');
    }
  };

  const endCall = () => {
    try { window.speechSynthesis.cancel(); } catch {}
    if (recognizerRef.current) {
      try { recognizerRef.current.stop(); } catch {}
    }
    setCallState('ended');
    setVoiceStatus('ready');
    setLcdText('Call Ended\nThank you for calling JanSethu AI');
    addTranscript('System', 'Call terminated.');
    setTimeout(() => {
      setCallState('idle');
      setLcdText('JanSethu AI Call Channel\nDial 1800-JANSETHU');
    }, 2000);
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Title & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Phone className="w-6 h-6 text-sky-600" />
            {activeLang === 'hi' ? 'जनसेतु AI वॉयस टेलीफोनी चैनल' : activeLang === 'mr' ? 'जनसेतु AI व्हॉइस टेलिफोनी चॅनेल' : 'JanSethu AI Voice Telephony Channel'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5 font-medium">
            {activeLang === 'hi'
              ? 'कीपैड/बेसिक फोन उपयोगकर्ताओं के लिए वास्तविक समय वॉयस IVR सिम्युलेटर'
              : 'Voice-first telephone call simulator with Web Speech recognition & safety triage'}
          </p>
        </div>
      </div>

      {/* Main Grid Layout: Phone Console (Left) + AI Panel & Transcript (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* LEFT COLUMN: NOKIA/FEATURE PHONE VOICE CONSOLE (5 Cols) */}
        <div className="lg:col-span-5 bg-slate-900 text-white rounded-3xl p-5 shadow-2xl border-4 border-slate-800 max-w-sm mx-auto w-full space-y-4 relative">
          
          {/* Status Header */}
          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono border-b border-slate-800 pb-2">
            <span className="flex items-center gap-1"><Signal className="w-3 h-3 text-emerald-400" /> 4G VOLTE</span>
            <span className="font-bold text-amber-300">1800-JANSETHU</span>
            <span className="flex items-center gap-1">100% <Battery className="w-3 h-3 text-emerald-400" /></span>
          </div>

          {/* LCD Screen Display */}
          <div className="bg-emerald-950/90 border-2 border-emerald-500/70 p-4 rounded-2xl min-h-[170px] flex flex-col justify-between font-mono shadow-inner text-emerald-300 relative overflow-hidden">
            <div className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 border-b border-emerald-800/60 pb-1 flex justify-between items-center">
              <span>{callState === 'connected' ? `📞 JANSETHU AI - CALL CONNECTED (${formatTimer(callTimer)})` : 'STATUS: READY TO CALL'}</span>
              <span className="text-amber-300 uppercase font-black">{activeLang}</span>
            </div>

            {/* LCD System Text */}
            <div className="py-2 space-y-1">
              <p className="text-xs font-bold leading-relaxed whitespace-pre-line text-white">
                {lcdText}
              </p>
              {interimTranscript && (
                <p className="text-[11px] font-semibold text-amber-300 animate-pulse">
                  {interimTranscript}
                </p>
              )}
            </div>

            {/* LIVE AUDIO WAVEFORM ANIMATION */}
            {callState === 'connected' && (
              <div className="border-t border-emerald-800/60 pt-2 flex items-center justify-between text-[10px]">
                {voiceStatus === 'ai_speaking' && (
                  <div className="flex items-center gap-1.5 text-sky-300 font-bold animate-pulse">
                    <Volume2 className="w-3.5 h-3.5 text-sky-400 animate-bounce" />
                    <span>🔊 AI IS SPEAKING...</span>
                  </div>
                )}

                {voiceStatus === 'listening' && (
                  <div className="flex items-center gap-1.5 text-amber-300 font-bold">
                    <Mic className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
                    <span>🎙️ LISTENING (SPEAK NOW)...</span>
                  </div>
                )}

                {voiceStatus === 'processing' && (
                  <div className="flex items-center gap-1.5 text-purple-300 font-bold animate-pulse">
                    <Activity className="w-3.5 h-3.5 text-purple-400" />
                    <span>AI PROCESSING...</span>
                  </div>
                )}

                {voiceStatus === 'ready' && (
                  <div className="flex items-center gap-1 text-emerald-400 font-bold">
                    <span>🟢 READY FOR VOICE</span>
                  </div>
                )}

                <div className="flex items-center gap-1">
                  <span className="w-1.5 h-3 bg-emerald-400 rounded animate-pulse" />
                  <span className="w-1.5 h-4 bg-emerald-400 rounded animate-pulse delay-75" />
                  <span className="w-1.5 h-2 bg-emerald-400 rounded animate-pulse delay-150" />
                </div>
              </div>
            )}
          </div>

          {/* EMERGENCY ALERT SCREEN OVERLAY */}
          {aiPanel.isEmergency && (
            <div className="bg-rose-950 border-2 border-rose-500 text-rose-100 p-4 rounded-2xl shadow-xl space-y-2.5 animate-pulse">
              <div className="flex items-center gap-2 border-b border-rose-800 pb-1.5">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
                <span className="font-black text-xs text-amber-300 uppercase tracking-wide">POTENTIAL EMERGENCY DETECTED</span>
              </div>
              <p className="text-xs font-semibold leading-relaxed">
                Reported severe respiratory distress. Pausing routine OPD booking.
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
              <span>{activeLang === 'hi' ? 'कॉल शुरू करें' : activeLang === 'mr' ? 'कॉल सुरू करा' : 'START CALL'}</span>
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
              <span>{activeLang === 'hi' ? 'कॉल समाप्त' : activeLang === 'mr' ? 'कॉल थांबवा' : 'END CALL'}</span>
            </button>
          </div>

          {/* PRIMARY VOICE ACTION BUTTON */}
          {callState === 'connected' && (
            <div className="space-y-3 pt-1">
              <button
                onClick={handleStartListening}
                disabled={voiceStatus === 'listening' || voiceStatus === 'processing'}
                className={`w-full py-4 rounded-2xl font-black text-sm shadow-xl flex items-center justify-center gap-3 transition transform active:scale-95 border-2 ${
                  voiceStatus === 'listening'
                    ? 'bg-amber-400 border-amber-300 text-slate-950 animate-pulse'
                    : 'bg-gradient-to-r from-sky-600 to-blue-700 hover:from-sky-500 hover:to-blue-600 text-white border-sky-400/50'
                }`}
              >
                <Mic className={`w-6 h-6 ${voiceStatus === 'listening' ? 'text-slate-950 animate-bounce' : 'text-amber-300'}`} />
                <span>
                  {voiceStatus === 'listening'
                    ? (activeLang === 'hi' ? '🎙️ सुन रहा है... (अब बोलें)' : activeLang === 'mr' ? '🎙️ ऐकत आहे... (आता बोला)' : '🎙️ LISTENING... (SPEAK NOW)')
                    : (activeLang === 'hi' ? '[ 🎙️ बोलने के लिए टैप करें ]' : activeLang === 'mr' ? '[ 🎙️ बोलण्यासाठी टॅप करा ]' : '[ 🎙️ TAP TO SPEAK ]')}
                </span>
              </button>

              {/* Language Selector Bar */}
              <div className="flex items-center justify-between bg-slate-800 p-2 rounded-xl text-xs">
                <span className="text-[11px] font-bold text-slate-400">Language:</span>
                <div className="flex gap-1">
                  <button
                    onClick={() => setActiveLang('hi')}
                    className={`px-2.5 py-1 rounded-lg font-extrabold text-[11px] transition ${activeLang === 'hi' ? 'bg-amber-400 text-slate-950' : 'text-slate-400 hover:text-white'}`}
                  >
                    हिंदी
                  </button>
                  <button
                    onClick={() => setActiveLang('mr')}
                    className={`px-2.5 py-1 rounded-lg font-extrabold text-[11px] transition ${activeLang === 'mr' ? 'bg-amber-400 text-slate-950' : 'text-slate-400 hover:text-white'}`}
                  >
                    मराठी
                  </button>
                  <button
                    onClick={() => setActiveLang('en')}
                    className={`px-2.5 py-1 rounded-lg font-extrabold text-[11px] transition ${activeLang === 'en' ? 'bg-amber-400 text-slate-950' : 'text-slate-400 hover:text-white'}`}
                  >
                    English
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* DEMO VOICE MODE (PREDEFINED SPOKEN PHRASE PICKER) */}
          {callState === 'connected' && (
            <div className="bg-slate-850 p-3 rounded-2xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-[11px] font-bold text-amber-400 border-b border-slate-800 pb-1.5">
                <span className="flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  Demo Voice Mode (Simulated Speech Input)
                </span>
                <button
                  onClick={() => setShowDemoVoiceMode(!showDemoVoiceMode)}
                  className="text-slate-400 hover:text-white underline text-[10px]"
                >
                  {showDemoVoiceMode ? 'Hide' : 'Show'}
                </button>
              </div>

              {showDemoVoiceMode && (
                <div className="space-y-1.5 pt-1 text-xs">
                  <button
                    onClick={() => handleSpokenPhraseSubmit(activeLang === 'mr' ? "मला तीन दिवसांपासून ताप आहे बारामतीमध्ये." : activeLang === 'hi' ? "मुझे तीन दिन से बारामती में बुखार है।" : "I have fever for 3 days in Baramati.", 'demo')}
                    className="w-full text-left bg-slate-800 hover:bg-slate-700 p-2.5 rounded-xl border border-slate-700 text-slate-200 transition text-[11px] font-semibold"
                  >
                    🗣️ "Mujhe teen din se tez bukhar hai in Baramati." (Fever Query)
                  </button>

                  <button
                    onClick={() => handleSpokenPhraseSubmit("Baramati", 'demo')}
                    className="w-full text-left bg-slate-800 hover:bg-slate-700 p-2.5 rounded-xl border border-slate-700 text-slate-200 transition text-[11px] font-semibold"
                  >
                    📍 "Baramati." (Location entity)
                  </button>

                  <button
                    onClick={() => handleSpokenPhraseSubmit(activeLang === 'mr' ? "रुग्णाला श्वास घेण्यास खूप त्रास होत आहे." : activeLang === 'hi' ? "मेरे पापा को सांस लेने में बहुत दिक्कत हो रही है।" : "My father has severe breathing difficulty.", 'demo')}
                    className="w-full text-left bg-slate-800 hover:bg-rose-900/60 p-2.5 rounded-xl border border-rose-500/40 text-rose-200 transition text-[11px] font-semibold"
                  >
                    🚨 "Mere papa ko saans lene mein bahut dikkat ho rahi hai." (Emergency)
                  </button>

                  <button
                    onClick={() => handleSpokenPhraseSubmit("मला डॉक्टरांना भेटायचे आहे.", 'demo')}
                    className="w-full text-left bg-slate-800 hover:bg-slate-700 p-2.5 rounded-xl border border-slate-700 text-amber-200 transition text-[11px] font-semibold"
                  >
                    🗣️ "मला डॉक्टरांना भेटायचे आहे." (Marathi Request)
                  </button>
                </div>
              )}
            </div>
          )}

          {/* SECONDARY & FALLBACK CONTROLS (DTMF KEYPAD & TYPE FALLBACK) */}
          {callState === 'connected' && (
            <div className="pt-2 border-t border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <button
                  onClick={() => setShowKeypad(!showKeypad)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold px-3 py-1.5 rounded-xl text-[11px] flex items-center gap-1.5"
                >
                  <Keyboard className="w-3.5 h-3.5 text-sky-400" />
                  <span>{showKeypad ? 'Hide DTMF' : '⌨️ DTMF Keypad'}</span>
                </button>

                <button
                  onClick={() => setShowTypeFallback(!showTypeFallback)}
                  className="text-slate-400 hover:text-slate-200 text-[11px] underline"
                >
                  {showTypeFallback ? 'Hide Type Fallback' : 'Type instead (Fallback)'}
                </button>
              </div>

              {/* DTMF Keypad */}
              {showKeypad && (
                <div className="grid grid-cols-3 gap-2 text-center pt-2">
                  {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map(digit => (
                    <button
                      key={digit}
                      onClick={() => handleKeypadPress(digit)}
                      className="bg-slate-800 hover:bg-slate-700 active:bg-sky-600 text-white font-mono font-extrabold text-base py-2 rounded-xl border border-slate-700 shadow transition active:scale-95"
                    >
                      {digit}
                    </button>
                  ))}
                </div>
              )}

              {/* Type Message Fallback */}
              {showTypeFallback && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSpokenPhraseSubmit(textInput, 'type');
                  }}
                  className="pt-2 space-y-1.5"
                >
                  <label className="block text-[10px] font-bold text-slate-400">
                    Fallback Text Input (if mic unavailable):
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={textInput}
                      onChange={(e) => setTextInput(e.target.value)}
                      placeholder="Type query here..."
                      className="flex-1 bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-semibold text-white focus:outline-none focus:ring-1 focus:ring-amber-400"
                    />
                    <button
                      type="submit"
                      className="bg-amber-400 hover:bg-amber-300 text-slate-950 font-black px-3.5 py-2 rounded-xl text-xs transition"
                    >
                      Send
                    </button>
                  </div>
                </form>
              )}
            </div>
          )}
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

            <div className="space-y-3 max-h-[320px] overflow-y-auto pr-1">
              {transcript.length === 0 ? (
                <div className="text-center py-8 text-slate-400 text-xs italic">
                  Click 'START CALL' and tap '[ 🎙️ TAP TO SPEAK ]' to begin live phone conversation.
                </div>
              ) : (
                transcript.map((t, idx) => (
                  <div
                    key={idx}
                    className={`p-3 rounded-2xl text-xs space-y-1 ${
                      t.sender.includes('You')
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
