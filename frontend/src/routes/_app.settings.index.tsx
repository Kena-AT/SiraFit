import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Panel } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { getProfile, updateProfile } from "@/lib/api/profiles";
import { toast } from "sonner";
import { useState } from "react";

export const Route = createFileRoute("/_app/settings/")({
  head: () => ({ meta: [{ title: "Account settings · SiraFit" }] }),
  component: SettingsIndex,
});

function SettingsIndex() {
  const queryClient = useQueryClient();

  const {
    data: profile,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["profile", "me"],
    queryFn: getProfile,
  });

  const updateMutation = useMutation({
    mutationFn: updateProfile,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile", "me"] });
      toast.success("Profile updated successfully");
    },
    onError: (error) => {
      toast.error(`Failed to update profile: ${error.message}`);
    },
  });

  const handleProfileSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!profile) return;

    const formData = new FormData(e.currentTarget);
    const fullName = formData.get("name") as string;
    const nameParts = fullName.split(" ");
    const first_name = nameParts[0] || "";
    const last_name = nameParts.slice(1).join(" ") || "";
    const location = formData.get("location") as string;

    updateMutation.mutate({
      ...profile,
      first_name,
      last_name,
      location,
    });
  };

  const passwordMutation = useMutation({
    mutationFn: async (data: FormData) => {
      // Mock API call since endpoint is not yet implemented
      await new Promise((resolve) => setTimeout(resolve, 500));
      const current = data.get("current_password");
      const newPwd = data.get("new_password");
      const confirmPwd = data.get("confirm_password");

      if (!current) throw new Error("Current password is required");
      if (!newPwd) throw new Error("New password is required");
      if (newPwd !== confirmPwd) throw new Error("Passwords do not match");
      if ((newPwd as string).length < 8) throw new Error("Password must be at least 8 characters");

      return true;
    },
    onSuccess: () => {
      toast.success("Password updated successfully");
    },
    onError: (error) => {
      toast.error(error.message);
    },
  });

  const handlePasswordSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    passwordMutation.mutate(formData);
    if (passwordMutation.isSuccess) {
      e.currentTarget.reset();
    }
  };

  if (isLoading)
    return (
      <div className="p-4 text-sm text-muted-foreground flex items-center justify-center min-h-[200px]">
        Loading profile...
      </div>
    );
  if (error)
    return (
      <div className="p-4 text-sm text-destructive bg-destructive/10 rounded-md">
        Failed to load profile. Make sure the backend is running.
      </div>
    );
  if (!profile) return null;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel title="Profile">
        <form onSubmit={handleProfileSubmit} className="grid gap-3 p-4">
          <div className="space-y-1.5">
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              name="name"
              defaultValue={`${profile.first_name ?? ""} ${profile.last_name ?? ""}`.trim()}
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="email">Email</Label>
            <Input id="email" name="email" defaultValue={profile.email ?? ""} disabled />
            <p className="text-xs text-muted-foreground">Email cannot be changed directly.</p>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="location">Location</Label>
            <Input id="location" name="location" defaultValue={profile.location ?? ""} />
          </div>
          <Button type="submit" className="w-fit" disabled={updateMutation.isPending}>
            {updateMutation.isPending ? "Saving..." : "Save changes"}
          </Button>
        </form>
      </Panel>
      <Panel title="Password">
        <form onSubmit={handlePasswordSubmit} className="grid gap-3 p-4">
          <div className="space-y-1.5">
            <Label htmlFor="current_password">Current password</Label>
            <Input id="current_password" name="current_password" type="password" required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="new_password">New password</Label>
            <Input id="new_password" name="new_password" type="password" required minLength={8} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="confirm_password">Confirm password</Label>
            <Input
              id="confirm_password"
              name="confirm_password"
              type="password"
              required
              minLength={8}
            />
          </div>
          <Button
            type="submit"
            variant="outline"
            className="w-fit"
            disabled={passwordMutation.isPending}
          >
            {passwordMutation.isPending ? "Updating..." : "Update password"}
          </Button>
        </form>
      </Panel>
      <Panel title="Devices" className="lg:col-span-2">
        <ul className="divide-y divide-border text-sm">
          <li className="flex items-center justify-between px-4 py-3">
            <div>
              <div className="font-semibold">MacBook Pro · alex-mbp</div>
              <div className="text-[11px] text-muted-foreground">Active · last seen 12s ago</div>
            </div>
            <span className="rounded bg-[color:var(--brand)]/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest text-[color:var(--brand)]">
              This device
            </span>
          </li>
        </ul>
      </Panel>
    </div>
  );
}
