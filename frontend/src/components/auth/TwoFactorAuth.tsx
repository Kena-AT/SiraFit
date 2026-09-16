"use client";

import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { apiFetch } from "@/lib/api/client";

interface TwoFactorSetupProps {
  onComplete?: () => void;
  onCancel?: () => void;
}

export function TwoFactorSetup({ onComplete, onCancel }: TwoFactorSetupProps) {
  const [step, setStep] = useState<"initial" | "scan" | "verify" | "recovery">("initial");
  const [qrUri, setQrUri] = useState("");
  const [secret, setSecret] = useState("");
  const [recoveryCodes, setRecoveryCodes] = useState<string[]>([]);
  const [verifyCode, setVerifyCode] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSetup = async () => {
    setIsLoading(true);
    setError("");
    try {
      const response = await apiFetch("/api/v1/auth/2fa/setup", {
        method: "POST",
      });
      if (response.ok) {
        const data = await response.json();
        setQrUri(data.qr_uri);
        setSecret(data.secret);
        setRecoveryCodes(data.recovery_codes);
        setStep("scan");
      } else {
        const errData = await response.json();
        setError(errData.detail || "Failed to set up 2FA");
      }
    } catch (err: any) {
      setError(err.message || "Failed to set up 2FA");
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerify = async () => {
    if (!verifyCode || verifyCode.length !== 6) {
      setError("Please enter a 6-digit code");
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      const response = await apiFetch("/api/v1/auth/2fa/verify", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: verifyCode }),
      });
      if (response.ok) {
        setStep("recovery");
      } else {
        const errData = await response.json();
        setError(errData.detail || "Invalid code");
      }
    } catch (err: any) {
      setError(err.message || "Verification failed");
    } finally {
      setIsLoading(false);
    }
  };

  if (step === "initial") {
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium">Set Up Two-Factor Authentication</h3>
          <p className="text-sm text-muted-foreground">
            Add an extra layer of security to your account by enabling 2FA.
          </p>
        </div>
        <div className="bg-muted p-4 rounded-md text-sm">
          <p>
            Once enabled, you'll need to enter a code from your authenticator app each time you log
            in.
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleSetup} disabled={isLoading}>
            {isLoading ? "Setting up..." : "Enable 2FA"}
          </Button>
          {onCancel && (
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
          )}
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
      </div>
    );
  }

  if (step === "scan") {
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium">Scan QR Code</h3>
          <p className="text-sm text-muted-foreground">
            Scan this QR code with your authenticator app (Google Authenticator, Authy, etc.)
          </p>
        </div>
        <div className="flex justify-center p-4 bg-white rounded-lg">
          <img
            src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(qrUri)}`}
            alt="2FA QR Code"
            className="w-48 h-48"
          />
        </div>
        <div>
          <Label>Or enter this code manually:</Label>
          <code className="block mt-1 p-2 bg-muted rounded text-sm font-mono break-all">
            {secret}
          </code>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setStep("verify")}>Next: Verify Code</Button>
          <Button variant="outline" onClick={() => setStep("initial")}>
            Back
          </Button>
        </div>
      </div>
    );
  }

  if (step === "verify") {
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium">Verify Your Code</h3>
          <p className="text-sm text-muted-foreground">
            Enter the 6-digit code from your authenticator app
          </p>
        </div>
        <div className="space-y-2">
          <Label htmlFor="totp-code">Verification Code</Label>
          <Input
            id="totp-code"
            type="text"
            inputMode="numeric"
            pattern="[0-9]*"
            maxLength={6}
            placeholder="000000"
            value={verifyCode}
            onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ""))}
          />
        </div>
        {error && <p className="text-red-500 text-sm">{error}</p>}
        <div className="flex gap-2">
          <Button onClick={handleVerify} disabled={isLoading || verifyCode.length !== 6}>
            {isLoading ? "Verifying..." : "Verify & Enable"}
          </Button>
          <Button variant="outline" onClick={() => setStep("scan")}>
            Back
          </Button>
        </div>
      </div>
    );
  }

  if (step === "recovery") {
    return (
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium">2FA Enabled Successfully!</h3>
          <p className="text-sm text-muted-foreground">
            Save these recovery codes in a safe place. You can use them to access your account if
            you lose your authenticator device.
          </p>
        </div>
        <div className="bg-muted p-4 rounded-md">
          <div className="grid grid-cols-2 gap-2 font-mono text-sm">
            {recoveryCodes.map((code, i) => (
              <div key={i} className="p-1 bg-background rounded">
                {code}
              </div>
            ))}
          </div>
        </div>
        <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-md text-sm">
          <p className="font-medium text-yellow-800 dark:text-yellow-200">
            Important: Each recovery code can only be used once.
          </p>
        </div>
        <Button onClick={onComplete} className="w-full">
          Done
        </Button>
      </div>
    );
  }

  return null;
}

interface TwoFactorVerifyProps {
  tempToken: string;
  onSuccess: () => void;
  onBack?: () => void;
}

export function TwoFactorVerify({ tempToken, onSuccess, onBack }: TwoFactorVerifyProps) {
  const [code, setCode] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleVerify = async () => {
    if (!code || code.length !== 6) {
      setError("Please enter a 6-digit code");
      return;
    }

    setIsLoading(true);
    setError("");
    try {
      const response = await apiFetch("/api/v1/auth/2fa/complete-login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ temp_token: tempToken, code }),
      });
      if (response.ok) {
        onSuccess();
      } else {
        const errData = await response.json();
        setError(errData.detail || "Invalid code");
      }
    } catch (err: any) {
      setError(err.message || "Verification failed");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium">Two-Factor Authentication</h3>
        <p className="text-sm text-muted-foreground">
          Enter the 6-digit code from your authenticator app
        </p>
      </div>
      <div className="space-y-2">
        <Label htmlFor="login-totp-code">Verification Code</Label>
        <Input
          id="login-totp-code"
          type="text"
          inputMode="numeric"
          pattern="[0-9]*"
          maxLength={6}
          placeholder="000000"
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          autoFocus
        />
      </div>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <div className="flex gap-2">
        <Button onClick={handleVerify} disabled={isLoading || code.length !== 6} className="w-full">
          {isLoading ? "Verifying..." : "Verify"}
        </Button>
      </div>
      {onBack && (
        <Button variant="ghost" onClick={onBack} className="w-full">
          Back to login
        </Button>
      )}
    </div>
  );
}

interface TwoFactorStatusProps {
  enabled: boolean;
  recoveryCodesRemaining?: number;
  onDisable?: () => void;
  onSetup?: () => void;
}

export function TwoFactorStatus({
  enabled,
  recoveryCodesRemaining,
  onDisable,
  onSetup,
}: TwoFactorStatusProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-medium">Two-Factor Authentication</h3>
        <p className="text-sm text-muted-foreground">
          {enabled
            ? "2FA is currently enabled on your account."
            : "2FA is not enabled. Enable it for extra security."}
        </p>
      </div>
      {enabled && recoveryCodesRemaining !== undefined && (
        <div className="bg-muted p-3 rounded-md text-sm">
          Recovery codes remaining: <span className="font-medium">{recoveryCodesRemaining}</span>
        </div>
      )}
      <div className="flex gap-2">
        {enabled ? (
          <Button variant="destructive" onClick={onDisable}>
            Disable 2FA
          </Button>
        ) : (
          <Button onClick={onSetup}>Enable 2FA</Button>
        )}
      </div>
    </div>
  );
}
