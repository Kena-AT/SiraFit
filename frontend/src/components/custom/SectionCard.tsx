"use client";

import { useState, ReactNode } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

interface SectionCardProps {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}

export default function SectionCard({ title, children, defaultOpen = false }: SectionCardProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="mb-6 border border-border rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 bg-background-secondary hover:bg-background-tertiary transition-colors"
      >
        <h2 className="text-lg font-semibold text-text-primary">{title}</h2>
        <span className="text-text-secondary">
          {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </span>
      </button>
      {isOpen && <div className="p-4 bg-background-primary">{children}</div>}
    </div>
  );
}
