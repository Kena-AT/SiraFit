"use client";

import { useState, type ChangeEvent } from "react";
import { X } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectTrigger,
  SelectContent,
  SelectItem,
  SelectValue,
} from "@/components/ui/select";
import {
  RadioGroup,
  RadioGroupItem,
} from "@/components/ui/radio-group";
import type { Job } from "@/types/job";

interface BatchCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (input: {
    operation_type: "analyze" | "score" | "tag" | "archive";
    job_ids: string[];
    params?: Record<string, unknown>;
  }) => void;
  availableJobs: Job[];
}

export function BatchCreateModal({
  isOpen,
  onClose,
  onSubmit,
  availableJobs,
}: BatchCreateModalProps) {
  if (!isOpen) return null;

  const [operation, setOperation] = useState<
    "analyze" | "score" | "tag" | "archive"
  >("analyze");
  const [selectedJobIds, setSelectedJobIds] = useState<string[]>([]);
  const [selectAll, setSelectAll] = useState(false);
  const [tags, setTags] = useState("");
  const [tagAction, setTagAction] = useState<"add" | "remove">("add");
  const [archiveTarget, setArchiveTarget] = useState<"jobs" | "applications">(
    "jobs"
  );

  const handleJobToggle = (id: string) => {
    setSelectedJobIds((prev) =>
      prev.includes(id) ? prev.filter((j) => j !== id) : [...prev, id]
    );
  };

  const handleSelectAllChange = (checked: boolean) => {
    setSelectAll(checked);
    if (checked) {
      setSelectedJobIds(availableJobs.map((j) => j.id));
    } else {
      setSelectedJobIds([]);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const params: Record<string, unknown> = {};
    if (operation === "tag") {
      params.tags = tags
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean);
      params.action = tagAction;
    } else if (operation === "archive") {
      params.target = archiveTarget;
    }
    onSubmit({ operation_type: operation, job_ids: selectedJobIds, params });
    onClose();
  };

  const filteredJobs = availableJobs;

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>New Batch Job</span>
            <button onClick={onClose} className="p-1 hover:bg-muted rounded">
              <X size={18} />
            </button>
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4 py-2">
          <div>
            <Label className="block mb-2">Operation</Label>
            <Select
              value={operation}
              onValueChange={(val) =>
                setOperation(val as "analyze" | "score" | "tag" | "archive")
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Select operation" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="analyze">Batch AI Analysis</SelectItem>
                <SelectItem value="score">Batch Match Scoring</SelectItem>
                <SelectItem value="tag">Batch Tagging</SelectItem>
                <SelectItem value="archive">Batch Archive</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label className="block mb-2">
              Jobs ({selectedJobIds.length} selected)
            </Label>
            <div className="max-h-48 overflow-y-auto border border-input rounded-md p-2 space-y-1">
              {filteredJobs.length === 0 ? (
                <div className="text-sm text-muted-foreground p-2">
                  No jobs available
                </div>
              ) : (
                filteredJobs.map((job) => (
                  <label
                    key={job.id}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <Checkbox
                      checked={selectAll || selectedJobIds.includes(job.id)}
                      onCheckedChange={(checked) => handleJobToggle(job.id)}
                    />
                    <span className="text-sm">
                      {job.company} – {job.title}
                    </span>
                  </label>
                ))
              )}
            </div>
          </div>

          {operation === "tag" && (
            <div className="space-y-2">
              <Label>Tags (comma-separated)</Label>
              <Input
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="remote, senior, python"
              />
              <RadioGroup value={tagAction} onValueChange={setTagAction}>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2">
                    <RadioGroupItem value="add" /> Add
                  </label>
                  <label className="flex items-center gap-2">
                    <RadioGroupItem value="remove" /> Remove
                  </label>
                </div>
              </RadioGroup>
            </div>
          )}

          {operation === "archive" && (
            <div>
              <Label>Target</Label>
              <RadioGroup value={archiveTarget} onValueChange={setArchiveTarget}>
                <div className="flex items-center gap-4">
                  <label className="flex items-center gap-2">
                    <RadioGroupItem value="jobs" /> Jobs
                  </label>
                  <label className="flex items-center gap-2">
                    <RadioGroupItem value="applications" /> Applications
                  </label>
                </div>
              </RadioGroup>
            </div>
          )}

          <DialogFooter className="flex gap-2 pt-2">
            <Button type="button" variant="ghost" onClick={onClose}>
              Cancel
            </Button>
            <Button
              type="submit"
              disabled={selectedJobIds.length === 0}
              className="ml-auto"
            >
              Create Batch Job
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}