import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Navbar from './components/layout/Navbar';
import Footer from './components/layout/Footer';

import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Facilities from './pages/Facilities';
import FacilityDetails from './pages/FacilityDetails';
import DoctorDetails from './pages/DoctorDetails';
import BookingConfirmation from './pages/BookingConfirmation';
import MyAppointments from './pages/MyAppointments';
import PhoneSimulator from './pages/PhoneSimulator';
import ProviderDashboard from './pages/provider/ProviderDashboard';
import AdminConsole from './pages/admin/AdminConsole';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="min-h-screen bg-slate-50 text-slate-900 flex flex-col font-sans">
          <Navbar />

          <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Navigate to="/phone-simulator" replace />} />
              <Route path="/register" element={<Navigate to="/phone-simulator" replace />} />
              <Route path="/facilities" element={<Facilities />} />
              <Route path="/facilities/:id" element={<FacilityDetails />} />
              <Route path="/booking" element={<DoctorDetails />} />
              <Route path="/confirmation" element={<BookingConfirmation />} />
              <Route path="/my-appointments" element={<MyAppointments />} />
              <Route path="/phone-simulator" element={<PhoneSimulator />} />
              <Route path="/provider" element={<ProviderDashboard />} />
              <Route path="/admin" element={<AdminConsole />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>

          <Footer />
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}
