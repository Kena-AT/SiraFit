import { createFileRoute } from "@tanstack/react-router";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel } from "@/components/sirafit/bits";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/cover-letters/builder")({
  head: () => ({ meta: [{ title: "Cover letter builder · SiraFit" }] }),
  component: () => (
    <PageBody className="max-w-none">
      <PageHeader eyebrow="Assets · Builder" title="Cover letter — Stripe, Infra Engineer" description="Generated from job analysis + master profile. Edit freely; no AI loops in validation." actions={<><Button variant="outline">Re-generate</Button><Button>Save</Button></>} />
      <div className="grid gap-4 lg:grid-cols-2">
        <Panel title="Draft" actions={<span className="font-mono text-[10px] text-muted-foreground">218 words</span>}>
          <Textarea className="min-h-[420px] rounded-none border-0 border-border bg-card" defaultValue={`Dear Stripe hiring team,

I'm Alex Rivera, a junior software engineer who's spent the past 18 months building distributed services in Go at Cloud Scale Labs — exactly the kind of system reliability work I see your Infrastructure team owning today.

On a recent project I rewrote a Kafka-backed ingestion pipeline that cut p99 latency by 40% and added autoscaling that has held at peak load for four months. I'd love to bring that operational instinct to your payments infrastructure.

Outside of work I maintain a small open-source distributed scraper in Go, and I'm comfortable picking up gRPC and Terraform — both called out in the role.

Happy to share more or chat about how I think.

Alex`} />
        </Panel>
        <Panel title="Preview" bodyClassName="bg-muted/30 p-6">
          <div className="space-y-3 rounded-sm bg-card p-8 text-[13px] leading-relaxed shadow-2xl ring-1 ring-border">
            <p>Dear Stripe hiring team,</p>
            <p>I'm Alex Rivera, a junior software engineer who's spent the past 18 months building distributed services in Go at Cloud Scale Labs — exactly the kind of system reliability work I see your Infrastructure team owning today.</p>
            <p>On a recent project I rewrote a Kafka-backed ingestion pipeline that cut p99 latency by 40% and added autoscaling that has held at peak load for four months. I'd love to bring that operational instinct to your payments infrastructure.</p>
            <p>Outside of work I maintain a small open-source distributed scraper in Go, and I'm comfortable picking up gRPC and Terraform — both called out in the role.</p>
            <p>Happy to share more or chat about how I think.</p>
            <p>Alex</p>
          </div>
        </Panel>
      </div>
    </PageBody>
  ),
});