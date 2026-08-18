import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader } from "@/components/sirafit/bits";
import { BatchJobList } from "@/components/sirafit/batch/BatchJobList";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/batch")({
  component: BatchJobsPage,
});

function BatchJobsPage() {
  return (
    <PageBody>
      <PageHeader
        eyebrow="Batch Processing"
        title="Batch Jobs"
        description="View and manage your batch operations."
        actions={
          <Link to="/jobs">
            <Button variant="outline">Back to Jobs</Button>
          </Link>
        }
      />
      <BatchJobList onViewDetails={(jobId) => {
        // Navigate to batch job details page (to be implemented)
        console.log("View details for batch job:", jobId);
      }} />
    </PageBody>
  );
}