import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/gemini-key")({
  head: () => ({ meta: [{ title: "Connect your Gemini key · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">Documentation</Link>
        <ChevronRight className="h-3 w-3" />
        <span>Connect your Gemini key</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">Connect your Gemini key</h1>
      <p className="mt-4 text-muted-foreground">
        SiraFit is local-first. You bring your own AI key; we store it encrypted
        at rest and never log your requests or responses.
      </p>
      <h2 className="mt-8 text-lg font-semibold">How to add your key</h2>
      <ol className="mt-4 list-decimal list-inside space-y-2 text-sm">
        <li>Go to <strong>Settings → AI Keys</strong> in the dashboard.</li>
        <li>Paste your Gemini API key into the <em>Gemini</em> field.</li>
        <li>Save. The key is encrypted and stored only on your account.</li>
        <li>Run a quick <strong>Analyze</strong> on any job to verify connectivity.</li>
      </ol>
    </article>
  ),
});