import React from 'react';
import { AlertCircle } from 'lucide-react';

export default function DemoBadge({ lang }) {
  return (
    <div className="bg-amber-100/80 border border-amber-300 text-amber-900 px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 shadow-sm">
      <AlertCircle className="w-3.5 h-3.5 text-amber-700 flex-shrink-0" />
      <span>
        {lang === 'hi'
          ? 'प्रोटोटाइप / डेमो डेटा'
          : 'PROTOTYPE / DEMO DATA ONLY'}
      </span>
    </div>
  );
}
