import { createFileRoute, Link } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, StatusPill } from "@/components/sirafit/bits";
import { ArrowLeft } from "lucide-react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getBatchJob } from "@/lib/api/batch";
import { BatchDetailView } from "@/components/sirafit/batch/BatchDetailView";

export const Route = createFileRoute("/_app/batch/$id")({
  head: () => ({ meta: [{ title: "Batch job · SiraFit" }] }),
  component: BatchDetailPage,
});

function BatchDetailPage() {
  const { id } = Route.useParams();
  const queryClient = useQueryClient();

  const {
    data: batchJob,
    isLoading,
    refetch,
  } = useQuery({
    queryKey: ["batch-job", id],
    queryFn: () => getBatchJob(id),
  });

  if (isLoading || !batchJob) {
    return (
      <PageBody>
        <PageHeader eyebrow="Operations" title="Loading batch job..." />
        <div className="grid place-items-center py-20">Loading...</div>
      </PageBody>
    );
  }

  return (
    <PageBody>
      <PageHeader
        eyebrow="Operations"
        title={`${batchJob.operation_type.charAt(0).toUpperCase() + batchJob.operation_type.slice(1)} batch`}
        actions={
          <Link
            to="/batch"
            className="flex items-center gap-2 rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted"
          >
            <ArrowLeft className="w-4 h-4" /> Back
          </Link>
        }
      />
      <BatchDetailView batchJob={batchJob} onRefetch={refetch} />
    </PageBody>
  );
}
