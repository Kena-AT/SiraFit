import { createFileRoute } from "@tanstack/react-router";
import { ChevronRight } from "lucide-react";
import { Link } from "@tanstack/react-router";

export const Route = createFileRoute("/docs/gemini-key")({
  head: () => ({ meta: [{ title: "Connect your AI keys · SiraFit" }] }),
  component: () => (
    <article className="mx-auto max-w-3xl px-6 py-16">
      <nav className="mb-6 flex items-center gap-1 text-xs text-muted-foreground">
        <Link to="/help" className="hover:text-foreground">
          Documentation
        </Link>
        <ChevronRight className="h-3 w-3" />
        <span>Connect your AI keys</span>
      </nav>
      <h1 className="text-3xl font-semibold tracking-tight">Connect your AI keys</h1>
      <p className="mt-4 text-muted-foreground">
        SiraFit is built on a Bring-Your-Own-Key (BYOK) architecture. You can connect your favorite
        AI models—Google Gemini, Anthropic Claude, OpenAI GPT, Groq, Mistral, xAI Grok, NVIDIA,
        OpenRouter, or a local Ollama instance. Your keys are encrypted at rest with AES-GCM and
        never used to train models.
      </p>
      <h2 className="mt-8 text-lg font-semibold">Supported providers</h2>
      <ul className="mt-4 list-disc list-inside space-y-1.5 text-sm text-muted-foreground">
        <li>
          <strong className="text-foreground">Google Gemini:</strong> Gemini 1.5 Pro, 1.5 Flash
        </li>
        <li>
          <strong className="text-foreground">Anthropic:</strong> Claude 3.5 Sonnet, Claude 3 Opus
        </li>
        <li>
          <strong className="text-foreground">OpenAI:</strong> GPT-4o, GPT-4o Mini, GPT-4 Turbo
        </li>
        <li>
          <strong className="text-foreground">Groq &amp; Mistral:</strong> High-throughput fast
          inference (Llama 3, Mistral Large/Small)
        </li>
        <li>
          <strong className="text-foreground">OpenRouter &amp; Local:</strong> Any OpenAI-compatible
          gateway or local Ollama endpoint
        </li>
      </ul>
      <h2 className="mt-8 text-lg font-semibold">How to add your keys</h2>
      <ol className="mt-4 list-decimal list-inside space-y-2 text-sm">
        <li>
          Go to <strong>Settings → AI &amp; Agent</strong> in the dashboard.
        </li>
        <li>Paste your API key into the corresponding provider field.</li>
        <li>Select your primary active model and configure fallback provider order.</li>
        <li>
          Click <strong>Save AI configuration</strong>. The key is encrypted and validated.
        </li>
        <li>
          Run a quick <strong>Analyze</strong> on any job card to verify end-to-end connectivity.
        </li>
      </ol>
    </article>
  ),
});
