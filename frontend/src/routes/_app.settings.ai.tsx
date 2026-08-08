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
  const [activeModel, setActiveModel] = useState("gemini-1.5-pro");

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
    const body: Record<string, string | undefined> = {
      provider,
      model: activeModel,
    };
    saveConfig(body);
  };

  const handleSaveKeys = () => {
    // Only send keys that have been modified (non-empty)
    const updates: Record<string, string | undefined> = {};
    Object.keys(apiKeys).forEach((key) => {
      if (apiKeys[key as keyof typeof apiKeys]) {
        // Map frontend state keys to backend field names
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
    setApiKeys(prev => ({ ...prev, [key]: "" }));
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

  if (isLoading || keyStatusLoading) {
    return <div className="p-4 text-sm text-muted-foreground">Loading configuration...</div>;
  }

  return (
    <div className="space-y-6">
      {/* Provider Selection Panel 1: AI API Configuration - ALL 7 PROVIDERS */}
      <Panel
        title="AI API Configuration"
        description="Stored encrypted on the server. Used to analyze jobs and generate content. Your key is never exposed to the client."
      >
        <div className="space-y-4">
          {/* Provider Selection */}
          <div className="space-y-3">
            <Label className="flex items-center space-x-2">
              <span className="flex-1">Default Provider & Model</span>
              <div className="flex items-center space-x-4">
                <select
                  value={provider}
                  onChange={(e) => {
                    setProvider(e.target.value as "gemini" | "openrouter" | "anthropic" | "openai" | "grok" | "mistral" | "nvidia");
                    // Reset model when provider changes
                    setActiveModel(
                      MODELS.find(m => m.provider === e.target.value)?.id ||
                      MODELS[0].id
                    );
                  }}
                  className="border rounded px-3 py-2 text-sm"
                >
                  <option value="gemini">Gemini</option>
                  <option value="openrouter">OpenRouter</option>
                  <option value="anthropic">Anthropic</option>
                  <option value="openai">OpenAI</option>
                  <option value="grok">Grok</option>
                  <option value="mistral">Mistral</option>
                  <option value="nvidia">Nvidia</option>
                </select>

                <select
                  value={activeModel}
                  onChange={(e) => setActiveModel(e.target.value)}
                  className="border rounded px-3 py-2 text-sm min-w-[200px]"
                >
                  {MODELS
                    .filter(m => m.provider === provider)
                    .map(m => (
                      <option key={m.id} value={m.id}>
                        {m.label}
                      </option>
                    ))}
                </select>
              </div>
            </Label>
          </div>

          {/* API Keys Section - All 7 Providers */}
          <div className="space-y-5">
            {/* Gemini */}
            <div className="space-y-2">
              <Label className="flex items-center space-x-2 justify-between">
                <span>Gemini API Key</span>
                {keyStatus && keyStatus.gemini_configured !== undefined
                  ? (
                    keyStatus.gemini_configured
                      ? <span className="text-[color:var(--success)] text-[10px]">(set)</span>
                      : <span className="text-muted-foreground text-[10px]">(not set)</span>
                  )
                  : <span className="text-muted-foreground text-[10px]">(not configured)</span>
                }
              </Label>
              <Input
                type="password"
                value={apiKeys.gemini}
                onChange={(e) => setApiKeys(prev => ({ ...prev, gemini: e.target.value }))}
                placeholder={
                  keyStatus && keyStatus.gemini_configured
                    ? "Enter new key to replace existing one"
                    : "Enter Gemini API key"
                }
              />
              {keyStatus && keyStatus.gemini_configured !== undefined && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleClearKey("gemini")}
                  className="ml-2"
                >
                  Clear
                </Button>
              )}
            </div>

            {/* OpenRouter */}
            <div className="space-y-2">
              <Label className="flex items-center space-x-2 justify-between">
                <span>OpenRouter API Key</span>
                {keyStatus && keyStatus.openrouter_configured !== undefined
                  ? (
                    keyStatus.openrouter_configured
                      ? <span className="text-[color:var(--success)] text-[10px]">(set)</span>
                      : <span className="text-muted-foreground text-[10px]">(not set)</span>
                  )
                  : <span className="text-muted-foreground text-[10px]">(not configured)</span>
                }
              </Label>
              <Input
                type="password"
                value={apiKeys.openrouter}
                onChange={(e) => setApiKeys(prev => ({ ...prev, openrouter: e.target.value }))}
                placeholder={
                  keyStatus && keyStatus.openrouter_configured
                    ? "Enter new key to replace existing one"
                    : "Enter OpenRouter API key"
                }
              />
              {keyStatus && keyStatus.openrouter_configured !== undefined && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleClearKey("openrouter")}
                  className="ml-2"
                >
                  Clear
                </Button>
              )}
            </div>

            {/* Anthropic */}
            <div className="space-y-2">
              <Label className="flex items-center space-x-2 justify-between">
                <span>Anthropic API Key</span>
                {keyStatus && keyStatus.anthropic_configured !== undefined
                  ? (
                    keyStatus.anthropic_configured
                      ? <span className="text-[color:var(--success)] text-[10px]">(set)</span>
                      : <span className="text-muted-foreground text-[10px]">(not set)</span>
                  )
                  : <span className="text-muted-foreground text-[10px]">(not configured)</span>
                }
              </Label>
              <Input
                type="password"
                value={apiKeys.anthropic}
                onChange={(e) => setApiKeys(prev => ({ ...prev, anthropic: e.target.value }))}
                placeholder="Enter Anthropic API key"
              />
              {keyStatus && keyStatus.anthropic_configured !== undefined && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleClearKey("anthropic")}
                  className="ml-2"
                >
                  Clear
                </Button>
              )}
            </div>

            {/* OpenAI */}
            <div className="space-y-2">
              <Label className="flex items-center space-x-2 justify-between">
                <span>OpenAI API Key</span>
                {keyStatus && keyStatus.openai_configured !== undefined
                  ? (
                    keyStatus.openai_configured
                      ? <span className="text-[color:var(--success)] text-[10px]">(set)</span>
                      : <span className="text-muted-foreground text-[10px]">(not set)</span>
                  )
                  : <span className="text-muted-foreground text-[10px]">(not configured)</span>
                }
              </Label>
              <Input
                type="password"
                value={apiKeys.openai}
                onChange={(e) => setApiKeys(prev => ({ ...prev, openai: e.target.value }))}
                placeholder="Enter OpenAI API key"
              />
              {keyStatus && keyStatus.openai_configured !== undefined && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleClearKey("openai")}
                  className="ml-2"
                >
                  Clear
                </Button>
              )}
            </div>

            {/* Grok */}
            <div className="space-y-2">
              <Label className="flex items-center space-x-2 justify-between">
                <span>Grok API Key</span>
                {keyStatus && keyStatus.grok_configured !== undefined
                  ? (
                    keyStatus.grok_configured
                      ? <span className="text-[color:var(--success)] text-[10px]">(set)</span>
                      : <span className="text-muted-foreground text-[10px]">(not set)</span>
                  )
                  : <span className="text-muted-foreground text-[10px]">(not configured)</span>
                }
              </Label>
              <Input
                type="password"
                value={apiKeys.grok}
                onChange={(e) => setApiKeys(prev => ({ ...prev, grok: e.target.value }))}
                placeholder="Enter Grok API key"
              />
              {keyStatus && keyStatus.grok_configured !== undefined && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleClearKey("grok")}
                  className="ml-2"
                >
                  Clear
                </Button>
              )}
            </div>

            {/* Mistral */}
            <div className="space-y-2">
              <Label className="flex items-center space-x-2 justify-between">
                <span>Mistral API Key</span>
                {keyStatus && keyStatus.mistral_configured !== undefined
                  ? (
                    keyStatus.mistral_configured
                      ? <span className="text-[color:var(--success)] text-[10px]">(set)</span>
                      : <span className="text-muted-foreground text-[10px]">(not set)</span>
                  )
                  : <span className="text-muted-foreground text-[10px]">(not configured)</span>
                }
              </Label>
              <Input
                type="password"
                value={apiKeys.mistral}
                onChange={(e) => setApiKeys(prev => ({ ...prev, mistral: e.target.value }))}
                placeholder="Enter Mistral API key"
              />
              {keyStatus && keyStatus.mistral_configured !== undefined && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleClearKey("mistral")}
                  className="ml-2"
                >
                  Clear
                </Button>
              )}
            </div>

            {/* Nvidia */}
            <div className="space-y-2">
              <Label className="flex items-center space-x-2 justify-between">
                <span>Nvidia API Key</span>
                {keyStatus && keyStatus.nvidia_configured !== undefined
                  ? (
                    keyStatus.nvidia_configured
                      ? <span className="text-[color:var(--success)] text-[10px]">(set)</span>
                      : <span className="text-muted-foreground text-[10px]">(not set)</span>
                  )
                  : <span className="text-muted-foreground text-[10px]">(not configured)</span>
                }
              </Label>
              <Input
                type="password"
                value={apiKeys.nvidia}
                onChange={(e) => setApiKeys(prev => ({ ...prev, nvidia: e.target.value }))}
                placeholder="Enter Nvidia API key"
              />
              {keyStatus && keyStatus.nvidia_configured !== undefined && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleClearKey("nvidia")}
                  className="ml-2"
                >
                  Clear
                </Button>
              )}
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-4 pt-4">
            <Button
              onClick={handleSaveProvider}
              disabled={savePending}
              className="flex-1 md:auto"
            >
              {savePending ? "Saving..." : "Save Provider & Model"}
            </Button>

            <Button
              onClick={handleSaveKeys}
              disabled={keySavePending}
              className="flex-1 md:auto"
            >
              {keySavePending ? "Saving..." : "Save All API Keys"}
            </Button>

            <Button
              onClick={handleClearAll}
              variant="outline"
              className="flex-1 md:auto"
            >
              Clear All Keys
            </Button>
          </div>
        </div>
      </Panel>

      {/* Panel 2: Local Agent (unchanged) */}
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

      {/* Panel 3: Generation options (unchanged) */}
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
