import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { toast } from "sonner";
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
  { id: "anthropic/claude-3-5-sonnet-20240620", label: "Claude 3.5 Sonnet", provider: "anthropic" },
  { id: "anthropic/claude-3-opus-20240229", label: "Claude 3 Opus", provider: "anthropic" },
  { id: "openai/gpt-4o", label: "GPT-4o", provider: "openai" },
  { id: "openai/gpt-4o-mini", label: "GPT-4o Mini", provider: "openai" },
  { id: "openai/gpt-4-turbo", label: "GPT-4 Turbo", provider: "openai" },
  { id: "meta-llama/llama-3-8b-instruct", label: "Llama 3 8B", provider: "openrouter" },
  { id: "meta-llama/llama-3-70b-instruct", label: "Llama 3 70B", provider: "openrouter" },
  { id: "xai/grok-beta", label: "Grok Beta", provider: "grok" },
  { id: "mistralai/mistral-large-latest", label: "Mistral Large", provider: "mistral" },
  { id: "mistralai/mistral-small-latest", label: "Mistral Small", provider: "mistral" },
  { id: "nvidia/meta/llama-3.1-405b-instruct", label: "Llama 3.1 405B", provider: "nvidia" },
];

const PROVIDERS = [
  { id: "gemini", label: "Gemini" },
  { id: "openrouter", label: "OpenRouter" },
  { id: "anthropic", label: "Anthropic" },
  { id: "openai", label: "OpenAI" },
  { id: "mistral", label: "Mistral" },
  { id: "grok", label: "Grok" },
  { id: "nvidia", label: "Nvidia" },
];
const DEFAULT_FALLBACK = PROVIDERS.map((p) => p.id);

function statusFor(keyStatus: any, provider: string): { text: string; tone: "success" | "muted" } {
  const ui = keyStatus?.[`${provider}_configured`];
  const env = keyStatus?.[`${provider}_env`];
  if (ui) return { text: "(set)", tone: "success" };
  if (env) return { text: "(env)", tone: "muted" };
  return { text: "(not set)", tone: "muted" };
}

function AISettings() {
  const queryClient = useQueryClient();
  const [apiKeys, setApiKeys] = useState({
    gemini: "",
    openrouter: "",
    anthropic: "",
    openai: "",
    grok: "",
    mistral: "",
    nvidia: "",
  });
  const [provider, setProvider] = useState("gemini");
  const [activeModel, setActiveModel] = useState("gemini-1.5-flash");
  const [fallbackOrder, setFallbackOrder] = useState<string[]>(DEFAULT_FALLBACK);
  const [fallbackEnabled, setFallbackEnabled] = useState<Record<string, boolean>>(
    Object.fromEntries(PROVIDERS.map((p) => [p.id, true])),
  );

  const { data: config, isLoading } = useQuery({
    queryKey: ["ai-config"],
    queryFn: async () => {
      const res = await apiFetch("/api/v1/users/me/ai-config");
      if (!res.ok) throw new Error("Failed to fetch AI config");
      return res.json();
    },
    retry: false,
  });

  const { data: keyStatus, isLoading: keyStatusLoading } = useQuery({
    queryKey: ["ai-key-status"],
    queryFn: async () => {
      const res = await apiFetch("/api/v1/users/me/preferences/ai-keys");
      if (!res.ok) throw new Error("Failed to fetch AI key status");
      return res.json();
    },
    retry: false,
  });

  useEffect(() => {
    if (config) {
      setProvider(config.provider || "gemini");
      setActiveModel(config.model || "gemini-1.5-flash");
      if (Array.isArray(config.fallback_order) && config.fallback_order.length) {
        const order = config.fallback_order.filter((p: string) =>
          PROVIDERS.some((x) => x.id === p),
        );
        const missing = PROVIDERS.map((p) => p.id).filter((p) => !order.includes(p));
        setFallbackOrder([...order, ...missing]);
        setFallbackEnabled(Object.fromEntries(PROVIDERS.map((p) => [p.id, order.includes(p.id)])));
      }
    }
  }, [config]);

  const { mutate: saveConfig, isPending: savePending } = useMutation({
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
      toast.success("Settings saved.");
      queryClient.invalidateQueries({ queryKey: ["ai-config"] });
    },
    onError: (err: Error) => {
      toast.error(`Error: ${err.message}`);
    },
  });

  const { mutate: saveKeys, isPending: keySavePending } = useMutation({
    mutationFn: async (body: object) => {
      const res = await apiFetch("/api/v1/users/me/preferences/ai-keys", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Save failed" }));
        throw new Error(err.detail || "Failed to save API keys");
      }
      return res.json();
    },
    onSuccess: () => {
      toast.success("API keys saved securely.");
      queryClient.invalidateQueries({ queryKey: ["ai-key-status"] });
    },
    onError: (err: Error) => {
      toast.error(`Error: ${err.message}`);
    },
  });

  const handleSaveProvider = () => {
    const orderedEnabled = fallbackOrder.filter((p) => fallbackEnabled[p]);
    saveConfig({ provider, model: activeModel, fallback_order: orderedEnabled });
  };

  const handleSaveKeys = () => {
    const updates: Record<string, string | undefined> = {};
    Object.keys(apiKeys).forEach((key) => {
      if (apiKeys[key as keyof typeof apiKeys]) {
        const fieldMap: Record<string, string> = {
          gemini: "gemini_key",
          openrouter: "openrouter_key",
          anthropic: "anthropic_key",
          openai: "openai_key",
          grok: "grok_key",
          mistral: "mistral_key",
          nvidia: "nvidia_key",
        };
        updates[fieldMap[key]] = apiKeys[key as keyof typeof apiKeys];
      }
    });
    if (Object.keys(updates).length > 0) {
      saveKeys(updates);
    }
  };

  const handleClearKey = (key: keyof typeof apiKeys) => {
    setApiKeys((prev) => ({ ...prev, [key]: "" }));
    const fieldMap: Record<string, string> = {
      gemini: "gemini_key",
      openrouter: "openrouter_key",
      anthropic: "anthropic_key",
      openai: "openai_key",
      grok: "grok_key",
      mistral: "mistral_key",
      nvidia: "nvidia_key",
    };
    saveKeys({ [fieldMap[key]]: "" });
  };

  const handleClearAll = () => {
    setApiKeys({
      gemini: "",
      openrouter: "",
      anthropic: "",
      openai: "",
      grok: "",
      mistral: "",
      nvidia: "",
    });
    saveKeys({
      gemini_key: "",
      openrouter_key: "",
      anthropic_key: "",
      openai_key: "",
      grok_key: "",
      mistral_key: "",
      nvidia_key: "",
    });
  };

  const moveFallback = (index: number, dir: -1 | 1) => {
    const next = [...fallbackOrder];
    const j = index + dir;
    if (j < 0 || j >= next.length) return;
    [next[index], next[j]] = [next[j], next[index]];
    setFallbackOrder(next);
  };

  if (isLoading || keyStatusLoading) {
    return <div className="p-4 text-sm text-muted-foreground">Loading configuration...</div>;
  }

  const effectiveChain = [
    provider,
    ...fallbackOrder.filter((p) => fallbackEnabled[p] && p !== provider),
  ];

  return (
    <div className="space-y-6">
      {/* Provider Selection + Fallback Panel */}
      <Panel
        title="AI provider & model"
        description="Stored encrypted on the server (or supplied via your env file). Used to analyze jobs and generate content. Your key is never exposed to the browser."
      >
        <div className="space-y-4">
          <div className="space-y-3">
            <Label className="flex items-center space-x-2">
              <span className="flex-1">Default Provider & Model</span>
              <div className="flex items-center space-x-4">
                <select
                  value={provider}
                  onChange={(e) => {
                    setProvider(e.target.value);
                    setActiveModel(
                      MODELS.find((m) => m.provider === e.target.value)?.id || MODELS[0].id,
                    );
                  }}
                  className="border rounded px-3 py-2 text-sm"
                >
                  {PROVIDERS.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.label}
                    </option>
                  ))}
                </select>

                <select
                  value={activeModel}
                  onChange={(e) => setActiveModel(e.target.value)}
                  className="border rounded px-3 py-2 text-sm min-w-[200px]"
                >
                  {MODELS.filter((m) => m.provider === provider).map((m) => (
                    <option key={m.id} value={m.id}>
                      {m.label}
                    </option>
                  ))}
                </select>
              </div>
            </Label>
          </div>

          <div className="rounded-md border border-border p-3 text-sm">
            <div className="mb-2 font-medium">Automatic fallback when a model is unavailable</div>
            <p className="mb-3 text-xs text-muted-foreground">
              If your selected model errors or is rate-limited, SiraFit tries the next provider
              below that has a key. Reorder with the arrows; uncheck to exclude.
            </p>
            <ul className="space-y-1">
              {fallbackOrder.map((p, i) => {
                const meta = PROVIDERS.find((x) => x.id === p)!;
                const st = statusFor(keyStatus, p);
                return (
                  <li
                    key={p}
                    className="flex items-center justify-between rounded px-2 py-1 text-sm hover:bg-muted/40"
                  >
                    <label className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={fallbackEnabled[p]}
                        onChange={(e) =>
                          setFallbackEnabled((prev) => ({
                            ...prev,
                            [p]: e.target.checked,
                          }))
                        }
                        className="h-4 w-4"
                      />
                      <span>{meta.label}</span>
                      <span
                        className={
                          st.tone === "success"
                            ? "text-[10px] text-[color:var(--success)]"
                            : "text-[10px] text-muted-foreground"
                        }
                      >
                        {st.text}
                      </span>
                    </label>
                    <div className="flex items-center gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => moveFallback(i, -1)}
                        disabled={i === 0}
                      >
                        ↑
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => moveFallback(i, 1)}
                        disabled={i === fallbackOrder.length - 1}
                      >
                        ↓
                      </Button>
                    </div>
                  </li>
                );
              })}
            </ul>
            <p className="mt-3 text-xs text-muted-foreground">
              Effective order:{" "}
              {effectiveChain.map((p) => PROVIDERS.find((x) => x.id === p)?.label).join(" → ")}
            </p>
          </div>

          <div className="flex items-center gap-4">
            <Button onClick={handleSaveProvider} disabled={savePending} className="flex-1 md:auto">
              {savePending ? "Saving..." : "Save Provider & Model"}
            </Button>
          </div>
        </div>
      </Panel>

      {/* API Keys Panel - All 7 Providers */}
      <Panel
        title="API keys"
        description="Paste keys here (encrypted at rest), or supply them via your server/.env USER_KEYS_ENV_FILE. Either source works — SiraFit uses your UI key first, then falls back to env."
      >
        <div className="space-y-5">
          {PROVIDERS.map((p) => {
            const st = statusFor(keyStatus, p.id);
            const value = apiKeys[p.id as keyof typeof apiKeys];
            return (
              <div className="space-y-2" key={p.id}>
                <Label className="flex items-center space-x-2 justify-between">
                  <span>{p.label} API Key</span>
                  <span
                    className={
                      st.tone === "success"
                        ? "text-[10px] text-[color:var(--success)]"
                        : "text-[10px] text-muted-foreground"
                    }
                  >
                    {st.text}
                  </span>
                </Label>
                <div className="flex items-center gap-2">
                  <Input
                    type="password"
                    value={value}
                    onChange={(e) => setApiKeys((prev) => ({ ...prev, [p.id]: e.target.value }))}
                    placeholder={
                      st.text === "(set)"
                        ? "Enter new key to replace existing one"
                        : `Enter ${p.label} API key`
                    }
                  />
                  {st.text === "(set)" && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleClearKey(p.id as keyof typeof apiKeys)}
                    >
                      Clear
                    </Button>
                  )}
                </div>
              </div>
            );
          })}

          <div className="flex items-center gap-4 pt-4">
            <Button onClick={handleSaveKeys} disabled={keySavePending} className="flex-1 md:auto">
              {keySavePending ? "Saving..." : "Save All API Keys"}
            </Button>
            <Button onClick={handleClearAll} variant="outline" className="flex-1 md:auto">
              Clear All Keys
            </Button>
          </div>
        </div>
      </Panel>

      {/* Local agent */}
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

      {/* Generation options */}
      <Panel title="Generation options" className="">
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
