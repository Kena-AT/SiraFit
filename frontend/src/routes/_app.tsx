import { createFileRoute } from "@tanstack/react-router";
import { AppShell } from "@/components/sirafit/shell";

export const Route = createFileRoute("/_app")({
  component: AppShell,
});