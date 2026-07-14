"use client";

import { CheckCircle, AlertCircle, Loader2 } from "lucide-react";

export type Status = "idle" | "saving" | "saved" | "error";

interface StatusBadgeProps {
  status: Status;
  message?: string;
}

export default function StatusBadge({ status, message }: StatusBadgeProps) {
  if (status === "idle") {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 text-gray-600 text-sm font-medium">
        <span className="w-2 h-2 rounded-full bg-gray-400"></span>
        Ready
      </div>
    );
  }

  if (status === "saving") {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-light text-brand text-sm font-medium">
        <Loader2 size={14} className="animate-spin" />
        Saving...
      </div>
    );
  }

  if (status === "saved") {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-green-100 text-green-800 text-sm font-medium">
        <CheckCircle size={14} />
        Saved
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-red-100 text-red-800 text-sm font-medium">
        <AlertCircle size={14} />
        <span>{message || "Error saving"}</span>
      </div>
    );
  }

  return null;
}
