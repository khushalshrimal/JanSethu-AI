// Browser Speech Recognition & Text-to-Speech Utility for JanSethu AI

export const isSpeechRecognitionSupported = () => {
  return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
};

export const isSpeechSynthesisSupported = () => {
  return 'speechSynthesis' in window;
};

export const getLocaleCode = (lang = 'en') => {
  if (lang === 'hi') return 'hi-IN';
  if (lang === 'mr') return 'mr-IN';
  return 'en-IN';
};

export const createSpeechRecognizer = (lang = 'en') => {
  if (!isSpeechRecognitionSupported()) return null;
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = getLocaleCode(lang);
  
  return recognition;
};

export const speakText = (text, lang = 'en', onStart = null, onEnd = null) => {
  if (!isSpeechSynthesisSupported() || !text) {
    if (onEnd) onEnd();
    return;
  }
  
  try {
    window.speechSynthesis.cancel(); // Stop ongoing audio playback
    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
    }
    
    // Clean text of markdown/emoji for speech clarity
    const cleanText = text.replace(/[*_~#`[\]()]/g, '').replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}]/gu, '');

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.lang = getLocaleCode(lang);
    utterance.rate = 0.92; // Slightly slower pace for low-literacy clarity
    utterance.pitch = 1.0;

    if (onStart) {
      utterance.onstart = () => onStart();
    }
    
    utterance.onend = () => {
      if (onEnd) onEnd();
    };

    utterance.onerror = (e) => {
      console.warn("Speech Synthesis utterance error:", e);
      if (onEnd) onEnd();
    };
    
    // Select best matching locale voice if available
    const voices = window.speechSynthesis.getVoices();
    const locale = getLocaleCode(lang).toLowerCase();
    const voice = voices.find(v => v.lang.toLowerCase().startsWith(locale) || v.lang.toLowerCase().startsWith(lang.toLowerCase()));
    if (voice) {
      utterance.voice = voice;
    }

    setTimeout(() => {
      window.speechSynthesis.speak(utterance);
    }, 50);
  } catch (e) {
    console.warn("Speech Synthesis error:", e);
    if (onEnd) onEnd();
  }
};
