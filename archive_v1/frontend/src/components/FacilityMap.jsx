import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Phone, Calendar, ArrowRight, ExternalLink, Navigation } from 'lucide-react';
import DemoBadge from './DemoBadge';

// Fix Leaflet marker icon assets in Vite build
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

// Component to handle map view center updates
function ChangeView({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);
  return null;
}

export default function FacilityMap({ facilities = [], selectedFacility, onSelectFacility, lang }) {
  // Default center: Jaipur (26.8549° N, 75.8243° E)
  const defaultCenter = [26.8206, 75.8075];
  
  const activeCenter = selectedFacility 
    ? [selectedFacility.latitude, selectedFacility.longitude]
    : facilities.length > 0
    ? [facilities[0].latitude, facilities[0].longitude]
    : defaultCenter;

  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-md p-4 space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-2.5">
        <div>
          <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
            <Navigation className="w-5 h-5 text-sky-600" />
            {lang === 'hi' ? 'ओपनस्ट्रीटमैप लाइव व्यू' : 'OpenStreetMap Facility Map'}
          </h3>
          <p className="text-xs text-slate-500">
            {lang === 'hi'
              ? 'डेटाबेस से सत्यापित स्वास्थ्य केंद्रों के जीपीएस स्थान'
              : 'GPS markers for government hospitals & PHCs from database'}
          </p>
        </div>
        <DemoBadge lang={lang} />
      </div>

      {/* Map Container Container */}
      <div className="w-full h-[360px] sm:h-[420px] rounded-2xl overflow-hidden border border-slate-300 relative shadow-inner z-0">
        <MapContainer
          center={activeCenter}
          zoom={12}
          scrollWheelZoom={false}
          className="w-full h-full"
        >
          <ChangeView center={activeCenter} zoom={13} />
          
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />

          {facilities.map((fac) => (
            <Marker
              key={fac.id}
              position={[fac.latitude, fac.longitude]}
            >
              <Popup className="custom-leaflet-popup">
                <div className="p-1 space-y-2 text-slate-900 max-w-[240px]">
                  <div>
                    <span className="bg-sky-100 text-sky-900 font-extrabold text-[9px] uppercase px-2 py-0.5 rounded-full">
                      {fac.facility_type}
                    </span>
                    <h4 className="font-extrabold text-sm text-slate-900 mt-1 leading-tight">
                      {lang === 'hi' && fac.name_hi ? fac.name_hi : fac.name}
                    </h4>
                    <p className="text-[11px] text-slate-600 mt-0.5">
                      📍 {fac.area}, {fac.city}
                    </p>
                  </div>

                  <div className="text-[11px] text-slate-600 font-medium">
                    📞 {fac.contact_phone}
                  </div>

                  <div className="pt-1 flex flex-col gap-1.5 border-t border-slate-100">
                    <button
                      onClick={() => onSelectFacility(fac)}
                      className="w-full bg-sky-700 hover:bg-sky-800 text-white font-extrabold text-[11px] py-2 px-3 rounded-xl shadow flex items-center justify-center gap-1.5 transition"
                    >
                      <Calendar className="w-3.5 h-3.5 text-amber-300" />
                      <span>{lang === 'hi' ? 'स्लॉट बुक करें' : 'View Available Slots'}</span>
                    </button>

                    <a
                      href={`https://www.google.com/maps/dir/?api=1&destination=${fac.latitude},${fac.longitude}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="w-full bg-slate-100 hover:bg-slate-200 text-slate-800 font-bold text-[10px] py-1.5 px-3 rounded-lg flex items-center justify-center gap-1 transition text-center"
                    >
                      <ExternalLink className="w-3 h-3 text-sky-600" />
                      <span>{lang === 'hi' ? 'दिशा-निर्देश प्राप्त करें (Directions)' : 'Open GPS Directions'}</span>
                    </a>
                  </div>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>

      {/* Facility Pin Legend */}
      <div className="flex flex-wrap items-center justify-between text-xs text-slate-600 bg-slate-50 p-2.5 rounded-xl border border-slate-200">
        <span className="font-bold text-slate-700">📍 Marker Pins:</span>
        <div className="flex flex-wrap items-center gap-3 text-[11px]">
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 bg-blue-600 rounded-full"></span>
            District Hospitals
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 bg-emerald-600 rounded-full"></span>
            PHC / CHC
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2.5 h-2.5 bg-amber-500 rounded-full"></span>
            Mobile Van
          </span>
        </div>
      </div>
    </div>
  );
}
