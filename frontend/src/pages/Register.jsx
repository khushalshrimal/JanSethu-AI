import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { UserPlus, AlertCircle, CheckCircle } from 'lucide-react';

export default function Register() {
  const { register, loading: authLoading } = useAuth();
  const navigate = useNavigate();

  const [formData, setFormData] = useState({
    full_name: '',
    phone: '',
    email: '',
    password: '',
    gender: 'MALE',
    date_of_birth: '1995-01-01',
    pincode: '411001',
    district: 'Pune',
    village: 'Shivajinagar',
    state: 'Maharashtra',
  });

  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    if (!formData.full_name || !formData.phone || !formData.password) {
      setError('Please fill in all required fields (Name, Phone, Password).');
      return;
    }

    setLoading(true);
    const result = await register({
      full_name: formData.full_name,
      phone: formData.phone,
      email: formData.email || undefined,
      password: formData.password,
      role: 'CUSTOMER',
      patient_profile: {
        gender: formData.gender,
        date_of_birth: formData.date_of_birth,
        pincode: formData.pincode,
        district: formData.district,
        village: formData.village,
        state: formData.state,
      },
    });
    setLoading(false);

    if (result.success) {
      navigate('/facilities');
    } else {
      setError(result.error);
    }
  };

  return (
    <div className="max-w-lg mx-auto my-8 px-4">
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-md space-y-6">
        <div className="text-center space-y-1">
          <div className="inline-flex p-3 bg-amber-100 text-amber-900 rounded-2xl mb-2">
            <UserPlus className="w-6 h-6" />
          </div>
          <h2 className="text-2xl font-black text-slate-900">Patient Registration</h2>
          <p className="text-xs text-slate-500 font-medium">
            Create your JanSethu healthcare profile to book OPD doctor appointments
          </p>
        </div>

        {error && (
          <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs font-semibold flex items-start gap-2">
            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block font-bold text-slate-700 uppercase mb-1">Full Name *</label>
              <input
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleChange}
                placeholder="Ramesh Kumar"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-sky-500 font-medium"
                required
              />
            </div>
            <div>
              <label className="block font-bold text-slate-700 uppercase mb-1">Mobile Phone *</label>
              <input
                type="text"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="+919876543299"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-sky-500 font-medium"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block font-bold text-slate-700 uppercase mb-1">Password *</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="••••••••"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-sky-500 font-medium"
                required
              />
            </div>
            <div>
              <label className="block font-bold text-slate-700 uppercase mb-1">Email (Optional)</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="ramesh@example.com"
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-sky-500 font-medium"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block font-bold text-slate-700 uppercase mb-1">Gender</label>
              <select
                name="gender"
                value={formData.gender}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-sky-500 font-medium"
              >
                <option value="MALE">Male</option>
                <option value="FEMALE">Female</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
            <div>
              <label className="block font-bold text-slate-700 uppercase mb-1">Date of Birth</label>
              <input
                type="date"
                name="date_of_birth"
                value={formData.date_of_birth}
                onChange={handleChange}
                className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl outline-none focus:ring-2 focus:ring-sky-500 font-medium"
              />
            </div>
          </div>

          <div className="border-t border-slate-100 pt-3">
            <p className="font-bold text-slate-800 uppercase mb-2 text-[11px]">Location & Address Details</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block font-semibold text-slate-600 mb-1">Pincode</label>
                <input
                  type="text"
                  name="pincode"
                  value={formData.pincode}
                  onChange={handleChange}
                  placeholder="411001"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl outline-none font-medium"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-600 mb-1">District</label>
                <input
                  type="text"
                  name="district"
                  value={formData.district}
                  onChange={handleChange}
                  placeholder="Pune"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl outline-none font-medium"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-600 mb-1">Village / Town</label>
                <input
                  type="text"
                  name="village"
                  value={formData.village}
                  onChange={handleChange}
                  placeholder="Shivajinagar"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl outline-none font-medium"
                />
              </div>
              <div>
                <label className="block font-semibold text-slate-600 mb-1">State</label>
                <input
                  type="text"
                  name="state"
                  value={formData.state}
                  onChange={handleChange}
                  placeholder="Maharashtra"
                  className="w-full px-3 py-2 bg-slate-50 border border-slate-300 rounded-xl outline-none font-medium"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || authLoading}
            className="w-full py-3 bg-amber-400 hover:bg-amber-300 text-slate-950 rounded-xl font-bold text-sm transition shadow-sm flex items-center justify-center gap-2 mt-4"
          >
            {loading || authLoading ? 'Registering Account...' : 'Create Account & Continue'}
          </button>
        </form>

        <div className="text-center text-xs text-slate-500 pt-2 border-t border-slate-100">
          Already have an account?{' '}
          <Link to="/login" className="text-sky-700 font-bold hover:underline">
            Sign In Here
          </Link>
        </div>
      </div>
    </div>
  );
}
