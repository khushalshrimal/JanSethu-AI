import React, { useState, useEffect, useRef } from 'react';
import { startCallSession, sendDtmfInput, sendVoiceInput, endCallSession, sendConversationMessage } from '../services/phoneService';
import { Phone, PhoneOff, Volume2, ShieldCheck, RefreshCw, Smartphone, Globe, AlertTriangle, Mic, Send, MessageSquare, Radio, Sparkles, Zap, Bot, PhoneCall } from 'lucide-react';

export default function PhoneSimulator() {
  const [callerPhone, setCallerPhone] = useState('+919876543210');
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [callHistory, setCallHistory] = useState([]);
  
  // Voice & Telephony Loop States
  const [agentMode, setAgentMode] = useState('UNSCRIPTED_AI'); // 'UNSCRIPTED_AI' | 'STRUCTURED_IVR'
  const [inputMode, setInputMode] = useState('VOICE'); // 'VOICE' or 'DTMF'
  const [voiceUtterance, setVoiceUtterance] = useState('');
  const [lastNlu, setLastNlu] = useState(null);
  const [callPhase, setCallPhase] = useState('IDLE'); // 'IDLE' | 'CONNECTING' | 'ASSISTANT_SPEAKING' | 'INTERRUPTED' | 'USER_SPEAKING' | 'LISTENING' | 'PROCESSING'
  const [handsFreeMode, setHandsFreeMode] = useState(true);

  const recognitionRef = useRef(null);
  const activeSessionRef = useRef(null);
  activeSessionRef.current = session;

  // Phase 5 Continuous Microphone & Barge-In Interruption State Refs
  const isSpeakingRef = useRef(false);
  const isInterruptedRef = useRef(false);
  const isProcessingTurnRef = useRef(false);

  // Cleanup speech synthesis & recognition on unmount
  useEffect(() => {
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }
    };
  }, []);

  const currentUtteranceRef = useRef(null);

  // Helper: Speak TTS Prompt to Caller with Barge-In Interruption Support & Chrome/Edge GC Protection
  const speakPrompt = (text, language = 'HI', onComplete) => {
    if (!('speechSynthesis' in window)) {
      if (onComplete) onComplete();
      return;
    }

    // Reset speech interruption flag for new utterance
    isInterruptedRef.current = false;
    isSpeakingRef.current = true;

    // Ensure SpeechSynthesis is active & unpaused on Windows Chrome/Edge
    try {
      window.speechSynthesis.cancel();
      window.speechSynthesis.resume();
    } catch (e) {}

    setCallPhase('ASSISTANT_SPEAKING');

    const cleanText = text.replace(/\[[A-Z]{2}\]\s*/g, '').replace(/[*#]/g, '');
    const utterance = new SpeechSynthesisUtterance(cleanText);
    currentUtteranceRef.current = utterance; // Prevent JS garbage collection from silencing audio mid-sentence

    // Pick localized voice language code
    const langCode = language === 'MR' ? 'mr-IN' : language === 'EN' ? 'en-US' : 'hi-IN';
    utterance.lang = langCode;
    utterance.rate = 0.95; // Slightly clear and deliberate for telephony simulation
    utterance.pitch = 1.0;
    utterance.volume = 1.0;

    // Try selecting native Hindi/Marathi/English browser voice
    const voices = window.speechSynthesis.getVoices();
    if (voices.length > 0) {
      const matchVoice = voices.find(v => v.lang.toLowerCase().includes(langCode.toLowerCase())) ||
                         voices.find(v => v.lang.toLowerCase().includes('hi')) ||
                         voices.find(v => v.lang.toLowerCase().includes('en-in')) ||
                         voices.find(v => v.lang.toLowerCase().includes('en'));
      if (matchVoice) utterance.voice = matchVoice;
    }

    utterance.onend = () => {
      currentUtteranceRef.current = null;
      // If user interrupted speech, do not trigger normal onend completion logic
      if (isInterruptedRef.current) return;

      isSpeakingRef.current = false;
      setCallPhase('IDLE');
      if (onComplete) onComplete();
    };

    utterance.onerror = (e) => {
      console.warn('SpeechSynthesis error:', e);
      currentUtteranceRef.current = null;
      if (isInterruptedRef.current) return;

      isSpeakingRef.current = false;
      setCallPhase('IDLE');
      if (onComplete) onComplete();
    };

    try {
      window.speechSynthesis.speak(utterance);
      window.speechSynthesis.resume();
    } catch (err) {
      console.error('Speech synthesis speak error:', err);
    }

    // Keep continuous mic active & listening during speech for instant barge-in detection
    if (handsFreeMode) {
      setTimeout(() => {
        listenForCallerSpeech(language);
      }, 200);
    }
  };

  // Helper: Start Continuous Speech Recognition with Instant Barge-In Detection
  const listenForCallerSpeech = (currentLang = 'HI') => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setCallPhase('IDLE');
      return;
    }

    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      
      // Stop prior instance cleanly
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }

      const recognition = new SpeechRecognition();
      recognitionRef.current = recognition;

      const langCode = currentLang === 'MR' ? 'mr-IN' : currentLang === 'EN' ? 'en-US' : 'hi-IN';
      recognition.lang = langCode;
      recognition.continuous = true;
      recognition.interimResults = true;

      recognition.onstart = () => {
        if (!isSpeakingRef.current && callPhase !== 'INTERRUPTED') {
          setCallPhase('LISTENING');
        }
      };

      // Detect speech onset / sound onset for instant barge-in cancellation
      const handleSpeechOnset = () => {
        if (isSpeakingRef.current) {
          // Instant Barge-In Interruption!
          isInterruptedRef.current = true;
          isSpeakingRef.current = false;
          if ('speechSynthesis' in window) {
            window.speechSynthesis.cancel();
          }
          setCallPhase('INTERRUPTED');
          setTimeout(() => {
            setCallPhase('USER_SPEAKING');
          }, 300);
        } else if (!isProcessingTurnRef.current) {
          setCallPhase('USER_SPEAKING');
        }
      };

      recognition.onsoundstart = handleSpeechOnset;
      recognition.onspeechstart = handleSpeechOnset;

      recognition.onresult = async (event) => {
        // If speech output is active when user speaks, trigger instant barge-in
        if (isSpeakingRef.current) {
          handleSpeechOnset();
        }

        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
          } else {
            interimTranscript += event.results[i][0].transcript;
          }
        }

        const candidateText = finalTranscript.trim() || interimTranscript.trim();
        if (!candidateText) return;

        // If we have a final result or substantial text, submit turn to backend
        const isFinal = event.results[event.results.length - 1].isFinal;
        if (isFinal && candidateText.length > 0) {
          if (isProcessingTurnRef.current) return; // Submission guard
          
          isProcessingTurnRef.current = true;
          setVoiceUtterance(candidateText);
          setCallPhase('PROCESSING');

          try {
            recognition.stop();
          } catch (e) {}

          await processVoiceTurn(candidateText);
        }
      };

      recognition.onerror = (err) => {
        if (err.error !== 'no-speech' && err.error !== 'aborted') {
          console.warn('Speech recognition error:', err.error);
        }
        if (!isProcessingTurnRef.current && !isSpeakingRef.current) {
          setCallPhase('IDLE');
        }
      };

      recognition.onend = () => {
        // If call is active and hands-free, seamlessly restart mic loop if not currently processing or speaking
        if (activeSessionRef.current && activeSessionRef.current.status === 'ACTIVE' && handsFreeMode && !isProcessingTurnRef.current && !isSpeakingRef.current) {
          try {
            recognition.start();
          } catch (e) {}
        } else if (!isSpeakingRef.current && !isProcessingTurnRef.current) {
          setCallPhase((prev) => (prev === 'LISTENING' || prev === 'USER_SPEAKING' ? 'IDLE' : prev));
        }
      };

      recognition.start();
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
      setCallPhase('IDLE');
    }
  };

  // Centralized Voice Turn Handler
  const processVoiceTurn = async (spokenText) => {
    const curSess = activeSessionRef.current;
    if (!curSess || curSess.status !== 'ACTIVE') {
      isProcessingTurnRef.current = false;
      return;
    }

    // Ensure any leftover TTS playback is halted
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }

    setLoading(true);
    setError(null);
    isProcessingTurnRef.current = true;

    try {
      if (agentMode === 'UNSCRIPTED_AI') {
        const data = await sendConversationMessage(
          curSess.conv_session_id || `conv-${curSess.session_id}`,
          spokenText,
          curSess.language || 'hi'
        );

        const updatedSess = {
          session_id: curSess.session_id,
          conv_session_id: data.session_id,
          caller_phone: curSess.caller_phone || callerPhone,
          current_state: data.response_type,
          language: data.language || 'HI',
          status: 'ACTIVE',
          prompt_text: data.assistant_message,
          voice_playback: data.assistant_message,
          options: data.missing_fields?.length > 0 ? data.missing_fields : []
        };

        setSession(updatedSess);
        activeSessionRef.current = updatedSess;

        setLastNlu({
          intent: data.intent,
          confidence: 0.95,
          detected_language: data.language || 'HI',
          raw_text: spokenText,
          normalized_text: spokenText,
          entities: data.entities
        });

        setCallHistory((prev) => [
          ...prev,
          { type: 'USER_VOICE', text: `🎤 "${spokenText}"`, time: new Date().toLocaleTimeString() },
          { type: 'SYSTEM', text: data.assistant_message, time: new Date().toLocaleTimeString() }
        ]);

        isProcessingTurnRef.current = false;

        speakPrompt(data.assistant_message, data.language || 'HI', () => {
          if (handsFreeMode && updatedSess.status === 'ACTIVE') {
            setTimeout(() => {
              listenForCallerSpeech(updatedSess.language || 'HI');
            }, 300);
          }
        });
        return;
      }

      const data = await sendVoiceInput(curSess.session_id, spokenText, curSess.language);
      
      const updatedSess = {
        session_id: data.session_id,
        caller_phone: data.caller_phone,
        current_state: data.current_state,
        language: data.language,
        status: data.status,
        prompt_text: data.prompt_text,
        voice_playback: data.voice_playback,
        options: data.options
      };

      setSession(updatedSess);
      activeSessionRef.current = updatedSess;

      setLastNlu({
        intent: data.intent,
        confidence: data.confidence,
        detected_language: data.detected_language,
        raw_text: data.raw_text,
        normalized_text: data.normalized_text,
        entities: data.entities
      });

      setCallHistory((prev) => [
        ...prev,
        { type: 'USER_VOICE', text: `🎤 "${spokenText}"`, time: new Date().toLocaleTimeString() },
        { type: 'SYSTEM', text: data.voice_playback, time: new Date().toLocaleTimeString() }
      ]);

      isProcessingTurnRef.current = false;

      // Speak TTS response and keep continuous hands-free voice loop ready
      speakPrompt(data.voice_playback || data.prompt_text, data.language, () => {
        if (handsFreeMode && updatedSess.status === 'ACTIVE') {
          setTimeout(() => {
            listenForCallerSpeech(updatedSess.language);
          }, 300);
        }
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Voice input processing failed.');
      setCallPhase('IDLE');
      isProcessingTurnRef.current = false;
    } finally {
      setLoading(false);
    }
  };

  // 1-Click Call Initiation
  const handleStartCall = async (e) => {
    if (e) e.preventDefault();
    if (!callerPhone.trim()) return;

    setLoading(true);
    setError(null);
    setLastNlu(null);
    setCallPhase('CONNECTING');
    isProcessingTurnRef.current = false;

    try {
      if (agentMode === 'UNSCRIPTED_AI') {
        const convId = `conv-${Date.now()}`;
        const initialPrompt = "Namaste! JanSethu Natural AI Voice Agent mein aapka swagat hai. Main aapki kya madad kar sakta hoon? Aap doctor search, OPD booking ya emergency help ke liye baat kar sakte hain.";
        const initialSess = {
          session_id: Date.now(),
          conv_session_id: convId,
          caller_phone: callerPhone.trim(),
          current_state: 'CONVERSATIONAL_AI',
          language: 'HI',
          status: 'ACTIVE',
          prompt_text: initialPrompt,
          voice_playback: initialPrompt,
          options: ['Doctor Search', 'OPD Booking', 'Emergency Help', 'Check Status']
        };

        setSession(initialSess);
        activeSessionRef.current = initialSess;

        setCallHistory([
          { type: 'SYSTEM', text: initialPrompt, time: new Date().toLocaleTimeString() }
        ]);

        speakPrompt(initialPrompt, 'HI', () => {
          if (handsFreeMode) {
            setTimeout(() => {
              listenForCallerSpeech('HI');
            }, 300);
          }
        });
        return;
      }

      const data = await startCallSession(callerPhone.trim());
      setSession(data);
      activeSessionRef.current = data;

      setCallHistory([
        { type: 'SYSTEM', text: data.voice_playback, time: new Date().toLocaleTimeString() }
      ]);

      // Unlocks browser audio & starts true hands-free voice loop with continuous mic & barge-in!
      speakPrompt(data.voice_playback || data.prompt_text, data.language, () => {
        if (handsFreeMode) {
          setTimeout(() => {
            listenForCallerSpeech(data.language);
          }, 300);
        }
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start phone call session.');
      setCallPhase('IDLE');
    } finally {
      setLoading(false);
    }
  };

  // Physical Keypad DTMF Action
  const handleKeyPress = async (key) => {
    if (!session || session.status !== 'ACTIVE') return;

    // Instant barge-in cancellation on keypress as well!
    isInterruptedRef.current = true;
    isSpeakingRef.current = false;
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }

    setLoading(true);
    setError(null);
    setCallPhase('PROCESSING');
    isProcessingTurnRef.current = true;

    try {
      const data = await sendDtmfInput(session.session_id, key);
      setSession(data);
      activeSessionRef.current = data;

      setCallHistory((prev) => [
        ...prev,
        { type: 'USER', text: `DTMF Key Pressed: [ ${key} ]`, time: new Date().toLocaleTimeString() },
        { type: 'SYSTEM', text: data.voice_playback, time: new Date().toLocaleTimeString() }
      ]);

      isProcessingTurnRef.current = false;

      speakPrompt(data.voice_playback || data.prompt_text, data.language, () => {
        if (handsFreeMode && data.status === 'ACTIVE') {
          setTimeout(() => {
            listenForCallerSpeech(data.language);
          }, 300);
        }
      });
    } catch (err) {
      setError(err.response?.data?.detail || 'DTMF processing failed.');
      setCallPhase('IDLE');
      isProcessingTurnRef.current = false;
    } finally {
      setLoading(false);
    }
  };

  // Manual Utterance Text Send (Triggers Barge-In if speaking)
  const handleSendVoiceUtterance = async (e) => {
    if (e) e.preventDefault();
    if (!session || session.status !== 'ACTIVE' || !voiceUtterance.trim()) return;

    const text = voiceUtterance.trim();
    setVoiceUtterance('');

    // Trigger barge-in cancellation if assistant is currently speaking
    if (isSpeakingRef.current) {
      isInterruptedRef.current = true;
      isSpeakingRef.current = false;
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
      setCallPhase('INTERRUPTED');
    }

    await processVoiceTurn(text);
  };

  // Manual Mic Trigger (if user clicks microphone icon manually)
  const handleManualMicClick = () => {
    if (isSpeakingRef.current) {
      // Manual click while assistant speaking triggers instant barge-in!
      isInterruptedRef.current = true;
      isSpeakingRef.current = false;
      if ('speechSynthesis' in window) window.speechSynthesis.cancel();
      setCallPhase('INTERRUPTED');
      setTimeout(() => {
        listenForCallerSpeech(session?.language || 'HI');
      }, 200);
      return;
    }

    if (callPhase === 'LISTENING' || callPhase === 'USER_SPEAKING') {
      if (recognitionRef.current) {
        try { recognitionRef.current.stop(); } catch (e) {}
      }
      setCallPhase('IDLE');
    } else {
      listenForCallerSpeech(session?.language || 'HI');
    }
  };

  // End Call Handler
  const handleEndCall = async () => {
    isInterruptedRef.current = true;
    isSpeakingRef.current = false;
    isProcessingTurnRef.current = false;

    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (e) {}
    }

    if (!session) return;
    setLoading(true);
    setCallPhase('IDLE');

    try {
      const data = await endCallSession(session.session_id);
      setSession(data);
      activeSessionRef.current = null;

      setCallHistory((prev) => [
        ...prev,
        { type: 'SYSTEM', text: 'Call Terminated.', time: new Date().toLocaleTimeString() }
      ]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const keypadLayout = [
    ['1', '2', '3'],
    ['4', '5', '6'],
    ['7', '8', '9'],
    ['*', '0', '#'],
  ];

  return (
    <div className="max-w-4xl mx-auto my-6 px-4 space-y-6">
      {/* Header Banner */}
      <div className="bg-slate-900 text-white p-6 rounded-3xl border border-slate-800 shadow-md space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="bg-amber-400 text-slate-950 font-black text-[10px] px-2 py-0.5 rounded uppercase tracking-wider flex items-center gap-1">
                <Sparkles className="w-3 h-3 text-slate-950" />
                Phase 5 Natural Voice Telephony
              </span>
              <h1 className="text-xl font-black text-white">Continuous Voice + Speech Interruption (Barge-In)</h1>
            </div>
            <p className="text-xs text-amber-300 font-bold mt-1 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-amber-400 flex-shrink-0" />
              <span>Natural Spoken Dialogue with Continuous Microphone & Speech Interruption (Barge-In)</span>
            </p>
            <p className="text-[11px] text-slate-400 mt-0.5">
              Supports continuous microphone monitoring, instant TTS cancellation on user interruption, Hindi/Marathi/English NLU, and DTMF keypad fallback.
            </p>
          </div>

          <span className="px-3 py-1 bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded-full text-xs font-bold w-fit flex items-center gap-1.5">
            <Radio className="w-3.5 h-3.5 animate-pulse text-emerald-400" />
            Live Continuous Telephony Voice
          </span>
        </div>

        {/* Agent Mode Switcher Bar */}
        <div className="bg-slate-950 p-1.5 rounded-2xl border border-slate-800 flex flex-col sm:flex-row items-center gap-2 text-xs">
          <button
            type="button"
            onClick={() => { setAgentMode('UNSCRIPTED_AI'); if(session) handleEndCall(); }}
            className={`w-full sm:flex-1 py-2.5 px-4 rounded-xl font-black transition flex items-center justify-center gap-2 ${
              agentMode === 'UNSCRIPTED_AI'
                ? 'bg-gradient-to-r from-amber-400 to-amber-500 text-slate-950 shadow-lg scale-[1.01]'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <Bot className="w-4 h-4" />
            <span>🧠 Natural Conversational AI (Unscripted Voice)</span>
          </button>
          <button
            type="button"
            onClick={() => { setAgentMode('STRUCTURED_IVR'); if(session) handleEndCall(); }}
            className={`w-full sm:flex-1 py-2.5 px-4 rounded-xl font-black transition flex items-center justify-center gap-2 ${
              agentMode === 'STRUCTURED_IVR'
                ? 'bg-sky-600 text-white shadow-lg scale-[1.01]'
                : 'text-slate-400 hover:text-white hover:bg-slate-800'
            }`}
          >
            <PhoneCall className="w-4 h-4" />
            <span>📞 Structured Phone Hotline (Menu 1-2-3 Tree)</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-start">
        {/* Left Column: Feature Keypad Phone Chassis */}
        <div className="md:col-span-6 bg-slate-900 p-6 rounded-3xl border-4 border-slate-800 shadow-2xl space-y-4 text-white font-sans max-w-sm mx-auto w-full">
          {/* Top Speaker & Branding */}
          <div className="flex items-center justify-between border-b border-slate-800 pb-2">
            <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
              <Volume2 className="w-4 h-4 text-amber-400" />
              <span>JanSethu Continuous Voice Hotline</span>
            </div>
            <div className="flex items-center gap-2">
              <label className="text-[9px] text-slate-400 flex items-center gap-1 cursor-pointer">
                <input
                  type="checkbox"
                  checked={handsFreeMode}
                  onChange={(e) => setHandsFreeMode(e.target.checked)}
                  className="rounded bg-slate-800 border-slate-700 text-amber-400 focus:ring-0"
                />
                Continuous Loop
              </label>
              <div className="w-6 h-1 bg-slate-700 rounded-full"></div>
            </div>
          </div>

          {/* LCD Screen Display */}
          <div className="bg-sky-950 border-2 border-sky-800 p-4 rounded-2xl space-y-3 shadow-inner text-sky-100 min-h-[230px] flex flex-col justify-between">
            {/* Status Header */}
            <div className="flex items-center justify-between text-[10px] font-mono border-b border-sky-800/80 pb-1 text-sky-300">
              <span className="flex items-center gap-1">
                <Globe className="w-3 h-3 text-emerald-400" />
                {session ? `LANG: ${session.language}` : 'SIGNAL: GSM/VOIP'}
              </span>
              
              {/* Telephony Call Phase Status Pill */}
              <span className={`font-bold px-2 py-0.5 rounded uppercase flex items-center gap-1 text-[10px] ${
                callPhase === 'ASSISTANT_SPEAKING'
                  ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30 animate-pulse'
                  : callPhase === 'INTERRUPTED'
                  ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30 animate-bounce font-extrabold'
                  : callPhase === 'USER_SPEAKING' || callPhase === 'LISTENING'
                  ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30 animate-pulse'
                  : callPhase === 'PROCESSING'
                  ? 'bg-sky-500/20 text-sky-300 border border-sky-500/30'
                  : session?.status === 'ACTIVE'
                  ? 'bg-emerald-500/20 text-emerald-300'
                  : 'bg-slate-800 text-slate-400'
              }`}>
                {callPhase === 'ASSISTANT_SPEAKING' && <Volume2 className="w-3 h-3 text-amber-400" />}
                {callPhase === 'INTERRUPTED' && <Zap className="w-3 h-3 text-purple-400 fill-purple-400 animate-spin" />}
                {(callPhase === 'USER_SPEAKING' || callPhase === 'LISTENING') && <Mic className="w-3 h-3 text-rose-400" />}
                {callPhase === 'PROCESSING' && <RefreshCw className="w-3 h-3 animate-spin text-sky-400" />}
                <span>{callPhase !== 'IDLE' ? callPhase : session?.status || 'STANDBY'}</span>
              </span>
            </div>

            {/* Main Screen Content */}
            {!session ? (
              <div className="text-center py-6 space-y-2">
                <Smartphone className="w-8 h-8 text-sky-400 mx-auto opacity-70" />
                <p className="text-xs font-bold text-sky-200">JanSethu Voice Hotline Ready</p>
                <p className="text-[10px] text-sky-400">Click [ CALL JANSETHU ] for continuous voice + barge-in conversation</p>
              </div>
            ) : (
              <div className="space-y-2 text-xs">
                <div className="text-[10px] font-mono text-sky-300 flex justify-between">
                  <span>State: <strong className="text-amber-300">{session.current_state}</strong></span>
                  <span>Call #{session.session_id}</span>
                </div>

                {/* Simulated Audio Speaker Output */}
                <div className="bg-sky-900/80 p-3 rounded-xl border border-sky-700 text-white font-medium text-xs space-y-1">
                  <div className="flex items-center justify-between text-[10px]">
                    <span className="text-amber-300 font-bold uppercase flex items-center gap-1">
                      <Volume2 className="w-3 h-3 animate-pulse" />
                      Voice Speaker Prompt
                    </span>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => speakPrompt(session.voice_playback || session.prompt_text, session.language || 'HI')}
                        className="px-2 py-0.5 bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-[9px] rounded flex items-center gap-1 transition shadow cursor-pointer"
                        title="Click to replay AI spoken voice"
                      >
                        <Volume2 className="w-3 h-3 text-slate-950" />
                        <span>🔊 Suno AI Ki Awaz</span>
                      </button>
                      {callPhase === 'ASSISTANT_SPEAKING' && (
                        <span className="text-[9px] bg-amber-400/20 text-amber-300 px-1.5 py-0.2 rounded font-bold">SPEAKING</span>
                      )}
                      {callPhase === 'INTERRUPTED' && (
                        <span className="text-[9px] bg-purple-500/30 text-purple-300 px-1.5 py-0.2 rounded font-black flex items-center gap-0.5">
                          <Zap className="w-2.5 h-2.5" /> INTERRUPTED
                        </span>
                      )}
                    </div>
                  </div>
                  <p className="text-[11px] leading-relaxed">{session.voice_playback || session.prompt_text}</p>
                </div>

                {/* Phase 6 Emergency Assistance Panel */}
                {(session?.current_state === 'EMERGENCY' || lastNlu?.intent === 'EMERGENCY') && (
                  <div className="bg-rose-950/90 border-2 border-rose-600 p-3 rounded-xl text-white space-y-2 animate-pulse shadow-lg">
                    <div className="flex items-center justify-between border-b border-rose-800 pb-1.5">
                      <span className="text-xs font-black text-rose-300 flex items-center gap-1.5 uppercase">
                        <AlertTriangle className="w-4 h-4 text-rose-400 fill-rose-400" />
                        🚨 EMERGENCY ASSISTANCE ACTIVATED
                      </span>
                      <span className="bg-rose-500 text-slate-950 font-black text-[9px] px-1.5 py-0.5 rounded uppercase">
                        SIMULATED / MOCK
                      </span>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
                      <div className="bg-rose-900/60 p-1.5 rounded border border-rose-700">
                        <span className="text-rose-300 block text-[9px]">Priority Status</span>
                        <strong className="text-white">EMERGENCY OVERRIDE</strong>
                      </div>
                      <div className="bg-rose-900/60 p-1.5 rounded border border-rose-700">
                        <span className="text-rose-300 block text-[9px]">Assistance Flow</span>
                        <strong className="text-amber-300">SIMULATED DISPATCH</strong>
                      </div>
                    </div>

                    <p className="text-[10px] text-rose-200 leading-snug">
                      ℹ️ This prototype uses <strong>SIMULATED emergency routing</strong>. For real life-threatening emergencies, please dial <strong>108 / 112</strong> immediately.
                    </p>
                  </div>
                )}

                {/* Hands-Free Mic Active & Interruption Indicators */}
                {callPhase === 'INTERRUPTED' && (
                  <div className="bg-purple-950/80 border border-purple-700/80 p-2 rounded-xl text-purple-200 text-[11px] font-bold flex items-center justify-between animate-pulse">
                    <span className="flex items-center gap-1.5">
                      <Zap className="w-3.5 h-3.5 text-purple-400 fill-purple-400" />
                      ⚡ Speech Interrupted (Barge-In)! Listening...
                    </span>
                    <span className="w-2 h-2 bg-purple-400 rounded-full animate-ping"></span>
                  </div>
                )}


                {(callPhase === 'LISTENING' || callPhase === 'USER_SPEAKING') && (
                  <div className="bg-rose-950/80 border border-rose-700/80 p-2 rounded-xl text-rose-200 text-[11px] font-bold flex items-center justify-between animate-pulse">
                    <span className="flex items-center gap-1.5">
                      <Mic className="w-3.5 h-3.5 text-rose-400" />
                      {callPhase === 'USER_SPEAKING' ? '🗣️ User speaking...' : '🎙️ Continuous Microphone active...'}
                    </span>
                    <span className="w-2 h-2 bg-rose-500 rounded-full animate-ping"></span>
                  </div>
                )}

                {/* Available Keypad Options */}
                {session.options && session.options.length > 0 && (
                  <div className="pt-1 text-[11px] space-y-1">
                    <span className="text-[10px] font-bold text-sky-300 uppercase">DTMF Menu Options:</span>
                    <div className="grid grid-cols-2 gap-1 text-[10px]">
                      {session.options.map((opt) => (
                        <div key={opt.key} className="bg-sky-900/60 px-2 py-1 rounded text-sky-200 font-medium">
                          <strong className="text-amber-300">[{opt.key}]</strong> {opt.label}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Screen Footer */}
            <div className="text-[9px] text-sky-400 text-center font-mono border-t border-sky-800/80 pt-1">
              {loading ? 'Processing Telephony Domain Request...' : handsFreeMode ? 'Continuous Mic + Barge-In Active' : 'Push-to-Talk / DTMF Active'}
            </div>
          </div>

          {/* Caller Phone Input */}
          {!session && (
            <div>
              <label className="block text-[10px] font-bold text-slate-400 uppercase mb-1">
                Caller Phone Number (Test First-Time vs Returning User)
              </label>
              <input
                type="text"
                value={callerPhone}
                onChange={(e) => setCallerPhone(e.target.value)}
                placeholder="+919876543210"
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs font-mono font-bold text-white outline-none focus:ring-2 focus:ring-amber-400"
              />
              <p className="text-[10px] text-slate-400 mt-1">
                Tip: Enter new number for Auto-Registration flow, or <strong>+919876543210</strong> for Returning User flow.
              </p>
            </div>
          )}

          {/* Call Control Action Buttons */}
          <div className="grid grid-cols-2 gap-3 pt-1">
            <button
              onClick={handleStartCall}
              disabled={loading || session?.status === 'ACTIVE'}
              className="py-2.5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white rounded-xl font-extrabold text-xs transition shadow-md flex items-center justify-center gap-1.5"
            >
              <Phone className="w-4 h-4" />
              <span>CALL JANSETHU</span>
            </button>
            <button
              onClick={handleEndCall}
              disabled={loading || !session || session?.status !== 'ACTIVE'}
              className="py-2.5 bg-rose-600 hover:bg-rose-500 disabled:opacity-50 text-white rounded-xl font-extrabold text-xs transition shadow-md flex items-center justify-center gap-1.5"
            >
              <PhoneOff className="w-4 h-4" />
              <span>END CALL</span>
            </button>
          </div>

          {/* Input Mode Switcher (Voice vs DTMF Keypad) */}
          <div className="pt-1">
            <div className="flex bg-slate-800 p-1 rounded-xl border border-slate-700 text-xs font-bold text-slate-300">
              <button
                type="button"
                onClick={() => setInputMode('VOICE')}
                className={`flex-1 py-1.5 rounded-lg flex items-center justify-center gap-1 transition ${
                  inputMode === 'VOICE' ? 'bg-amber-400 text-slate-950 font-black shadow' : 'hover:text-white'
                }`}
              >
                <Mic className="w-3.5 h-3.5" />
                <span>Spoken Voice</span>
              </button>
              <button
                type="button"
                onClick={() => setInputMode('DTMF')}
                className={`flex-1 py-1.5 rounded-lg flex items-center justify-center gap-1 transition ${
                  inputMode === 'DTMF' ? 'bg-amber-400 text-slate-950 font-black shadow' : 'hover:text-white'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" />
                <span>DTMF Keypad</span>
              </button>
            </div>
          </div>

          {/* Voice Utterance Controls */}
          {inputMode === 'VOICE' && (
            <div className="space-y-2 pt-1">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                Voice Utterance (Continuous Speech / Barge-In Interrupt)
              </span>
              <form onSubmit={handleSendVoiceUtterance} className="space-y-2">
                <div className="relative">
                  <input
                    type="text"
                    value={voiceUtterance}
                    onChange={(e) => setVoiceUtterance(e.target.value)}
                    disabled={loading || !session || session?.status !== 'ACTIVE'}
                    placeholder={
                      session?.language === 'MR'
                        ? 'उदा. "रमेश कुमार" किंवा "मला डॉक्टरांना भेटायचे आहे"'
                        : session?.language === 'EN'
                        ? 'e.g. "Ramesh Kumar" or "Book an appointment"'
                        : 'e.g. "Ramesh Kumar" ya "Mujhe doctor ko dikhana hai"'
                    }
                    className="w-full pl-3 pr-10 py-2 bg-slate-800 border border-slate-700 rounded-xl text-xs font-medium text-white placeholder-slate-500 outline-none focus:ring-2 focus:ring-amber-400 disabled:opacity-50"
                  />
                  <button
                    type="button"
                    onClick={handleManualMicClick}
                    disabled={loading || !session || session?.status !== 'ACTIVE'}
                    className={`absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition ${
                      callPhase === 'LISTENING' || callPhase === 'USER_SPEAKING' ? 'bg-rose-500 text-white animate-bounce' : callPhase === 'ASSISTANT_SPEAKING' ? 'bg-purple-600 text-white animate-pulse' : 'text-slate-400 hover:text-amber-400'
                    }`}
                    title={callPhase === 'ASSISTANT_SPEAKING' ? "Click to interrupt assistant speech (Barge-In)" : "Click to toggle microphone"}
                  >
                    {callPhase === 'ASSISTANT_SPEAKING' ? <Zap className="w-4 h-4 fill-white" /> : <Mic className="w-4 h-4" />}
                  </button>
                </div>
                <button
                  type="submit"
                  disabled={loading || !session || session?.status !== 'ACTIVE' || !voiceUtterance.trim()}
                  className="w-full py-2 bg-amber-400 hover:bg-amber-300 disabled:opacity-40 text-slate-950 font-black text-xs rounded-xl shadow flex items-center justify-center gap-1.5 transition"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Send Spoken Utterance (Interrupt if Speaking)</span>
                </button>
              </form>

              {/* Sample Voice Hints */}
              <div className="pt-1 text-[10px] text-slate-400 space-y-1">
                <span className="font-bold text-slate-300">Quick Test Utterances:</span>
                <div className="flex flex-wrap gap-1">
                  <button
                    type="button"
                    onClick={() => setVoiceUtterance('Ramesh Kumar')}
                    className="bg-slate-800 hover:bg-slate-700 px-2 py-0.5 rounded text-amber-300"
                  >
                    "Ramesh Kumar" (Name)
                  </button>
                  <button
                    type="button"
                    onClick={() => setVoiceUtterance('Mujhe doctor ko dikhana hai')}
                    className="bg-slate-800 hover:bg-slate-700 px-2 py-0.5 rounded text-amber-300"
                  >
                    "Mujhe doctor ko dikhana hai"
                  </button>
                  <button
                    type="button"
                    onClick={() => setVoiceUtterance('Mujhe saans lene mein bahut dikkat ho rahi hai')}
                    className="bg-rose-950 border border-rose-700 hover:bg-rose-900 px-2 py-0.5 rounded text-rose-300 font-bold"
                  >
                    🚨 "Saans lene mein dikkat"
                  </button>
                  <button
                    type="button"
                    onClick={() => setVoiceUtterance('Seene mein bahut tez dard hai')}
                    className="bg-rose-950 border border-rose-700 hover:bg-rose-900 px-2 py-0.5 rounded text-rose-300 font-bold"
                  >
                    🚨 "Seene mein tez dard"
                  </button>
                  <button
                    type="button"
                    onClick={() => setVoiceUtterance('Galti se emergency bola tha')}
                    className="bg-purple-950 border border-purple-700 hover:bg-purple-900 px-2 py-0.5 rounded text-purple-300 font-bold"
                  >
                    🔄 "Clear Emergency"
                  </button>

                  <button
                    type="button"
                    onClick={() => setVoiceUtterance('Baramati')}
                    className="bg-slate-800 hover:bg-slate-700 px-2 py-0.5 rounded text-amber-300"
                  >
                    "Baramati"
                  </button>
                  <button
                    type="button"
                    onClick={() => setVoiceUtterance('Check in karna hai')}
                    className="bg-slate-800 hover:bg-slate-700 px-2 py-0.5 rounded text-emerald-300"
                  >
                    "Check in karna hai"
                  </button>
                  <button
                    type="button"
                    onClick={() => setVoiceUtterance('Pichhe jao')}
                    className="bg-slate-800 hover:bg-slate-700 px-2 py-0.5 rounded text-slate-300"
                  >
                    "Pichhe jao"
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Physical Keypad Buttons Grid */}
          {inputMode === 'DTMF' && (
            <div className="pt-2 space-y-2">
              <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block text-center">
                Physical Keypad (DTMF Key Fallback)
              </span>
              <div className="grid grid-cols-3 gap-2">
                {keypadLayout.flat().map((key) => (
                  <button
                    key={key}
                    onClick={() => handleKeyPress(key)}
                    disabled={loading || !session || session?.status !== 'ACTIVE'}
                    className="py-3 bg-slate-800 hover:bg-slate-700 active:bg-amber-400 active:text-slate-950 disabled:opacity-40 text-white rounded-xl font-black text-sm border border-slate-700 shadow transition flex flex-col items-center justify-center"
                  >
                    <span>{key}</span>
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Right Column: Real-Time Session Audit & NLU Inspector */}
        <div className="md:col-span-6 space-y-4">
          {/* NLU Metadata Inspector */}
          {lastNlu && (
            <div className="bg-slate-900 text-white p-5 rounded-3xl border border-slate-800 shadow-md space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h4 className="font-extrabold text-amber-400 text-xs flex items-center gap-1.5 uppercase">
                  <Mic className="w-3.5 h-3.5" />
                  Voice NLU Pipeline Inspector
                </h4>
                <span className="bg-emerald-500/20 text-emerald-300 text-[10px] font-mono px-2 py-0.5 rounded border border-emerald-500/30">
                  Confidence: {Math.round(lastNlu.confidence * 100)}%
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="bg-slate-800/80 p-2 rounded-xl">
                  <span className="text-[9px] text-slate-400 uppercase block">Detected Intent</span>
                  <span className="font-extrabold text-amber-300">{lastNlu.intent}</span>
                </div>
                <div className="bg-slate-800/80 p-2 rounded-xl">
                  <span className="text-[9px] text-slate-400 uppercase block">Language</span>
                  <span className="font-extrabold text-sky-300">{lastNlu.detected_language}</span>
                </div>
              </div>

              <div className="bg-slate-800/80 p-2.5 rounded-xl text-xs space-y-1 font-mono">
                <div className="flex justify-between text-[10px] text-slate-400">
                  <span>Raw Utterance:</span>
                  <span className="text-slate-300">"{lastNlu.raw_text}"</span>
                </div>
                <div className="flex justify-between text-[10px] text-slate-400">
                  <span>Normalized Text:</span>
                  <span className="text-slate-300">"{lastNlu.normalized_text}"</span>
                </div>
                {lastNlu.entities && Object.keys(lastNlu.entities).length > 0 && (
                  <div className="border-t border-slate-700/80 pt-1 text-[10px]">
                    <span className="text-amber-300 font-bold">Extracted Entities: </span>
                    <span className="text-emerald-300">{JSON.stringify(lastNlu.entities)}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-3">
            <div className="flex items-center justify-between border-b border-slate-100 pb-2">
              <h3 className="font-black text-slate-900 text-sm flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-sky-700" />
                Backend Session Context Inspector
              </h3>
              {loading && <RefreshCw className="w-4 h-4 text-sky-600 animate-spin" />}
            </div>

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 text-rose-900 rounded-xl text-xs font-bold flex items-start gap-2">
                <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {!session ? (
              <p className="text-xs text-slate-500 font-medium py-4 text-center">
                No active phone call session. Click <strong>CALL JANSETHU</strong> to start continuous voice dialog.
              </p>
            ) : (
              <div className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-2 bg-slate-50 p-3 rounded-2xl border border-slate-200 font-mono">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase">Session ID</span>
                    <p className="font-extrabold text-slate-900">{session.session_id}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase">State Machine</span>
                    <p className="font-extrabold text-sky-700">{session.current_state}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase">Selected Facility</span>
                    <p className="font-bold text-slate-800">{session.selected_facility_id || 'None'}</p>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase">Selected Doctor</span>
                    <p className="font-bold text-slate-800">{session.selected_doctor_id || 'None'}</p>
                  </div>
                </div>

                <div className="border-t border-slate-100 pt-2 space-y-2">
                  <h4 className="font-extrabold text-slate-800 text-xs">Live Call Dialogue Transcript</h4>
                  <div className="max-h-60 overflow-y-auto space-y-2 text-xs pr-1 scrollbar-thin">
                    {callHistory.map((item, idx) => (
                      <div
                        key={idx}
                        className={`p-2.5 rounded-2xl text-xs font-medium ${
                          item.type === 'USER_VOICE'
                            ? 'bg-amber-100 text-amber-950 font-bold ml-4 border border-amber-300'
                            : item.type === 'USER'
                            ? 'bg-sky-100 text-sky-950 font-bold ml-4 border border-sky-300'
                            : 'bg-slate-100 text-slate-800 mr-4 border border-slate-200'
                        }`}
                      >
                        <div className="text-[9px] font-mono text-slate-500 mb-0.5 flex justify-between">
                          <span>{item.type}</span>
                          <span>{item.time}</span>
                        </div>
                        <p>{item.text}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
