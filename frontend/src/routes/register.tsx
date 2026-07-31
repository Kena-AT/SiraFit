import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { AuthShell } from "@/components/sirafit/shell";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/register")({
  head: () => ({ meta: [{ title: "Create account · SiraFit" }] }),
  component: RegisterPage,
});

function RegisterPage() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { id, value } = e.target;
    setFormData((prev) => ({ ...prev, [id]: value }));
    if (errors[id]) {
      setErrors((prev) => {
        const n = { ...prev };
        delete n[id];
        return n;
      });
    }
  };

  const validate = () => {
    const errs: Record<string, string> = {};
    if (!formData.full_name.trim()) errs.full_name = "Full name is required";
    if (!formData.email.trim()) errs.email = "Email is required";
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email))
      errs.email = "Invalid email format";
    if (!formData.password) errs.password = "Password is required";
    else if (!/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/.test(formData.password))
      errs.password = "Password must be at least 8 characters, include an uppercase letter, a lowercase letter, a number, and a special character";
    if (formData.password !== formData.confirmPassword)
      errs.confirmPassword = "Passwords do not match";
    return errs;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const validationErrors = validate();
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setIsLoading(true);
    setMessage(null);
    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_URL || "http://localhost:8000"}/api/v1/auth/register`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            full_name: formData.full_name.trim(),
            email: formData.email.trim().toLowerCase(),
            password: formData.password,
          }),
        },
      );
      if (response.ok) {
        setMessage({ type: "success", text: "Registration successful! Please verify your email." });
        const registeredEmail = formData.email.trim().toLowerCase();
        setFormData({ full_name: "", email: "", password: "", confirmPassword: "" });
        setTimeout(() => navigate({ to: "/verify-email", search: { email: registeredEmail } }), 2000);
      } else {
        const errorData = await response.json();
        setMessage({ type: "error", text: errorData.detail || "Registration failed" });
      }
    } catch {
      setMessage({ type: "error", text: "Network error. Please try again." });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AuthShell
      title="Create your account"
      subtitle="One device per account. Bring your own Gemini key."
      footer={
        <>
          Have an account?{" "}
          <Link to="/login" className="font-medium text-foreground hover:underline">
            Log in
          </Link>
          .
        </>
      }
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {message && (
          <div
            className={`p-3 rounded-md text-sm border ${
              message.type === "success"
                ? "bg-green-50 text-green-600 border-green-200"
                : "bg-red-50 text-red-600 border-red-200"
            }`}
          >
            {message.text}
          </div>
        )}
        <div className="space-y-1.5">
          <Label htmlFor="full_name">Name</Label>
          <Input
            id="full_name"
            placeholder="King Kunta"
            value={formData.full_name}
            onChange={handleChange}
          />
          {errors.full_name && <p className="text-xs text-red-600 mt-1">{errors.full_name}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            placeholder="king@kunta.dev"
            value={formData.email}
            onChange={handleChange}
          />
          {errors.email && <p className="text-xs text-red-600 mt-1">{errors.email}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            placeholder="Create a strong password"
            value={formData.password}
            onChange={handleChange}
          />
          <div className="text-xs space-y-1 mt-1">
            <p className={/^(?=.*[A-Z]).{1,}$/.test(formData.password) ? "text-green-600" : "text-muted-foreground"}>
              • At least one uppercase letter
            </p>
            <p className={/^(?=.*[a-z]).{1,}$/.test(formData.password) ? "text-green-600" : "text-muted-foreground"}>
              • At least one lowercase letter
            </p>
            <p className={/^(?=.*\d).{1,}$/.test(formData.password) ? "text-green-600" : "text-muted-foreground"}>
              • At least one number
            </p>
            <p className={/^(?=.*[!@#$%^&*(),.?":{}|<>]).{1,}$/.test(formData.password) ? "text-green-600" : "text-muted-foreground"}>
              • At least one special character
            </p>
            <p className={formData.password.length >= 8 ? "text-green-600" : "text-muted-foreground"}>
              • At least 8 characters
            </p>
          </div>
          {errors.password && <p className="text-xs text-red-600 mt-1">{errors.password}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="confirmPassword">Confirm Password</Label>
          <Input
            id="confirmPassword"
            type="password"
            placeholder="Confirm your password"
            value={formData.confirmPassword}
            onChange={handleChange}
          />
          {errors.confirmPassword && (
            <p className="text-xs text-red-600 mt-1">{errors.confirmPassword}</p>
          )}
        </div>
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? "Creating account..." : "Create account"}
        </Button>
      </form>
    </AuthShell>
  );
}
