"use client";

import { useState } from "react";
import { Trash2, ChevronDown, ChevronUp } from "lucide-react";
import Input from "./Input";
import Textarea from "./Textarea";

interface ArrayItemProps<T extends object> {
  item: T;
  index: number;
  onChange: (field: keyof T, value: any) => void;
  onRemove: () => void;
  fields: Array<{
    label: string;
    name: keyof T;
    required?: boolean;
    maxLength?: number;
    type?: "text" | "email" | "date" | "checkbox" | "textarea";
    rows?: number;
    placeholder?: string;
  }>;
}

export default function ArrayItem<T extends object>({
  item,
  index,
  onChange,
  onRemove,
  fields,
}: ArrayItemProps<T>) {
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className="mb-4 border border-border rounded-lg overflow-hidden">
      <div className="flex items-center justify-between p-4 bg-background-secondary">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="text-text-secondary hover:text-text-primary transition-colors"
          >
            {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
          <span className="font-medium text-text-primary">Item #{index + 1}</span>
        </div>
        <button
          onClick={onRemove}
          className="p-1 text-text-secondary hover:text-red-600 transition-colors"
          aria-label="Remove item"
        >
          <Trash2 size={18} />
        </button>
      </div>

      {isOpen && (
        <div className="p-4 bg-background-primary">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {fields.map((field) => {
              const value = item[field.name] as any;

              if (field.type === "textarea") {
                return (
                  <div key={field.name as string} className="md:col-span-2">
                    <Textarea
                      label={field.label}
                      value={value || ""}
                      onChange={(newValue) => onChange(field.name, newValue)}
                      required={field.required}
                      maxLength={field.maxLength}
                      rows={field.rows || 3}
                      placeholder={field.placeholder}
                    />
                  </div>
                );
              }

              if (field.type === "checkbox") {
                return (
                  <div key={field.name as string} className="md:col-span-2">
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={value || false}
                        onChange={(e) => onChange(field.name, e.target.checked)}
                        className="rounded border-border text-brand focus:ring-brand"
                      />
                      <span className="text-sm font-medium text-text-primary">{field.label}</span>
                    </label>
                  </div>
                );
              }

              return (
                <div key={field.name as string}>
                  <Input
                    label={field.label}
                    type={field.type || "text"}
                    value={value || ""}
                    onChange={(newValue) => onChange(field.name, newValue)}
                    required={field.required}
                    maxLength={field.maxLength}
                    placeholder={field.placeholder}
                  />
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
