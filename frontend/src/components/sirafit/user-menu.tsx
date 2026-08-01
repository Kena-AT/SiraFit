"use client";

import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Settings, HelpCircle, LogOut } from "lucide-react";

/**
 * Derive display initials from the user's full name or, as a fallback,
 * the first two characters of their email.
 */
function getInitials(name: string | null, email: string): string {
  if (name) {
    const parts = name.trim().split(/\s+/).filter(Boolean);
    if (parts.length >= 2) {
      return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
    }
    return parts[0].substring(0, Math.min(2, parts[0].length)).toUpperCase();
  }
  return email.substring(0, 2).toUpperCase();
}

export function UserMenu() {
  const { user, logout } = useAuth();
  const [open, setOpen] = useState(false);

  // Don't render until we have a user
  if (!user) return null;

  const handleLogout = () => {
    setOpen(false);
    void logout();
  };

  return (
    <DropdownMenu open={open} onOpenChange={setOpen}>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label="Open user menu"
          className={cn(
            "grid h-7 w-7 place-items-center rounded-full bg-muted text-[11px] font-semibold text-muted-foreground ring-1 ring-border",
            "transition-colors hover:bg-accent hover:text-foreground",
            "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background",
          )}
        >
          {getInitials(user.full_name, user.email)}
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        align="end"
        sideOffset={8}
        // Replace the default zoom-in/zoom-out with a cleaner fade + slide
        className="w-56 data-[state=closed]:zoom-out-100 data-[state=open]:zoom-in-100"
      >
        {/* Non-clickable user info header */}
        <div className="px-3 py-2.5 select-none">
          <div className="text-sm font-medium text-foreground">
            {user.full_name || ""}
          </div>
          <div
            className="mt-0.5 max-w-[208px] truncate text-xs text-muted-foreground"
            title={user.email}
          >
            {user.email}
          </div>
        </div>

        <DropdownMenuSeparator />

        {/* Action items */}
        <DropdownMenuItem asChild>
          <Link to="/settings" className="cursor-pointer">
            <Settings className="h-4 w-4" />
            <span>Settings</span>
          </Link>
        </DropdownMenuItem>
        <DropdownMenuItem asChild>
          <Link to="/help" className="cursor-pointer">
            <HelpCircle className="h-4 w-4" />
            <span>Help &amp; Support</span>
          </Link>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        {/* Destructive action */}
        <DropdownMenuItem
          onSelect={handleLogout}
          className="text-destructive focus:bg-destructive/15 focus:text-destructive"
        >
          <LogOut className="h-4 w-4" />
          <span>Log out</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
