import React, { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tag } from "@/components/sirafit/bits";
import {
  validatePlatformSession,
  importSessionJobs,
  getUserSessions,
  deleteStoredSession,
} from "@/lib/api/jobs";
import type { UserSessionRecord, SessionImportPayload } from "@/types/job";

interface SessionImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImportStarted: (importId: string) => void;
}

export function SessionImportModal({
  isOpen,
  onClose,
  onImportStarted,
}: SessionImportModalProps) {
  const [platform, setPlatform] = useState<"linkedin" | "indeed">("linkedin");
  const [cookieInput, setCookieInput] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [consentConfirmed, setConsentConfirmed] = useState(false);
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<{
    valid: boolean;
    message: string;
  } | null>(null);
  const [importing, setImporting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [storedSessions, setStoredSessions] = useState<UserSessionRecord[]>([]);
  const [deletingSession, setDeletingSession] = useState(false);

  useEffect(() => {
    if (isOpen) {
      loadStoredSessions();
      setValidationResult(null);
      setErrorMessage(null);
    } else {
      // Clear sensitive inputs from memory when modal closes
      setCookieInput("");
      setConsentConfirmed(false);
      setValidationResult(null);
      setErrorMessage(null);
    }
  }, [isOpen]);

  const loadStoredSessions = async () => {
    try {
      const sessions = await getUserSessions();
      setStoredSessions(sessions);
    } catch {
      // Ignore background load failures
    }
  };

  if (!isOpen) return null;

  const currentStoredSession = storedSessions.find((s) => s.platform === platform);

  const parseCookies = (raw: string): Record<string, string> => {
    const trimmed = raw.trim();
    if (!trimmed) return {};

    // Check if JSON format
    if (trimmed.startsWith("{") && trimmed.endsWith("}")) {
      try {
        const parsed = JSON.parse(trimmed);
        if (typeof parsed === "object" && parsed !== null) {
          const res: Record<string, string> = {};
          for (const [k, v] of Object.entries(parsed)) {
            res[String(k)] = String(v);
          }
          return res;
        }
      } catch {
        // Fall back to semicolon parsing
      }
    }

    // Standard cookie string format: key=value; key2=value2
    const cookies: Record<string, string> = {};
    const parts = trimmed.split(";");
    for (const part of parts) {
      const eqIdx = part.indexOf("=");
      if (eqIdx !== -1) {
        const key = part.slice(0, eqIdx).trim();
        const val = part.slice(eqIdx + 1).trim();
        if (key) {
          cookies[key] = val;
        }
      }
    }
    return cookies;
  };

  const buildPayload = (): SessionImportPayload => {
    const cookies = parseCookies(cookieInput);
    return {
      cookies,
      consent_confirmed: consentConfirmed,
    };
  };

  const handleValidate = async () => {
    setErrorMessage(null);
    const cookies = parseCookies(cookieInput);
    if (Object.keys(cookies).length === 0) {
      setErrorMessage("Please enter at least one session cookie.");
      return;
    }

    setValidating(true);
    setValidationResult(null);
    try {
      const res = await validatePlatformSession(platform, buildPayload());
      setValidationResult(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Session validation failed.";
      setValidationResult({
        valid: false,
        message: msg,
      });
    } finally {
      setValidating(false);
    }
  };

  const handleImport = async () => {
    setErrorMessage(null);
    if (!consentConfirmed) {
      setErrorMessage("You must confirm consent before importing.");
      return;
    }

    const cookies = parseCookies(cookieInput);
    if (Object.keys(cookies).length === 0 && !currentStoredSession) {
      setErrorMessage(
        "Please enter session cookies or select a platform with an active stored session.",
      );
      return;
    }

    setImporting(true);
    try {
      const payload = buildPayload();
      const res = await importSessionJobs(platform, payload);

      // Immediately clear sensitive cookie input
      setCookieInput("");

      if (res.import_record?.id) {
        onImportStarted(res.import_record.id);
        onClose();
      } else {
        setErrorMessage("Import initiated but received no tracking record.");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to start session import.";
      setErrorMessage(msg);
    } finally {
      setImporting(false);
    }
  };

  const handleDeleteSession = async () => {
    setDeletingSession(true);
    try {
      await deleteStoredSession(platform);
      await loadStoredSessions();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to delete stored session.";
      setErrorMessage(msg);
    } finally {
      setDeletingSession(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="relative w-full max-w-xl rounded-xl border border-border bg-card p-6 shadow-2xl">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <div>
            <h2 className="text-lg font-semibold text-foreground">
              Import Saved Jobs via Authenticated Session
            </h2>
            <p className="text-xs text-muted-foreground mt-0.5">
              Securely discover your saved jobs from supported platforms.
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
          >
            ✕
          </button>
        </div>

        <div className="mt-4 space-y-4">
          {/* Platform Selector */}
          <div>
            <label className="text-xs font-semibold text-foreground uppercase tracking-wider">
              Target Platform
            </label>
            <div className="mt-1.5 flex gap-2">
              <button
                type="button"
                onClick={() => {
                  setPlatform("linkedin");
                  setValidationResult(null);
                }}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                  platform === "linkedin"
                    ? "border-primary bg-primary/10 text-primary ring-1 ring-primary"
                    : "border-border bg-background text-muted-foreground hover:bg-muted"
                }`}
              >
                LinkedIn
              </button>
              <button
                type="button"
                onClick={() => {
                  setPlatform("indeed");
                  setValidationResult(null);
                }}
                className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                  platform === "indeed"
                    ? "border-primary bg-primary/10 text-primary ring-1 ring-primary"
                    : "border-border bg-background text-muted-foreground hover:bg-muted"
                }`}
              >
                Indeed
              </button>
            </div>
          </div>

          {/* Stored Session Status */}
          {currentStoredSession ? (
            <div className="flex items-center justify-between rounded-lg border border-border bg-muted/40 p-3 text-xs">
              <div>
                <span className="font-semibold text-foreground">Stored Session Active</span>
                <p className="text-muted-foreground">
                  Saved on {new Date(currentStoredSession.stored_at).toLocaleDateString()}
                  {currentStoredSession.last_used_at &&
                    ` · Last used ${new Date(currentStoredSession.last_used_at).toLocaleDateString()}`}
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="h-7 text-xs text-destructive hover:bg-destructive/10"
                onClick={handleDeleteSession}
                disabled={deletingSession}
              >
                {deletingSession ? "Deleting..." : "Delete Session"}
              </Button>
            </div>
          ) : null}

          {/* Security & Privacy Notice */}
          <div className="rounded-lg border border-amber-500/20 bg-amber-500/10 p-3 text-xs text-amber-900 dark:text-amber-200">
            <div className="font-semibold flex items-center gap-1.5 mb-1">
              <span>Security & Consent Notice</span>
            </div>
            <ul className="list-disc pl-4 space-y-1 text-[11px] text-amber-800 dark:text-amber-300">
              <li>Credentials are encrypted using AES-128-CBC at rest and decrypted only in worker memory.</li>
              <li>SiraFit accesses only your authorized saved jobs; credentials are never exposed in API responses.</li>
              <li>Platform Terms of Service may regulate automated access; use only with your own personal account.</li>
            </ul>
          </div>

          {/* Cookie Input */}
          <div>
            <div className="flex items-center justify-between">
              <label className="text-xs font-semibold text-foreground uppercase tracking-wider">
                Session Cookie String or JSON
              </label>
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-xs text-primary hover:underline"
              >
                {showPassword ? "Hide" : "Show"}
              </button>
            </div>
            <div className="mt-1.5">
              <Input
                type={showPassword ? "text" : "password"}
                value={cookieInput}
                onChange={(e) => setCookieInput(e.target.value)}
                placeholder={
                  platform === "linkedin"
                    ? 'li_at=AQED...; JSESSIONID="ajax:..."'
                    : "CSRF=...; CTK=..."
                }
                className="font-mono text-xs"
              />
            </div>
            <p className="mt-1 text-[11px] text-muted-foreground">
              {platform === "linkedin"
                ? "Provide your authenticated LinkedIn cookies (`li_at`, `JSESSIONID`)."
                : "Provide your authenticated Indeed cookies (`CTK`, `CSRF`)."}
            </p>
          </div>

          {/* Consent Checkbox */}
          <label className="flex items-start gap-2.5 text-xs text-foreground cursor-pointer">
            <input
              type="checkbox"
              checked={consentConfirmed}
              onChange={(e) => setConsentConfirmed(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-border"
            />
            <span>
              I confirm that I am authorized to access this account and consent to SiraFit discovering my saved jobs.
            </span>
          </label>

          {/* Validation Result Feedback */}
          {validationResult && (
            <div
              className={`rounded-lg border p-3 text-xs ${
                validationResult.valid
                  ? "border-emerald-500/20 bg-emerald-500/10 text-emerald-800 dark:text-emerald-200"
                  : "border-destructive/20 bg-destructive/10 text-destructive"
              }`}
            >
              <div className="font-semibold">
                {validationResult.valid ? "Validation Succeeded" : "Validation Failed"}
              </div>
              <p className="text-[11px] mt-0.5">{validationResult.message}</p>
            </div>
          )}

          {/* Error Message */}
          {errorMessage && (
            <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-xs text-destructive">
              {errorMessage}
            </div>
          )}
        </div>

        {/* Modal Actions */}
        <div className="mt-6 flex items-center justify-end gap-2 border-t border-border pt-4">
          <Button variant="outline" size="sm" onClick={onClose} disabled={importing || validating}>
            Cancel
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={handleValidate}
            disabled={validating || importing || !cookieInput.trim()}
          >
            {validating ? "Validating..." : "Validate Session"}
          </Button>
          <Button
            size="sm"
            onClick={handleImport}
            disabled={importing || validating || !consentConfirmed || (!cookieInput.trim() && !currentStoredSession)}
          >
            {importing ? "Queueing..." : "Start Saved-Jobs Import"}
          </Button>
        </div>
      </div>
    </div>
  );
}
