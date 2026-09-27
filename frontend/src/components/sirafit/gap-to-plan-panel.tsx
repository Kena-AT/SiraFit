import { useQuery } from "@tanstack/react-query";
import { getGapToPlan, GapToPlanResponse } from "@/lib/api/learning";
import { BookOpen, Code, ExternalLink, Clock, Sparkles, CheckCircle2 } from "lucide-react";

interface GapToPlanPanelProps {
  jobId: string;
}

export function GapToPlanPanel({ jobId }: GapToPlanPanelProps) {
  const { data, isLoading, error } = useQuery<GapToPlanResponse>({
    queryKey: ["gap-to-plan", jobId],
    queryFn: () => getGapToPlan(jobId),
  });

  if (isLoading) {
    return (
      <div className="rounded-xl border border-border/60 bg-muted/20 p-4 text-xs text-muted-foreground flex items-center gap-2">
        <span className="h-3 w-3 animate-spin rounded-full border-2 border-border border-t-foreground" />
        Calculating deterministic skill gap roadmap...
      </div>
    );
  }

  if (error || !data) {
    return null;
  }

  const { missing_skills, plan_items } = data;

  if (missing_skills.length === 0) {
    return (
      <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4 flex items-center gap-2.5 text-xs text-emerald-700 dark:text-emerald-400">
        <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-500" />
        <span>
          You match all identified skill requirements for this role! No learning gaps detected.
        </span>
      </div>
    );
  }

  const learningResources = plan_items.filter((item) => item.type === "learning_resource");
  const projectTemplates = plan_items.filter((item) => item.type === "project_template");

  return (
    <div className="space-y-3 rounded-xl border border-border/70 bg-card p-4 shadow-xs">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex h-6 w-6 items-center justify-center rounded-md bg-amber-500/10 text-amber-600 dark:text-amber-400">
            <Sparkles className="h-3.5 w-3.5" />
          </div>
          <h4 className="text-xs font-semibold uppercase tracking-wider text-foreground">
            Gap-to-Plan Action Roadmap
          </h4>
        </div>
        <span className="text-[11px] font-mono text-muted-foreground">
          {missing_skills.length} missing skill{missing_skills.length === 1 ? "" : "s"}
        </span>
      </div>

      {/* Missing Skills list */}
      <div className="flex flex-wrap gap-1.5 pt-1">
        {missing_skills.map((skill) => (
          <span
            key={skill}
            className="rounded-md bg-amber-500/10 px-2 py-0.5 text-[11px] font-medium text-amber-700 dark:text-amber-300 ring-1 ring-amber-500/20"
          >
            {skill}
          </span>
        ))}
      </div>

      {/* Curated Resources */}
      {learningResources.length > 0 && (
        <div className="space-y-2 pt-2">
          <div className="text-[11px] font-medium text-muted-foreground flex items-center gap-1.5">
            <BookOpen className="h-3.5 w-3.5 text-blue-500" />
            <span>Recommended Learning Resources</span>
          </div>
          <div className="space-y-1.5">
            {learningResources.map((res) => (
              <a
                key={res.id}
                href={res.url || "#"}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-2 rounded-lg bg-muted/40 hover:bg-muted/70 transition-colors text-xs group"
              >
                <div className="space-y-0.5 truncate pr-2">
                  <div className="font-medium text-foreground group-hover:text-blue-500 transition-colors truncate">
                    {res.title}
                  </div>
                  <div className="text-[10px] text-muted-foreground flex items-center gap-2">
                    {res.provider && <span>{res.provider}</span>}
                    {res.estimated_minutes && (
                      <span className="flex items-center gap-0.5">
                        <Clock className="h-3 w-3" /> {res.estimated_minutes}m
                      </span>
                    )}
                    {res.difficulty && <span className="capitalize">{res.difficulty}</span>}
                  </div>
                </div>
                <ExternalLink className="h-3.5 w-3.5 text-muted-foreground group-hover:text-blue-500 shrink-0" />
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Proof-of-Skill Projects */}
      {projectTemplates.length > 0 && (
        <div className="space-y-2 pt-2 border-t border-border/50">
          <div className="text-[11px] font-medium text-muted-foreground flex items-center gap-1.5">
            <Code className="h-3.5 w-3.5 text-emerald-500" />
            <span>Proof-of-Skill Projects</span>
          </div>
          <div className="space-y-1.5">
            {projectTemplates.map((proj) => (
              <div key={proj.id} className="p-2.5 rounded-lg bg-muted/40 text-xs space-y-1">
                <div className="flex items-start justify-between gap-2">
                  <span className="font-medium text-foreground">{proj.title}</span>
                  {proj.estimated_minutes && (
                    <span className="text-[10px] font-mono text-muted-foreground shrink-0 flex items-center gap-0.5">
                      <Clock className="h-3 w-3" /> ~{Math.round(proj.estimated_minutes / 60)}h
                    </span>
                  )}
                </div>
                {proj.skills && proj.skills.length > 0 && (
                  <div className="flex flex-wrap gap-1">
                    {proj.skills.map((s) => (
                      <span
                        key={s}
                        className="rounded bg-background px-1.5 py-0.5 text-[10px] text-muted-foreground ring-1 ring-border"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
