import React from 'react';
import { Home, Mic, Search, Building2, LayoutDashboard, PhoneCall, Smartphone, Ticket } from 'lucide-react';

export default function Navigation({ activeScreen, setActiveScreen, lang }) {
  const navItems = [
    {
      id: 'home',
      label: lang === 'hi' ? 'होम' : lang === 'mr' ? 'होम' : 'Home',
      icon: Home,
    },
    {
      id: 'voice',
      label: lang === 'hi' ? 'आवाज सहायक' : lang === 'mr' ? 'व्हॉइस सहाय्यक' : 'Voice Assistant',
      icon: Mic,
      highlight: true
    },
    {
      id: 'phone',
      label: lang === 'hi' ? 'कीपैड फोन' : lang === 'mr' ? 'कीपॅड फोन' : 'Keypad Call',
      icon: Smartphone,
    },
    {
      id: 'track',
      label: lang === 'hi' ? 'ट्रैक' : lang === 'mr' ? 'ट्रॅक' : 'Track',
      icon: Ticket,
    },
    {
      id: 'dashboard',
      label: lang === 'hi' ? 'डैशबोर्ड' : lang === 'mr' ? 'डॅशबोर्ड' : 'Dashboard',
      icon: LayoutDashboard,
    },
    {
      id: 'emergency',
      label: lang === 'hi' ? 'आपातकाल' : lang === 'mr' ? 'आणीबाणी' : 'Emergency',
      icon: PhoneCall,
      emergency: true
    }
  ];

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 shadow-lg z-50 px-2 py-1">
      <div className="max-w-md mx-auto flex items-center justify-around">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeScreen === item.id;
          
          if (item.highlight) {
            return (
              <button
                key={item.id}
                onClick={() => setActiveScreen(item.id)}
                className={`flex flex-col items-center justify-center p-2 rounded-2xl -mt-5 shadow-lg transition active:scale-95 ${
                  isActive 
                    ? 'bg-amber-400 text-slate-950 ring-4 ring-sky-700 font-extrabold' 
                    : 'bg-sky-600 text-white hover:bg-sky-700'
                }`}
                aria-label={item.label}
              >
                <Icon className="w-7 h-7" />
                <span className="text-[10px] font-bold mt-0.5 px-1">{item.label}</span>
              </button>
            );
          }

          return (
            <button
              key={item.id}
              onClick={() => setActiveScreen(item.id)}
              className={`flex flex-col items-center justify-center py-1.5 px-1.5 rounded-xl transition ${
                isActive
                  ? 'text-sky-700 font-bold bg-sky-50'
                  : item.emergency
                  ? 'text-rose-600 font-semibold hover:bg-rose-50'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              <Icon className={`w-5 h-5 ${item.emergency ? 'text-rose-600 animate-pulse' : ''}`} />
              <span className="text-[10px] tracking-tight mt-0.5">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
