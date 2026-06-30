import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { Panel, AgentDot, Tag } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";

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
  const [apiKey, setApiKey] = useState("");
  const [provider, setProvider] = useState("gemini");
  const [activeModel, setActiveModel] = useState("gemini-1.5-pro");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setApiKey(localStorage.getItem("ai_api_key") || "");
    setProvider(localStorage.getItem("ai_provider") || "gemini");
    setActiveModel(localStorage.getItem("ai_model") || "gemini-1.5-pro");
  }, []);

  const handleSave = () => {
    localStorage.setItem("ai_api_key", apiKey);
    localStorage.setItem("ai_provider", provider);
    localStorage.setItem("ai_model", activeModel);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleModelSelect = (modelId: string, modelProvider: string) => {
    setActiveModel(modelId);
    setProvider(modelProvider);
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel title="AI API Configuration" description="Stored locally in your browser. Used to analyze jobs.">
        <div className="space-y-4 p-4">
          <div className="space-y-1.5">
            <Label>API Key</Label>
            <Input 
              type="password" 
              value={apiKey} 
              onChange={(e) => setApiKey(e.target.value)} 
              placeholder="Enter Gemini or OpenRouter API key" 
            />
            <p className="text-[11px] text-muted-foreground mt-1">
              Provides fallback if backend `.env` is not set.
            </p>
          </div>
          
          <div className="space-y-2">
            <Label>Available Models</Label>
            <div className="flex flex-wrap gap-2">
              {MODELS.map((m) => (
                <button 
                  key={m.id}
                  onClick={() => handleModelSelect(m.id, m.provider)}
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
            <Button onClick={handleSave}>Save Settings</Button>
            {saved && <span className="text-xs text-[color:var(--success)] font-medium">Saved!</span>}
          </div>
        </div>
      </Panel>

      <Panel title="Local agent">
        <div className="space-y-3 p-4 text-sm">
          <AgentDot label="Connected · v0.8.2" />
          <div className="text-[12px] text-muted-foreground">Auto-update enabled. Next check in 4h.</div>
          <div className="grid grid-cols-2 gap-2 text-[12px]">
            <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Scrape rate</div>1 req / 1.2s</div>
            <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Queue cap</div>64</div>
            <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Retry max</div>3</div>
            <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Cooldown</div>60s</div>
          </div>
          <div className="flex gap-2"><Button variant="outline" size="sm">Restart agent</Button><Button variant="ghost" size="sm">View logs</Button></div>
        </div>
      </Panel>
      <Panel title="Generation options" className="lg:col-span-2">
        <div className="grid gap-3 p-4 sm:grid-cols-3 text-sm">
          <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Repair attempts</div>1 (max)</div>
          <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Tokens / generation</div>1500</div>
          <div><div className="text-[10px] font-semibold uppercase text-muted-foreground">Throttle</div>5 / min</div>
        </div>
      </Panel>
    </div>
  );
}