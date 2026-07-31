import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Panel } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { getProfile, updateProfile } from "@/lib/api/profiles";
import { changePassword, getDevices, revokeDevice, type DeviceSession } from "@/lib/api/users";
import { toast } from "sonner";
import { useState, useEffect } from "react";

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
      const current = data.get("current_password") as string;
      const newPwd = data.get("new_password") as string;
      const confirmPwd = data.get("confirm_password") as string;

      if (!current) throw new Error("Current password is required");
      if (!newPwd) throw new Error("New password is required");
      if (newPwd !== confirmPwd) throw new Error("Passwords do not match");

      // Frontend validation to match backend requirements
      if (newPwd.length < 12) {
        throw new Error("Password must be at least 12 characters");
      }
      if (!/[A-Z]/.test(newPwd)) {
        throw new Error("Password must contain at least one uppercase letter");
      }
      if (!/[a-z]/.test(newPwd)) {
        throw new Error("Password must contain at least one lowercase letter");
      }
      if (!/[0-9]/.test(newPwd)) {
        throw new Error("Password must contain at least one digit");
      }

      return changePassword({
        current_password: current,
        new_password: newPwd,
        confirm_password: confirmPwd,
      });
    },
    onSuccess: () => {
      toast.success("Password updated successfully");
    },
    onError: (error: Error) => {
      const detail = error.message || "Failed to update password";
      toast.error(detail);
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
        <DeviceList />
    </Panel>
  </div>
);
}

function DeviceList() {
  const [devices, setDevices] = useState<DeviceSession[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDevices()
      .then((data) => {
        setDevices(data);
        setLoading(false);
      })
      .catch(() => {
        setDevices([]);
        setLoading(false);
      });
  }, []);

  const formatLastSeen = (lastSeen: string | null | undefined) => {
    if (!lastSeen) return "Never";
    const d = new Date(lastSeen);
    const diffMins = Math.floor((Date.now() - d.getTime()) / 60000);
    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    return `${diffDays}d ago`;
  };

  if (loading) {
    return (
      <div className="divide-y divide-border text-sm">
        <div className="px-4 py-3 text-muted-foreground">Loading devices...</div>
      </div>
    );
  }

  if (devices.length === 0) {
    return (
      <div className="divide-y divide-border text-sm">
        <div className="px-4 py-3 text-muted-foreground">No devices found.</div>
      </div>
    );
  }

  return (
    <ul className="divide-y divide-border text-sm">
      {devices.map((device) => (
        <li key={device.id} className="flex items-center justify-between px-4 py-3">
          <div>
            <div className="font-semibold">{device.device_name}</div>
            <div className="text-[11px] text-muted-foreground">
              {device.is_active ? "Active" : "Inactive"} · Last seen {formatLastSeen(device.last_seen)}
            </div>
            {device.ip_address && (
              <div className="text-[10px] text-muted-foreground mt-0.5">{device.ip_address}</div>
            )}
          </div>
          <div className="flex items-center gap-2">
            <span
              className={cn(
                "rounded px-2 py-0.5 text-[10px] font-semibold uppercase tracking-widest",
                device.is_active
                  ? "bg-[color:var(--brand)]/10 text-[color:var(--brand)]"
                  : "bg-muted/30 text-muted-foreground",
              )}
            >
              {device.is_active ? "Active" : "Revoked"}
            </span>
            {device.is_active && (
              <Button
                variant="ghost"
                size="sm"
                className="text-xs"
                onClick={async () => {
                  try {
                    await revokeDevice(device.id);
                    setDevices(devices.filter((d) => d.id !== device.id));
                    toast.success("Device session revoked");
                  } catch (err: any) {
                    toast.error(err.message || "Failed to revoke device");
                  }
                }}
              >
                Revoke
              </Button>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
