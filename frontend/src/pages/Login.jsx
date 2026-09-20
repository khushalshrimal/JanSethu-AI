import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LogIn, Phone, Lock, AlertCircle, CheckCircle, ShieldCheck } from 'lucide-react';

export default function Login() {
  const { login, loading: authLoading, error: authError } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [phoneOrEmail, setPhoneOrEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const from = location.state?.from?.pathname || '/facilities';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!phoneOrEmail || !password) {
      setError('Please enter mobile number/email and password.');
      return;
    }

    setLoading(true);
    const result = await login(phoneOrEmail, password);
    setLoading(false);

    if (result.success) {
      navigate(from, { replace: true });
    } else {
      setError(result.error);
    }
  };

  const fillDemoUser = (phone, pass) => {
    setPhoneOrEmail(phone);
    setPassword(pass);
    setError(null);
  };

  return (
    <div className="max-w-md mx-auto my-8 px-4">
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-md space-y-6">
        <div className="text-center space-y-1">
          <div className="inline-flex p-3 bg-sky-100 text-sky-800 rounded-2xl mb-2">
            <LogIn className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-black text-slate-900">Welcome to JanSethu</h2>
          <p className="text-xs text-slate-500 font-medium">
            Sign in to access OPD doctor slots & manage appointments
          </p>
        </div>

        {(error || authError) && (
          <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs font-semibold flex items-start gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error || authError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
              Mobile Number or Email
            </label>
            <div className="relative">
              <Phone className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="text"
                value={phoneOrEmail}
                onChange={(e) => setPhoneOrEmail(e.target.value)}
                placeholder="+919876543210 or user@example.com"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 focus:bg-white outline-none font-medium"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase mb-1">
              Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-900 focus:ring-2 focus:ring-sky-500 focus:bg-white outline-none font-medium"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || authLoading}
            className="w-full py-3 bg-sky-700 hover:bg-sky-800 text-white rounded-xl font-bold text-sm transition shadow-sm flex items-center justify-center gap-2"
          >
            {loading || authLoading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        {/* Demo Fast Fill Helpers */}
        <div className="border-t border-slate-100 pt-4 space-y-2">
          <p className="text-[11px] font-bold text-slate-500 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-sky-600" />
            Testing Accounts Quick Fill:
          </p>
          <div className="grid grid-cols-3 gap-2 text-[10px]">
            <button
              type="button"
              onClick={() => fillDemoUser('+919876543210', 'password123')}
              className="p-2 bg-slate-100 hover:bg-sky-50 hover:border-sky-300 border border-slate-200 rounded-xl font-semibold text-slate-700 text-center"
            >
              Customer
            </button>
            <button
              type="button"
              onClick={() => fillDemoUser('+919876543211', 'password123')}
              className="p-2 bg-slate-100 hover:bg-sky-50 hover:border-sky-300 border border-slate-200 rounded-xl font-semibold text-slate-700 text-center"
            >
              Provider
            </button>
            <button
              type="button"
              onClick={() => fillDemoUser('+919876543212', 'password123')}
              className="p-2 bg-slate-100 hover:bg-sky-50 hover:border-sky-300 border border-slate-200 rounded-xl font-semibold text-slate-700 text-center"
            >
              Admin
            </button>
          </div>
        </div>

        <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
          Don't have an account?{' '}
          <Link to="/register" className="text-sky-700 font-bold hover:underline">
            Register as Patient
          </Link>
        </div>
      </div>
    </div>
  );
}
