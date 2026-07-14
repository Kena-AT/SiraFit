"use client";

import { AlertTriangle, XCircle } from "lucide-react";

interface ValidationDisplayProps {
  errors: Record<string, string>;
  onClear?: () => void;
}

export default function ValidationDisplay({ errors, onClear }: ValidationDisplayProps) {
  if (Object.keys(errors).length === 0) {
    return null;
  }

  return (
    <div className="mb-6 bg-red-50 border border-red-600 rounded-lg p-4">
      <div className="flex items-start justify-between mb-2">
        <div className="flex items-center gap-2">
          <AlertTriangle size={20} className="text-red-600" />
          <h3 className="font-semibold text-red-800">Validation Errors</h3>
        </div>
        {onClear && (
          <button
            onClick={onClear}
            className="p-1 text-red-600 hover:text-red-800 transition-colors"
            aria-label="Clear errors"
          >
            <XCircle size={18} />
          </button>
        )}
      </div>
      <ul className="space-y-1 text-red-700">
        {Object.entries(errors).map(([field, message]) => (
          <li key={field} className="flex items-start gap-2 text-sm">
            <span className="text-red-600 mt-0.5">•</span>
            <span>
              <strong className="font-medium">{field}:</strong> {message}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-3 text-sm text-red-600">Please fix the errors above before saving.</p>
    </div>
  );
}
