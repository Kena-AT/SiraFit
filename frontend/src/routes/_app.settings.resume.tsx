import { createFileRoute } from "@tanstack/react-router";
import { Panel, Tag } from "@/components/sirafit/bits";
import { Button } from "@/components/ui/button";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { useState, useEffect } from "react";
import {
  getResumeDefaults,
  updateResumeDefaults,
  type ResumeDefaults,
} from "@/lib/api/users";

export const Route = createFileRoute("/_app/settings/resume")({
  head: () => ({ meta: [{ title: "Resume settings · SiraFit" }] }),
  component: ResumeSettings,
});

const TEMPLATE_MAP: Record<string, string> = {
  Minimal: "minimal",
  Technical: "modern",
  Modern: "modern",
  Corporate: "corporate",
  Compact: "compact",
};

const TEMPLATE_LABELS = ["Minimal", "Technical", "Modern", "Corporate", "Compact"];

function ResumeSettings() {
  const queryClient = useQueryClient();

  const { data: defaults, isLoading } = useQuery({
    queryKey: ["resume-defaults"],
    queryFn: getResumeDefaults,
  });

  const saveMutation = useMutation({
    mutationFn: async (prefs: Partial<ResumeDefaults>) => {
      return updateResumeDefaults(prefs);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["resume-defaults"] });
      toast.success("Resume settings updated successfully");
    },
    onError: (error) => {
      toast.error(`Failed to update resume settings: ${error.message}`);
    },
  });

  const [selectedTemplate, setSelectedTemplate] = useState("Technical");
  const [autoTailor, setAutoTailor] = useState(true);
  const [exportFormat, setExportFormat] = useState("pdf");

  useEffect(() => {
    if (defaults) {
      const label = Object.keys(TEMPLATE_MAP).find(
        (key) => TEMPLATE_MAP[key] === defaults.default_template,
      );
      setSelectedTemplate(label ?? "Technical");
      setAutoTailor(defaults.auto_tailor_enabled);
      setExportFormat(defaults.export_format);
    }
  }, [defaults]);

  const handleSave = () => {
    const templateKey = TEMPLATE_MAP[selectedTemplate] || "modern";
    saveMutation.mutate({
      default_template: templateKey,
      auto_tailor_enabled: autoTailor,
      export_format: exportFormat,
    });
  };

  if (isLoading) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Loading resume settings...
      </div>
    );
  }

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Panel title="Default template">
        <div className="space-y-3 p-4">
          <div className="flex flex-wrap gap-2">
            {TEMPLATE_LABELS.map((t) => (
              <button key={t} onClick={() => setSelectedTemplate(t)} type="button">
                <Tag
                  className={
                    selectedTemplate === t
                      ? "bg-primary text-primary-foreground"
                      : "hover:bg-muted"
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
            onClick={() => {
              setAutoTailor(!autoTailor);
              saveMutation.mutate({ auto_tailor_enabled: !autoTailor });
            }}
          >
            {autoTailor ? "Enabled" : "Disabled"}
          </Button>
        </div>
      </Panel>
      <Panel title="Export defaults" className="lg:col-span-2">
        <div className="grid gap-3 p-4 sm:grid-cols-3 text-sm">
          <div>
            <div className="text-[10px] font-semibold uppercase text-muted-foreground">Format</div>
            {exportFormat.toUpperCase()}
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
