import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState, useRef } from "react";
import { AuthShell } from "@/components/sirafit/shell";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/verify-email")({
  head: () => ({ meta: [{ title: "Verify email · SiraFit" }] }),
  component: VerifyEmailPage,
});

function VerifyEmailPage() {
  const navigate = useNavigate();
  const [code, setCode] = useState(["", "", "", "", "", ""]);
  const [isLoading, setIsLoading] = useState(false);
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

  const handleChange = (index: number, value: string) => {
    if (!/^[0-9]?$/.test(value)) return;
    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);

    // Auto-advance focus
    if (value && index < 5) {
      inputsRef.current[index + 1]?.focus();
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Backspace" && !code[index] && index > 0) {
      inputsRef.current[index - 1]?.focus();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code.some((digit) => !digit)) return;

    setIsLoading(true);
    // Simulate verification delay since backend doesn't have this yet
    setTimeout(() => {
      setIsLoading(false);
      navigate({ to: "/login" });
    }, 1500);
  };

  return (
    <AuthShell
      title="Verify your email"
      subtitle="We sent a 6-digit code to your inbox."
      footer={
        <>
          Didn't get it? <button className="font-medium text-foreground hover:underline">Resend</button>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="flex justify-between gap-2">
          {[0, 1, 2, 3, 4, 5].map((i) => (
            <input
              key={i}
              ref={(el) => { inputsRef.current[i] = el; }}
              type="text"
              inputMode="numeric"
              maxLength={1}
              value={code[i]}
              onChange={(e) => handleChange(i, e.target.value)}
              onKeyDown={(e) => handleKeyDown(i, e)}
              className="h-12 w-10 rounded-md border border-input bg-background text-center font-mono text-lg outline-hidden focus:border-[color:var(--brand)]"
              required
            />
          ))}
        </div>
        <Button type="submit" className="w-full" disabled={isLoading || code.some((d) => !d)}>
          {isLoading ? "Verifying..." : "Verify and continue"}
        </Button>
      </form>
    </AuthShell>
  );
}