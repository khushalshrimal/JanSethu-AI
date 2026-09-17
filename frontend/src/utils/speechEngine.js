// Browser Speech Recognition & Text-to-Speech Utility for JanSethu AI

export const isSpeechRecognitionSupported = () => {
  return 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window;
};

export const isSpeechSynthesisSupported = () => {
  return 'speechSynthesis' in window;
};

export const createSpeechRecognizer = (lang = 'en') => {
  if (!isSpeechRecognitionSupported()) return null;
  
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = new SpeechRecognition();
  
  recognition.continuous = false;
  recognition.interimResults = true;
  recognition.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
  
  return recognition;
};

export const speakText = (text, lang = 'en') => {
  if (!isSpeechSynthesisSupported() || !text) return;
  
  try {
    window.speechSynthesis.cancel(); // Stop ongoing audio
    
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang === 'hi' ? 'hi-IN' : 'en-IN';
    utterance.rate = 0.95; // Slightly slower for low-literacy clarity
    utterance.pitch = 1.0;
    
    // Pick best matching voice if available
    const voices = window.speechSynthesis.getVoices();
    const targetLang = lang === 'hi' ? 'hi' : 'en';
    const voice = voices.find(v => v.lang.startsWith(targetLang));
    if (voice) {
      utterance.voice = voice;
    }

    window.speechSynthesis.speak(utterance);
  } catch (e) {
    console.warn("Speech Synthesis error:", e);
  }
};
