"use client";

import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { BatchOperationType } from "@/lib/api/batch";
import { Job } from "@/types/job";

interface BatchCreateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (operationType: BatchOperationType, jobIds: string[]) => void;
  selectedJobs: Job[];
}

export function BatchCreateModal({ isOpen, onClose, onSubmit, selectedJobs }: BatchCreateModalProps) {
  const [operationType, setOperationType] = useState<BatchOperationType>("analyze");

  const handleSubmit = () => {
    onSubmit(operationType, selectedJobs.map(job => job.id));
    onClose();
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create Batch Job</DialogTitle>
          <DialogDescription>
            Select an operation to perform on {selectedJobs.length} job(s).
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="operation-type">Operation Type</Label>
            <Select value={operationType} onValueChange={(value) => setOperationType(value as BatchOperationType)}>
              <SelectTrigger id="operation-type">
                <SelectValue placeholder="Select operation type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="analyze">Analyze Jobs</SelectItem>
                <SelectItem value="score">Calculate Match Scores</SelectItem>
                <SelectItem value="tag">Tag Jobs</SelectItem>
                <SelectItem value="archive">Archive Jobs</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit}>Create Batch Job</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}