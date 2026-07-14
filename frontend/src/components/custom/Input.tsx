"use client";

interface InputProps {
  label: string;
  type?: "text" | "email" | "tel" | "date" | "url" | "password";
  value: string;
  onChange: (value: string) => void;
  required?: boolean;
  maxLength?: number;
  placeholder?: string;
  disabled?: boolean;
  error?: string;
}

export default function Input({
  label,
  type = "text",
  value,
  onChange,
  required = false,
  maxLength,
  placeholder,
  disabled = false,
  error,
}: InputProps) {
  const inputId = `input-${label.replace(/\s+/g, "-").toLowerCase()}`;

  return (
    <div className="space-y-1">
      <label htmlFor={inputId} className="block text-sm font-medium text-text-primary">
        {label}
        {required && <span className="text-red-600 ml-1">*</span>}
      </label>
      <input
        id={inputId}
        type={type}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        required={required}
        maxLength={maxLength}
        placeholder={placeholder}
        disabled={disabled}
        className={`
          w-full px-3 py-2 border rounded-md transition-colors
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
