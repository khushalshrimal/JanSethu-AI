import React, { useState } from 'react';
import Header from './components/Header';
import Navigation from './components/Navigation';
import DemoPresetBar from './components/DemoPresetBar';
import SihDemoWizard, { SIH_DEMO_STEPS } from './components/SihDemoWizard';

// Screens
import HomeScreen from './screens/HomeScreen';
import VoiceAssistantScreen from './screens/VoiceAssistantScreen';
import SearchScreen from './screens/SearchScreen';
import FacilityResultsScreen from './screens/FacilityResultsScreen';
import SlotSelectionScreen from './screens/SlotSelectionScreen';
import ConfirmationScreen from './screens/ConfirmationScreen';
import ProviderDashboardScreen from './screens/ProviderDashboardScreen';
import EmergencyScreen from './screens/EmergencyScreen';
import PhoneSimulatorScreen from './screens/PhoneSimulatorScreen';
import TrackAppointmentScreen from './screens/TrackAppointmentScreen';

export default function App() {
  const [lang, setLang] = useState('hi'); // 'hi', 'en', or 'mr'
  const [activeScreen, setActiveScreen] = useState('home');
  const [selectedFacility, setSelectedFacility] = useState(null);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [activeDemo, setActiveDemo] = useState(null);
  
  // SIH Wizard Stepper state
  const [wizardStepIdx, setWizardStepIdx] = useState(0);
  const [isWizardClosed, setIsWizardClosed] = useState(false);

  const handleWizardStepExecute = (stepObj) => {
    if (stepObj.lang) setLang(stepObj.lang);
    if (stepObj.screen) setActiveScreen(stepObj.screen);
    if (stepObj.facility) setSelectedFacility(stepObj.facility);
    if (stepObj.slot) setSelectedSlot(stepObj.slot);
  };

  const handleTriggerDemo = (demoId) => {
    setActiveDemo(demoId);
    if (demoId === 'demo1') {
      setLang('hi');
      setSelectedFacility({
        id: 1,
        name: 'Government Sub-District Hospital, Baramati',
        name_hi: 'सरकारी उप-जिला अस्पताल, बारामती',
        city: 'Baramati',
        area: 'Indapur Road',
        address: 'Opposite ST Stand, Indapur Road, Baramati 413106',
        services: 'General OPD, Pediatrics, Maternity, Emergency',
        contact_phone: '+91-2112-222108'
      });
      setSelectedSlot({
        id: 101,
        facility_id: 1,
        date: 'Tomorrow',
        time: '10:30 AM',
        doctor_name: 'Dr. Sharma',
        department: 'Pediatrics'
      });
      setActiveScreen('confirmation');
    } else if (demoId === 'demo2') {
      setLang('hi');
      setActiveScreen('emergency');
    } else if (demoId === 'demo3') {
      setLang('mr');
      setActiveScreen('voice');
    }
  };

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
        {/* SIH Video Pitch Guided Demo Wizard */}
        <SihDemoWizard
          currentStepIndex={wizardStepIdx}
          setStepIndex={setWizardStepIdx}
          onStepExecute={handleWizardStepExecute}
          isClosed={isWizardClosed}
          setIsClosed={setIsWizardClosed}
        />

        {/* Demo Scenario Preset Switcher */}
        <DemoPresetBar onTriggerDemo={handleTriggerDemo} activeDemo={activeDemo} />

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

        {activeScreen === 'track' && (
          <TrackAppointmentScreen
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

        {activeScreen === 'phone' && (
          <PhoneSimulatorScreen
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
