import React, { useState } from 'react';
import Header from './components/Header';
import Navigation from './components/Navigation';

// Screens
import HomeScreen from './screens/HomeScreen';
import VoiceAssistantScreen from './screens/VoiceAssistantScreen';
import SearchScreen from './screens/SearchScreen';
import FacilityResultsScreen from './screens/FacilityResultsScreen';
import SlotSelectionScreen from './screens/SlotSelectionScreen';
import ConfirmationScreen from './screens/ConfirmationScreen';
import ProviderDashboardScreen from './screens/ProviderDashboardScreen';
import EmergencyScreen from './screens/EmergencyScreen';

export default function App() {
  const [lang, setLang] = useState('hi'); // 'hi' or 'en'
  const [activeScreen, setActiveScreen] = useState('home');
  const [selectedFacility, setSelectedFacility] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 flex flex-col font-sans selection:bg-sky-500 selection:text-white pb-24">
      {/* Header */}
      <Header
        lang={lang}
        setLang={setLang}
        activeScreen={activeScreen}
        setActiveScreen={setActiveScreen}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-2xl w-full mx-auto p-4 sm:p-6">
        {activeScreen === 'home' && (
          <HomeScreen
            setActiveScreen={setActiveScreen}
            lang={lang}
          />
        )}

        {activeScreen === 'voice' && (
          <VoiceAssistantScreen
            setActiveScreen={setActiveScreen}
            setSelectedFacility={setSelectedFacility}
            lang={lang}
          />
        )}

        {activeScreen === 'search' && (
          <SearchScreen
            setActiveScreen={setActiveScreen}
            setSelectedFacility={setSelectedFacility}
            lang={lang}
          />
        )}

        {activeScreen === 'facilities' && (
          <FacilityResultsScreen
            setActiveScreen={setActiveScreen}
            setSelectedFacility={setSelectedFacility}
            lang={lang}
          />
        )}

        {activeScreen === 'slots' && (
          <SlotSelectionScreen
            selectedFacility={selectedFacility}
            setSelectedSlot={setSelectedSlot}
            setActiveScreen={setActiveScreen}
            lang={lang}
          />
        )}

        {activeScreen === 'confirmation' && (
          <ConfirmationScreen
            selectedSlot={selectedSlot}
            setActiveScreen={setActiveScreen}
            lang={lang}
          />
        )}

        {activeScreen === 'dashboard' && (
          <ProviderDashboardScreen
            lang={lang}
          />
        )}

        {activeScreen === 'emergency' && (
          <EmergencyScreen
            lang={lang}
          />
        )}
      </main>

      {/* Mobile-First Navigation Bar */}
      <Navigation
        activeScreen={activeScreen}
        setActiveScreen={setActiveScreen}
        lang={lang}
      />
    </div>
  );
}
