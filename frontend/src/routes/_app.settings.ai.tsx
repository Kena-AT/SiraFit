import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Panel, AgentDot } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { apiFetch } from "@/lib/api/client";

export const Route = createFileRoute("/_app/settings/ai")({
  head: () => ({ meta: [{ title: "AI & agent settings · SiraFit" }] }),
  component: AISettings,
});

const MODELS = [
  { id: "gemini-1.5-pro", label: "Gemini 1.5 Pro", provider: "gemini" },
  { id: "gemini-1.5-flash", label: "Gemini 1.5 Flash", provider: "gemini" },
  { id: "anthropic/claude-3-haiku", label: "Claude 3 Haiku", provider: "openrouter" },
  { id: "meta-llama/llama-3-8b-instruct", label: "Llama 3 8B", provider: "openrouter" },
];

function AISettings() {
  const queryClient = useQueryClient();
  const [geminiKey, setGeminiKey] = useState("");
  const [openrouterKey, setOpenrouterKey] = useState("");
  const [provider, setProvider] = useState("gemini");
  const [activeModel, setActiveModel] = useState("gemini-1.5-pro");
  const [message, setMessage] = useState("");

  const { data: config, isLoading } = useQuery({
    queryKey: ["ai-config"],
    queryFn: async () => {
      const res = await apiFetch("/api/v1/users/me/ai-config");
      if (!res.ok) throw new Error("Failed to fetch AI config");
      return res.json();
    },
    retry: false,
  });

  useEffect(() => {
    if (config) {
      setProvider(config.provider || "gemini");
      setActiveModel(config.model || "gemini-1.5-pro");
    }
  }, [config]);

  const { mutate: saveConfig, isPending } = useMutation({
    mutationFn: async (body: object) => {
      const res = await apiFetch("/api/v1/users/me/ai-config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Save failed" }));
        throw new Error(err.detail || "Failed to save AI configuration");
      }
      return res.json();
    },
    onSuccess: () => {
      setMessage("Settings saved securely.");
      setGeminiKey("");
      setOpenrouterKey("");
      queryClient.invalidateQueries({ queryKey: ["ai-config"] });
      setTimeout(() => setMessage(""), 3000);
    },
    onError: (err: Error) => {
      setMessage(`Error: ${err.message}`);
    },
  });

  const handleSave = () => {
    const body: Record<string, string | undefined> = {
      provider,
      model: activeModel,
    };
    if (geminiKey) body.gemini_key = geminiKey;
    if (openrouterKey) body.openrouter_key = openrouterKey;
    saveConfig(body);
  };

  const handleClear = () => {
    setGeminiKey("");
    setOpenrouterKey("");
    saveConfig({ gemini_key: "", openrouter_key: "", provider, model: activeModel });
  };

  if (isLoading) {
    return <div className="p-4 text-sm text-muted-foreground">Loading configuration...</div>;
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel
        title="AI API Configuration"
        description="Stored encrypted on the server. Used to analyze jobs. Your key is never exposed to the client."
      >
        <div className="space-y-4 p-4">
          <div className="space-y-1.5">
            <Label>
              Gemini API Key{" "}
              {config?.has_gemini_key ? (
                <span className="text-[color:var(--success)]">(set)</span>
              ) : (
                <span className="text-muted-foreground">(not set)</span>
              )}
            </Label>
            <Input
              type="password"
              value={geminiKey}
              onChange={(e) => setGeminiKey(e.target.value)}
              placeholder={
                config?.has_gemini_key
                  ? "Enter new key to replace existing one"
                  : "Enter Gemini API key"
              }
            />
          </div>

          <div className="space-y-1.5">
            <Label>
              OpenRouter API Key{" "}
              {config?.has_openrouter_key ? (
                <span className="text-[color:var(--success)]">(set)</span>
              ) : (
                <span className="text-muted-foreground">(not set)</span>
              )}
            </Label>
            <Input
              type="password"
              value={openrouterKey}
              onChange={(e) => setOpenrouterKey(e.target.value)}
              placeholder={
                config?.has_openrouter_key
                  ? "Enter new key to replace existing one"
                  : "Enter OpenRouter API key"
              }
            />
          </div>

          <div className="space-y-2">
            <Label>Available Models</Label>
            <div className="flex flex-wrap gap-2">
              {MODELS.map((m) => (
                <button
                  key={m.id}
                  onClick={() => {
                    setActiveModel(m.id);
                    setProvider(m.provider);
                  }}
                  className={`px-2.5 py-1 text-xs font-medium rounded-md ring-1 ${
                    activeModel === m.id
                      ? "bg-foreground text-background ring-foreground"
                      : "bg-card text-foreground ring-border hover:bg-muted"
                  }`}
                >
                  {m.label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button onClick={handleSave} disabled={isPending}>
              {isPending ? "Saving..." : "Save Settings"}
            </Button>
            {(config?.has_gemini_key || config?.has_openrouter_key) && (
              <Button variant="outline" onClick={handleClear} disabled={isPending}>
                Clear Keys
              </Button>
            )}
            {message && (
              <span
                className={`text-xs font-medium ${message.startsWith("Error") ? "text-red-500" : "text-[color:var(--success)]"}`}
              >
                {message}
              </span>
            )}
          </div>
        </div>
      </Panel>

      <Panel title="Local agent">
        <div className="space-y-3 p-4 text-sm">
          <AgentDot label="Connected · v0.8.2" />
          <div className="text-[12px] text-muted-foreground">
            Auto-update enabled. Next check in 4h.
          </div>
          <div className="grid grid-cols-2 gap-2 text-[12px]">
            <div>
              <div className="text-[10px] font-semibold uppercase text-muted-foreground">
                Scrape rate
              </div>
              1 req / 1.2s
            </div>
            <div>
              <div className="text-[10px] font-semibold uppercase text-muted-foreground">
                Queue cap
              </div>
              64
            </div>
            <div>
              <div className="text-[10px] font-semibold uppercase text-muted-foreground">
                Retry max
              </div>
              3
            </div>
            <div>
              <div className="text-[10px] font-semibold uppercase text-muted-foreground">
                Cooldown
              </div>
              60s
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              Restart agent
            </Button>
            <Button variant="ghost" size="sm">
              View logs
            </Button>
          </div>
        </div>
      </Panel>
      <Panel title="Generation options" className="lg:col-span-2">
        <div className="grid gap-3 p-4 sm:grid-cols-3 text-sm">
          <div>
            <div className="text-[10px] font-semibold uppercase text-muted-foreground">
              Repair attempts
            </div>
            1 (max)
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase text-muted-foreground">
              Tokens / generation
            </div>
            1500
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase text-muted-foreground">
              Throttle
            </div>
            5 / min
          </div>
        </div>
      </Panel>
    </div>
  );
}
