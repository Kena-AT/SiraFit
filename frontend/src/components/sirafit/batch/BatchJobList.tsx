"use client";

import { useState, useEffect } from "react";
import { BatchJob, getBatchJobs, retryBatchJob, cancelBatchJob } from "@/lib/api/batch";
import { BatchJobCard } from "./BatchJobCard";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { RefreshCw } from "lucide-react";

interface BatchJobListProps {
  onViewDetails: (jobId: string) => void;
}

export function BatchJobList({ onViewDetails }: BatchJobListProps) {
  const [jobs, setJobs] = useState<BatchJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getBatchJobs();
      setJobs(data.jobs);
    } catch (err) {
      setError("Failed to fetch batch jobs.");
      console.error("Error fetching batch jobs:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleRetry = async (id: string) => {
    try {
      await retryBatchJob(id);
      fetchJobs();
    } catch (err) {
      setError("Failed to retry batch job.");
      console.error("Error retrying batch job:", err);
    }
  };

  const handleCancel = async (id: string) => {
    try {
      await cancelBatchJob(id);
      fetchJobs();
    } catch (err) {
      setError("Failed to cancel batch job.");
      console.error("Error cancelling batch job:", err);
    }
  };

  if (loading) {
    return (
      <div className="space-y-4">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-40 w-full" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  if (jobs.length === 0) {
    return (
      <Alert>
        <AlertTitle>No Batch Jobs</AlertTitle>
        <AlertDescription>You haven't created any batch jobs yet.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button variant="outline" size="sm" onClick={fetchJobs}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>
      <div className="space-y-4">
        {jobs.map(job => (
          <BatchJobCard
            key={job.id}
            job={job}
            onRetry={handleRetry}
            onCancel={handleCancel}
            onViewDetails={onViewDetails}
          />
        ))}
      </div>
    </div>
  );
}