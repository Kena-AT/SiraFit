import { useState, useEffect, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

/**
 * Replaces native window.prompt() with an in-app dialog.
 *
 * Usage (promise-based — awaits the user's answers or null on cancel):
 *
 *   const values = await ask({
 *     title: "Import from GitHub",
 *     description: "Enter your GitHub username.",
 *     fields: [{ key: "username", label: "Username", required: true }],
 *     confirmLabel: "Import",
 *   });
 *   if (!values) return; // cancelled
 */

export interface PromptSelectOption {
  value: string;
  label: string;
}

export interface PromptField {
  key: string;
  label: string;
  placeholder?: string;
  required?: boolean;
  defaultValue?: string;
  type?: "text" | "select";
  /** For type === "select": strings act as both value and label. */
  options?: Array<string | PromptSelectOption>;
}

export interface PromptDialogConfig {
  title: string;
  description?: string;
  confirmLabel?: string;
  fields: PromptField[];
}

export function PromptDialog({
  config,
  resolve,
}: {
  config: PromptDialogConfig;
  resolve: (values: Record<string, string> | null) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>(() =>
    Object.fromEntries(config.fields.map((f) => [f.key, f.defaultValue ?? ""])),
  );
  const firstInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const t = setTimeout(() => firstInputRef.current?.focus(), 50);
    return () => clearTimeout(t);
  }, []);

  const canSubmit = config.fields.every((f) => !f.required || !!values[f.key]?.trim());

  const submit = () => {
    if (!canSubmit) return;
    resolve(values);
  };

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) resolve(null);
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{config.title}</DialogTitle>
          {config.description ? <DialogDescription>{config.description}</DialogDescription> : null}
        </DialogHeader>
        <div className="space-y-3 py-2">
          {config.fields.map((f, i) => (
            <div key={f.key} className="space-y-1.5">
              <label className="text-[10px] font-semibold uppercase text-muted-foreground">
                {f.label}
                {f.required ? " *" : ""}
              </label>
              {f.type === "select" ? (
                <select
                  ref={i === 0 ? (firstInputRef as any) : undefined}
                  value={values[f.key] ?? ""}
                  onChange={(e) => setValues((prev) => ({ ...prev, [f.key]: e.target.value }))}
                  className="h-9 w-full rounded-md border border-input bg-background px-3 text-sm"
                >
                  {(f.options ?? []).map((opt) => {
                    const value = typeof opt === "string" ? opt : opt.value;
                    const label = typeof opt === "string" ? opt : opt.label;
                    return (
                      <option key={value} value={value}>
                        {label}
                      </option>
                    );
                  })}
                </select>
              ) : (
                <Input
                  ref={i === 0 ? firstInputRef : undefined}
                  value={values[f.key] ?? ""}
                  onChange={(e) => setValues((prev) => ({ ...prev, [f.key]: e.target.value }))}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") {
                      e.preventDefault();
                      submit();
                    }
                  }}
                  placeholder={f.placeholder}
                />
              )}
            </div>
          ))}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => resolve(null)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={!canSubmit}>
            {config.confirmLabel ?? "OK"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
