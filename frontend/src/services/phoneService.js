import { apiClient } from './api';

export const phoneService = {
  startCallSession: async (callerPhone = '+919876543210') => {
    const response = await apiClient.post('/phone/calls/start', {
      caller_phone: callerPhone,
      channel: 'TELEPHONY_SIMULATOR'
    });
    return response.data;
  },

  sendDtmfInput: async (sessionId, value) => {
    const response = await apiClient.post(`/phone/calls/${sessionId}/input`, {
      input_type: 'DTMF',
      value: String(value)
    });
    return response.data;
  },

  getCallSession: async (sessionId) => {
    const response = await apiClient.get(`/phone/calls/${sessionId}`);
    return response.data;
  },

  endCallSession: async (sessionId) => {
    const response = await apiClient.post(`/phone/calls/${sessionId}/end`);
    return response.data;
  },

  sendVoiceInput: async (sessionId, text, languageHint = null) => {
    const response = await apiClient.post('/phone/voice/input', {
      call_session_id: sessionId,
      text: text,
      language_hint: languageHint
    });
    return response.data;
  },

  understandVoice: async (text, languageHint = null) => {
    const response = await apiClient.post('/phone/voice/understand', {
      text: text,
      language_hint: languageHint
    });
    return response.data;
  },

  ttsVoice: async (text, language = 'hi') => {
    const response = await apiClient.post('/phone/voice/tts', {
      text: text,
      language: language
    });
    return response.data;
  },

  sendConversationMessage: async (sessionId, message, languageHint = 'hi') => {
    const response = await apiClient.post('/conversation/message', {
      session_id: sessionId,
      message: message,
      language_hint: languageHint
    });
    return response.data;
  }
};

export const startCallSession = phoneService.startCallSession;
export const sendDtmfInput = phoneService.sendDtmfInput;
export const getCallSession = phoneService.getCallSession;
export const endCallSession = phoneService.endCallSession;
export const sendVoiceInput = phoneService.sendVoiceInput;
export const understandVoice = phoneService.understandVoice;
export const ttsVoice = phoneService.ttsVoice;
export const sendConversationMessage = phoneService.sendConversationMessage;

