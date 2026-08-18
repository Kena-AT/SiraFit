"use client";

import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { BatchJob } from "@/lib/api/batch";
import { formatDistanceToNow } from "date-fns";
import { Clock, CheckCircle2, XCircle, AlertCircle, PlayCircle, StopCircle } from "lucide-react";

interface BatchJobCardProps {
  job: BatchJob;
  onRetry?: (id: string) => void;
  onCancel?: (id: string) => void;
  onViewDetails?: (id: string) => void;
}

export function BatchJobCard({ job, onRetry, onCancel, onViewDetails }: BatchJobCardProps) {
  const getStatusIcon = () => {
    switch (job.status) {
      case "pending":
        return <Clock className="h-4 w-4 text-blue-500" />;
      case "running":
        return <PlayCircle className="h-4 w-4 text-blue-500" />;
      case "completed":
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case "failed":
        return <XCircle className="h-4 w-4 text-red-500" />;
      case "partial":
        return <AlertCircle className="h-4 w-4 text-yellow-500" />;
      case "cancelled":
        return <StopCircle className="h-4 w-4 text-gray-500" />;
      default:
        return null;
    }
  };

  const getStatusLabel = () => {
    switch (job.status) {
      case "pending":
        return "Pending";
      case "running":
        return "Running";
      case "completed":
        return "Completed";
      case "failed":
        return "Failed";
      case "partial":
        return "Partial";
      case "cancelled":
        return "Cancelled";
      default:
        return job.status;
    }
  };

  const progress = job.total_items > 0 ? (job.processed_items / job.total_items) * 100 : 0;

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <CardTitle className="text-sm font-medium capitalize">
            {job.operation_type} Batch Job
          </CardTitle>
        </div>
        <Badge variant={job.status === "completed" ? "success" : job.status === "failed" ? "destructive" : job.status === "partial" ? "warning" : "secondary"}>
          {getStatusLabel()}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Progress</span>
            <span>
              {job.processed_items} / {job.total_items} ({Math.round(progress)}%)
            </span>
          </div>
          <Progress value={progress} className="h-2" />
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-muted-foreground">Created</span>
          <span>
            {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
          </span>
        </div>
        {job.started_at && (
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Started</span>
            <span>
              {formatDistanceToNow(new Date(job.started_at), { addSuffix: true })}
            </span>
          </div>
        )}
        {job.completed_at && (
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Completed</span>
            <span>
              {formatDistanceToNow(new Date(job.completed_at), { addSuffix: true })}
            </span>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-end gap-2">
        {job.status === "failed" || job.status === "partial" ? (
          <Button variant="outline" size="sm" onClick={() => onRetry?.(job.id)}>
            Retry
          </Button>
        ) : job.status === "running" || job.status === "pending" ? (
          <Button variant="outline" size="sm" onClick={() => onCancel?.(job.id)}>
            Cancel
          </Button>
        ) : null}
        <Button variant="outline" size="sm" onClick={() => onViewDetails?.(job.id)}>
          View Details
        </Button>
      </CardFooter>
    </Card>
  );
}