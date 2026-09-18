import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { fetchSystemStatus, SystemHealthState } from "@/lib/api/status";
import { 
  Activity, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  RefreshCw, 
  Database, 
  Server, 
  Zap, 
  Cpu 
} from "lucide-react";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/status")({
  component: SystemStatusPage,
});

function getStatusBadge(state: SystemHealthState) {
  switch (state) {
    case "healthy":
      return {
        icon: <CheckCircle2 className="w-5 h-5 text-emerald-500" />,
        bg: "bg-emerald-500/10 text-emerald-500 border-emerald-500/20",
        label: "Operational",
      };
    case "degraded":
      return {
        icon: <AlertTriangle className="w-5 h-5 text-amber-500" />,
        bg: "bg-amber-500/10 text-amber-500 border-amber-500/20",
        label: "Degraded",
      };
    case "failed":
      return {
        icon: <XCircle className="w-5 h-5 text-rose-500" />,
        bg: "bg-rose-500/10 text-rose-500 border-rose-500/20",
        label: "Major Outage",
      };
    default:
      return {
        icon: <Activity className="w-5 h-5 text-muted-foreground" />,
        bg: "bg-muted text-muted-foreground border-border",
        label: "Unknown",
      };
  }
}

export default function SystemStatusPage() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ["system-status"],
    queryFn: fetchSystemStatus,
    refetchInterval: 30000,
  });

  const overallBadge = getStatusBadge(
    isLoading ? "unknown" : isError ? "failed" : data?.overall || "unknown"
  );

  const components = [
    {
      name: "API & Web Services",
      desc: "Handles incoming HTTP/REST requests and frontend web sessions.",
      icon: <Server className="w-5 h-5 text-primary" />,
      status: data?.api || "unknown",
    },
    {
      name: "PostgreSQL Database",
      desc: "Persistent relational store and vector similarity search.",
      icon: <Database className="w-5 h-5 text-primary" />,
      status: data?.database || "unknown",
    },
    {
      name: "Redis & Cache Layer",
      desc: "In-memory cache, WebSocket real-time bus, and rate-limiting store.",
      icon: <Zap className="w-5 h-5 text-primary" />,
      status: data?.redis || "unknown",
    },
    {
      name: "Background Job Workers",
      desc: "Asynchronous task queue for resume generation, tailoring, and imports.",
      icon: <Cpu className="w-5 h-5 text-primary" />,
      status: data?.background_jobs || "unknown",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Status</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Real-time status of SiraFit platform services and infrastructure.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => refetch()}
          disabled={isFetching}
          className="gap-2"
        >
          <RefreshCw className={`w-4 h-4 ${isFetching ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {/* Overall Banner */}
      <div className={`p-6 rounded-xl border flex items-center justify-between ${overallBadge.bg}`}>
        <div className="flex items-center gap-4">
          {overallBadge.icon}
          <div>
            <h2 className="text-lg font-semibold">
              {data?.overall === "healthy"
                ? "All Systems Operational"
                : data?.overall === "degraded"
                ? "Experiencing Degraded Performance"
                : isError || data?.overall === "failed"
                ? "Service Outage Detected"
                : "Checking System Status..."}
            </h2>
            <p className="text-xs opacity-90">
              {data?.last_checked
                ? `Last verified: ${new Date(data.last_checked).toLocaleTimeString()}`
                : "Waiting for status heartbeat..."}
            </p>
          </div>
        </div>
        <span className="text-xs font-semibold px-2.5 py-1 rounded-full border border-current uppercase tracking-wider">
          {overallBadge.label}
        </span>
      </div>

      {/* Component Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {components.map((comp) => {
          const badge = getStatusBadge(comp.status);
          return (
            <div
              key={comp.name}
              className="p-5 rounded-lg border bg-card text-card-foreground shadow-xs flex flex-col justify-between"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-md bg-muted/60">{comp.icon}</div>
                  <div>
                    <h3 className="text-base font-medium">{comp.name}</h3>
                    <p className="text-xs text-muted-foreground mt-0.5">{comp.desc}</p>
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-3 border-t flex items-center justify-between">
                <span className="text-xs text-muted-foreground">Status</span>
                <div className="flex items-center gap-1.5">
                  <span className={`inline-block w-2 h-2 rounded-full ${
                    comp.status === "healthy" ? "bg-emerald-500" :
                    comp.status === "degraded" ? "bg-amber-500" :
                    comp.status === "failed" ? "bg-rose-500" : "bg-muted-foreground"
                  }`} />
                  <span className="text-xs font-medium capitalize">{comp.status}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Footer Info */}
      <div className="text-xs text-muted-foreground text-center pt-4">
        Automatic polling every 30 seconds. Metrics and telemetry gathered without sensitive exposure.
      </div>
    </div>
  );
}
