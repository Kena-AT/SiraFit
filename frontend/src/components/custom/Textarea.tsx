"use client";

interface TextareaProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  maxLength?: number;
  rows?: number;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
}

export default function Textarea({
  label,
  value,
  onChange,
  required = false,
  maxLength,
  rows = 3,
  placeholder,
  disabled = false,
  error,
}: TextareaProps) {
  const textareaId = `textarea-${label.replace(/\s+/g, "-").toLowerCase()}`;

  return (
    <div className="space-y-1">
      <label htmlFor={textareaId} className="block text-sm font-medium text-text-primary">
        {label}
        {required && <span className="text-red-600 ml-1">*</span>}
      </label>
      <textarea
        id={textareaId}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        maxLength={maxLength}
        placeholder={placeholder}
        disabled={disabled}
        rows={rows}
        className={`
          w-full px-3 py-2 border rounded-md transition-colors resize-y
          focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent
          disabled:bg-background-secondary disabled:text-text-secondary disabled:cursor-not-allowed
          ${
            error
              ? "border-red-600 bg-red-50"
              : "border-border bg-background-primary text-text-primary"
          }
        `}
      />
      <div className="flex justify-between">
        {maxLength && (
          <span className="text-xs text-text-secondary">
            {value.length} / {maxLength}
          </span>
        )}
        {error && <span className="text-xs text-red-600">{error}</span>}
      </div>
    </div>
  );
}
