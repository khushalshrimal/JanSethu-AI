import React, { useState, useEffect } from 'react';
import { Phone, PhoneOff, Mic, Volume2, MessageSquare, Signal, Battery, Play, ShieldAlert } from 'lucide-react';
import DemoBadge from '../components/DemoBadge';
import { speakText } from '../utils/speechEngine';
import axios from 'axios';

export default function PhoneSimulatorScreen({ lang }) {
  const [callState, setCallState] = useState('idle'); // 'idle' | 'calling' | 'connected' | 'ended'
  const [lcdText, setLcdText] = useState('JanSethu Call Channel\nDial 1800-JANSETHU');
  const [currentStep, setCurrentStep] = useState('welcome');
  const [callerPhone, setCallerPhone] = useState('+91-9876543210');
  const [speechInput, setSpeechInput] = useState('');
  const [receivedSms, setReceivedSms] = useState(null);
  const [logs, setLogs] = useState([]);

  const addLog = (msg) => {
    setLogs(prev => [ `[${new Date().toLocaleTimeString()}] ${msg}`, ...prev ]);
  };

  const startCall = async () => {
    setCallState('connected');
    setCurrentStep('welcome');
    setReceivedSms(null);
    addLog(`Initiating phone call from ${callerPhone}...`);

    try {
      const res = await axios.post('http://localhost:8000/api/telephony/voice', {
        Caller: callerPhone,
        Step: 'welcome'
      });
      const data = res.data;
      
      const text = lang === 'hi' ? data.speech_text_hi : data.speech_text;
      setLcdText(`[IVR SYSTEM]\n${text}`);
      speakText(text, lang);
      addLog(`IVR Prompt: "${text}"`);
    } catch (err) {
      console.warn("Backend telephony fallback:", err);
      const fallbackText = lang === 'hi' 
        ? 'जनसेतु में आपका स्वागत है। हिंदी के लिए 1 दबाएं, अंग्रेजी के लिए 2 दबाएं।'
        : 'Welcome to JanSethu. Press 1 for Hindi, Press 2 for English.';
      setLcdText(`[IVR SYSTEM]\n${fallbackText}`);
      speakText(fallbackText, lang);
    }
  };

  const handleKeypadPress = async (digit) => {
    if (callState !== 'connected') return;

    addLog(`Keypad DTMF pressed: '${digit}'`);
    setLcdText(`DTMF Key Pressed: [ ${digit} ]\nProcessing...`);

    try {
      const res = await axios.post('http://localhost:8000/api/telephony/gather', {
        Caller: callerPhone,
        Digits: String(digit),
        Step: currentStep,
        Language: lang
      });
      const data = res.data;
      const text = data.speech_text;
      
      setLcdText(`[IVR RESPONSE]\n${text}`);
      speakText(text, lang);
      addLog(`IVR Response: "${text}"`);

      if (data.sms_sent && data.sms_body) {
        setReceivedSms(data.sms_body);
        addLog(`SMS Delivered: "${data.sms_body}"`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSpokenPhraseSubmit = async (phrase) => {
    const textToSpeak = phrase || speechInput;
    if (!textToSpeak || callState !== 'connected') return;

    addLog(`Caller Spoke: "${textToSpeak}"`);
    setLcdText(`Caller Voice Input:\n"${textToSpeak}"`);

    try {
      const res = await axios.post('http://localhost:8000/api/telephony/gather', {
        Caller: callerPhone,
        SpeechResult: textToSpeak,
        Language: lang
      });
      const data = res.data;
      const text = data.speech_text;

      setLcdText(`[IVR RESPONSE]\n${text}`);
      speakText(text, lang);
      addLog(`IVR Response: "${text}"`);

      if (data.sms_sent && data.sms_body) {
        setReceivedSms(data.sms_body);
        addLog(`SMS Delivered: "${data.sms_body}"`);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const endCall = () => {
    setCallState('ended');
    setLcdText('Call Ended\nThank you for using JanSethu AI');
    addLog('Call terminated.');
    setTimeout(() => {
      setCallState('idle');
      setLcdText('JanSethu Call Channel\nDial 1800-JANSETHU');
    }, 2000);
  };

  return (
    <div className="space-y-6 pb-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-extrabold text-slate-900 flex items-center gap-2">
            <Phone className="w-6 h-6 text-sky-600" />
            {lang === 'hi' ? 'कीपैड फोन / वॉइस कॉल चैनल' : 'Keypad Phone IVR Simulator'}
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {lang === 'hi'
              ? 'बिना स्मार्टफोन या इंटरनेट वाले उपयोगकर्ताओं के लिए नॉर्मल फोन कॉल सपोर्ट'
              : 'Interactive feature phone simulator testing IVR webhooks & SMS'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Main Grid: Keypad Phone Mockup + Call Logs */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        
        {/* KEYPAD FEATURE PHONE MOCKUP CONTAINER */}
        <div className="bg-slate-900 text-white rounded-3xl p-6 shadow-2xl border-4 border-slate-800 max-w-sm mx-auto w-full space-y-5 relative">
          
          {/* Top Speaker & Status Bar */}
          <div className="flex items-center justify-between text-[10px] text-slate-400 font-mono border-b border-slate-800 pb-2">
            <span className="flex items-center gap-1"><Signal className="w-3 h-3 text-emerald-400" /> 4G VOLTE</span>
            <span className="font-bold text-amber-300">JanSethu Telephony</span>
            <span className="flex items-center gap-1">100% <Battery className="w-3 h-3 text-emerald-400" /></span>
          </div>

          {/* Keypad Phone LCD Display */}
          <div className="bg-emerald-950/80 border-2 border-emerald-500/60 p-4 rounded-2xl min-h-[140px] flex flex-col justify-between font-mono shadow-inner text-emerald-300">
            <div className="text-[10px] uppercase font-bold tracking-wider text-emerald-400 border-b border-emerald-800/60 pb-1 flex justify-between">
              <span>{callState === 'connected' ? '🔴 CALL IN PROGRESS' : 'STATUS: READY'}</span>
              <span>1800-JANSETHU</span>
            </div>
            
            <p className="text-xs font-bold leading-relaxed whitespace-pre-line py-2 text-white">
              {lcdText}
            </p>

            <div className="text-[9px] text-emerald-400/80 flex justify-between pt-1 border-t border-emerald-800/60">
              <span>[1] Hindi</span>
              <span>[2] English</span>
              <span>[*] Options</span>
            </div>
          </div>

          {/* Call Control Green/Red Buttons */}
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={startCall}
              disabled={callState === 'connected'}
              className={`py-3 rounded-2xl font-black text-xs shadow flex items-center justify-center gap-2 transition active:scale-95 ${
                callState === 'connected'
                  ? 'bg-slate-800 text-slate-600 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-500 text-white animate-pulse'
              }`}
            >
              <Phone className="w-4 h-4" />
              <span>{lang === 'hi' ? 'कॉल शुरू करें' : 'START CALL'}</span>
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
              <span>{lang === 'hi' ? 'कॉल काटें' : 'END CALL'}</span>
            </button>
          </div>

          {/* Keypad Digits Grid (0-9, *, #) */}
          <div className="grid grid-cols-3 gap-2 text-center pt-2">
            {['1', '2', '3', '4', '5', '6', '7', '8', '9', '*', '0', '#'].map(digit => (
              <button
                key={digit}
                onClick={() => handleKeypadPress(digit)}
                className="bg-slate-800 hover:bg-slate-700 active:bg-sky-600 text-white font-mono font-extrabold text-lg py-3 rounded-xl border border-slate-700 shadow transition transform active:scale-95"
              >
                {digit}
              </button>
            ))}
          </div>

          {/* Simulated Spoken Phrase Quick Bar */}
          <div className="pt-2 space-y-2 border-t border-slate-800">
            <div className="text-[10px] font-bold text-slate-400 uppercase">
              {lang === 'hi' ? 'कॉल में बोलें (सिम्युलेटेड वॉइस):' : 'Speak into Phone Mic:'}
            </div>
            <div className="grid grid-cols-1 gap-1.5">
              {[
                { en: 'I need a fever doctor tomorrow in Sanganer', hi: 'मुझे कल सांगानेर में डॉक्टर दिखाना है' },
                { en: 'Is there a maternity ward in Malviya Nagar?', hi: 'क्या मालवीय नगर में प्रसूति वार्ड है?' }
              ].map((p, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSpokenPhraseSubmit(lang === 'hi' ? p.hi : p.en)}
                  className="bg-slate-800 hover:bg-sky-900 border border-slate-700 text-slate-200 text-[11px] font-medium p-2 rounded-xl text-left transition"
                >
                  🗣️ "{lang === 'hi' ? p.hi : p.en}"
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: SMS INBOX & TELEPHONY LOGS */}
        <div className="space-y-4">
          
          {/* SMS Notification Banner */}
          {receivedSms && (
            <div className="bg-amber-100 border-2 border-amber-400 text-amber-950 p-4 rounded-3xl shadow-lg space-y-1 animate-bounce">
              <div className="flex items-center justify-between text-xs font-extrabold text-amber-900">
                <span className="flex items-center gap-1.5">
                  <MessageSquare className="w-4 h-4 text-amber-700" />
                  INCOMING SMS RECEIVED
                </span>
                <span>To: {callerPhone}</span>
              </div>
              <p className="text-xs font-mono font-bold text-amber-950 pt-1">
                "{receivedSms}"
              </p>
            </div>
          )}

          {/* Telephony Architecture Overview */}
          <div className="bg-white p-5 rounded-3xl border border-slate-200 shadow-sm space-y-3">
            <h3 className="font-extrabold text-slate-900 text-sm flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-sky-600" />
              {lang === 'hi' ? 'टेलीफोनी आर्किटेक्चर एवं क्रेडेंशियल' : 'Telephony Architecture & Setup'}
            </h3>

            <div className="text-xs text-slate-600 space-y-2 leading-relaxed">
              <p>
                <strong>Universal Telephony Webhook:</strong> Phone calls hit <code className="bg-slate-100 text-slate-800 px-1 py-0.5 rounded font-mono">POST /api/telephony/voice</code> which executes TwiML / Voice XML against the <strong>same SQLite database</strong>.
              </p>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1 font-mono text-[11px]">
                <div>• Twilio Account SID: <span className="text-slate-400">TWILIO_ACCOUNT_SID</span></div>
                <div>• Twilio Auth Token: <span className="text-slate-400">TWILIO_AUTH_TOKEN</span></div>
                <div>• Twilio Phone Number: <span className="text-slate-400">TWILIO_PHONE_NUMBER</span></div>
                <div>• Exotel SID: <span className="text-slate-400">EXOTEL_SID</span></div>
              </div>
              <p className="text-[11px] text-slate-500 italic">
                *Mock mode allows 100% full testing without paid telephony credentials.
              </p>
            </div>
          </div>

          {/* Telephony Call Console Log */}
          <div className="bg-slate-950 text-slate-300 p-4 rounded-3xl font-mono text-[11px] space-y-2 border border-slate-800 shadow-inner max-h-[260px] overflow-y-auto">
            <div className="text-xs font-bold text-amber-400 border-b border-slate-800 pb-1 flex justify-between">
              <span>TELEPHONY REALTIME CONSOLE</span>
              <span>{logs.length} Events</span>
            </div>
            {logs.length === 0 ? (
              <div className="text-slate-600 py-4 text-center">Click 'START CALL' on the phone mockup to test IVR call flow.</div>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className="leading-tight text-slate-300">
                  {log}
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
