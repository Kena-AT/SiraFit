import { createFileRoute } from "@tanstack/react-router";
import { Panel, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { useState } from "react";

export const Route = createFileRoute("/_app/settings/resume")({
  head: () => ({ meta: [{ title: "Resume settings · SiraFit" }] }),
  component: ResumeSettings,
});

function ResumeSettings() {
  const [selectedTemplate, setSelectedTemplate] = useState("Technical");
  const [autoTailor, setAutoTailor] = useState(true);

  const saveMutation = useMutation({
    mutationFn: async () => {
      // Mock API call
      await new Promise((resolve) => setTimeout(resolve, 500));
      return true;
    },
    onSuccess: () => {
      toast.success("Resume settings updated successfully");
    },
    onError: () => {
      toast.error("Failed to update resume settings");
    },
  });

  const handleSave = () => {
    saveMutation.mutate();
  };

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel title="Default template">
        <div className="space-y-3 p-4">
          <div className="flex flex-wrap gap-2">
            {["Minimal", "Technical", "Modern", "Corporate", "Compact"].map((t) => (
              <button key={t} onClick={() => setSelectedTemplate(t)} type="button">
                <Tag
                  className={
                    selectedTemplate === t ? "bg-primary text-primary-foreground" : "hover:bg-muted"
                  }
                >
                  {t}
                  {t === "Technical" && selectedTemplate !== t ? " · default" : ""}
                </Tag>
              </button>
            ))}
          </div>
          <p className="text-[12px] text-muted-foreground">
            Used when generating a new tailored resume unless overridden.
          </p>
        </div>
      </Panel>
      <Panel title="Auto-tailor on new job">
        <div className="flex items-center justify-between p-4 text-sm">
          <div>Run resume tailoring when a job scores above 85%.</div>
          <Button
            variant={autoTailor ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoTailor(!autoTailor)}
          >
            {autoTailor ? "Enabled" : "Disabled"}
          </Button>
        </div>
      </Panel>
      <Panel title="Export defaults" className="lg:col-span-2">
        <div className="grid gap-3 p-4 sm:grid-cols-3 text-sm">
          <div>
            <div className="text-[10px] font-semibold uppercase text-muted-foreground">Format</div>
            PDF
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase text-muted-foreground">
              Page size
            </div>
            Letter
          </div>
          <div>
            <div className="text-[10px] font-semibold uppercase text-muted-foreground">
              Filename
            </div>
            <span className="font-mono">{`{{candidate}}_{{company}}_{{role}}.pdf`}</span>
          </div>
        </div>
      </Panel>
      <div className="lg:col-span-2 flex justify-end">
        <Button onClick={handleSave} disabled={saveMutation.isPending}>
          {saveMutation.isPending ? "Saving..." : "Save settings"}
        </Button>
      </div>
    </div>
  );
}
