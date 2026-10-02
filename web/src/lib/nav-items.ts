import {
  LayoutDashboard,
  Compass,
  ListChecks,
  Send,
  Radar,
  BarChart3,
  FileText,
  Settings,
  Target,
} from "lucide-react";
import type { ComponentType, SVGProps } from "react";

export type NavItem = {
  href: string;
  label: string;
  icon: ComponentType<SVGProps<SVGSVGElement>>;
  chip?: string;
  group?: "Operations" | "Assets" | "Intelligence" | "System";
};

export const NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Today", icon: LayoutDashboard, group: "Operations" },
  { href: "/match", label: "Match Analysis", icon: Target, chip: "A-H", group: "Operations" },
  { href: "/explore", label: "Explore", icon: Compass, chip: "New", group: "Operations" },
  { href: "/pipeline", label: "Pipeline", icon: ListChecks, group: "Operations" },
  { href: "/cv", label: "CV & Health", icon: FileText, group: "Assets" },
  { href: "/followups", label: "Follow-ups", icon: Send, group: "Intelligence" },
  { href: "/portals", label: "Portals", icon: Radar, group: "Intelligence" },
  { href: "/analytics", label: "Analytics", icon: BarChart3, group: "Intelligence" },
  { href: "/config", label: "Config", icon: Settings, group: "System" },
];

export function isActivePath(href: string, pathname: string): boolean {
  return href === "/" ? pathname === "/" : pathname.startsWith(href);
}
