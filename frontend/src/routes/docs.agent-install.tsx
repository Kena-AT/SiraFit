import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/agent-install")({
  head: () => ({ meta: [{ title: "Install the local agent · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">Documentation</Link>
        <ChevronRight className="h-3 w-3" />
        <span>Install the local agent</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">Install the local agent</h1>
      <p className="mt-4 text-muted-foreground">
        Download the desktop agent and connect it to your account. The agent runs
        locally on your machine, so your AI key never leaves your computer.
      </p>
      <h2 className="mt-8 text-lg font-semibold">Steps</h2>
      <ol className="mt-4 list-decimal list-inside space-y-2 text-sm">
        <li>Navigate to <strong>Settings → AI Keys</strong> in the web app.</li>
        <li>Download the SiraFit agent for your platform (macOS, Windows, Linux).</li>
        <li>Run the installer and follow the on-screen prompts.</li>
        <li>Copy the pairing code shown in the agent and paste it into the web app.</li>
        <li>Once paired, the agent is ready to scrape jobs and run analyses.</li>
      </ol>
    </article>
  ),
});