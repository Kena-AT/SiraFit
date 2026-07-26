"use client";

import { useQuery } from "@tanstack/react-query";
import { getHealthStatus } from "@/lib/api/stats";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { useEffect } from "react";

interface HealthStatusProps {
  className?: string;
  showLabel?: boolean;
  showDetails?: boolean;
}

export function HealthStatusDot({ className, showLabel = true, showDetails = false }: HealthStatusProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["health-status"],
    queryFn: getHealthStatus,
    refetchInterval: 60000, // Refetch every 60 seconds
  });

  // If there's an error, use a fallback status
  const status = error ? {
    color: "gray",
    message: "Status unavailable",
    frontend: false,
    backend: false,
    database: false,
    deployment: false,
    agent_api: { connected: false, source: "none", error: "Failed to fetch status" },
  } : data || {
    color: "gray",
    message: "Checking status...",
    frontend: true,
    backend: false,
    database: false,
    deployment: false,
    agent_api: { connected: false, source: "none" },
  };

  // Get the appropriate color class
  const colorClass = getColorClass(status.color);

  // Determine what to show in the label
  const label = showLabel ? (
    status.agent_api.connected ? (
      `Agent: connected${status.agent_api.source === "env" ? " via .env" : ""}`
    ) : (
      ("error" in status.agent_api && status.agent_api.error) || "Agent: disconnected"
    )
  ) : null;

  if (isLoading && !data) {
    return showLabel ? (
      <span className="inline-flex items-center gap-1.5 font-mono text-[10px] font-medium uppercase tracking-widest text-muted-foreground">
        <span className="relative inline-flex h-1.5 w-1.5">
          <span className="relative inline-block h-1.5 w-1.5 rounded-full bg-gray-400" />
        </span>
        Checking status...
      </span>
    ) : (
      <span className="relative inline-flex h-1.5 w-1.5">
        <span className="relative inline-block h-1.5 w-1.5 rounded-full bg-gray-400" />
      </span>
    );
  }

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={`inline-flex items-center gap-1.5 font-mono text-[10px] font-medium uppercase tracking-widest ${className}`}>
          <span className="relative inline-flex h-1.5 w-1.5">
            {status.color.startsWith("blend:") ? (
              <span className="relative inline-flex h-1.5 w-1.5 overflow-hidden rounded-full">
                <span
                  className={`h-full w-1/2 ${getColorClass(status.color.split(":")[1])}`}
                  style={{ backgroundColor: getColorValue(status.color.split(":")[1]) }}
                />
                <span
                  className={`h-full w-1/2 ${getColorClass(status.color.split(":")[2])}`}
                  style={{ backgroundColor: getColorValue(status.color.split(":")[2]) }}
                />
              </span>
            ) : (
              <span className={`relative inline-block h-1.5 w-1.5 rounded-full ${colorClass}`} />
            )}
          </span>
          {label}
        </span>
      </TooltipTrigger>
      {showDetails && (
        <TooltipContent className="max-w-xs p-3 text-xs">
          <div className="space-y-2">
            <div className="font-semibold">{status.message}</div>
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className={`inline-block h-2 w-2 rounded-full ${status.frontend ? "bg-green-500" : "bg-red-500"}`} />
                <span>Frontend: {status.frontend ? "Healthy" : "Unhealthy"}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`inline-block h-2 w-2 rounded-full ${status.backend ? "bg-green-500" : "bg-red-500"}`} />
                <span>Backend: {status.backend ? "Healthy" : "Unhealthy"}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`inline-block h-2 w-2 rounded-full ${status.database ? "bg-green-500" : "bg-red-500"}`} />
                <span>Database: {status.database ? "Healthy" : "Unhealthy"}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`inline-block h-2 w-2 rounded-full ${status.deployment ? "bg-green-500" : "bg-red-500"}`} />
                <span>Deployment: {status.deployment ? "Healthy" : "Unhealthy"}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`inline-block h-2 w-2 rounded-full ${status.agent_api.connected ? "bg-green-500" : "bg-red-500"}`} />
                <span>
                  Agent API: {status.agent_api.connected ? "Connected" : "Disconnected"}
                  {status.agent_api.source !== "none" && (
                    <span className="text-muted-foreground">
                      
                      {status.agent_api.source === "env" ? " (env)" : " (settings)"}
                    </span>
                  )}
                </span>
              </div>
            </div>
            {"error" in status.agent_api && status.agent_api.error && (
              <div className="mt-2 text-red-500">
                Error: {status.agent_api.error}
              </div>
            )}
          </div>
        </TooltipContent>
      )}
    </Tooltip>
  );
}

function getColorClass(color: string): string {
  switch (color) {
    case "green": return "bg-green-500";
    case "blue": return "bg-blue-500";
    case "yellow": return "bg-yellow-500";
    case "purple": return "bg-purple-500";
    case "orange": return "bg-orange-500";
    case "red": return "bg-red-500";
    default: return "bg-gray-400";
  }
}

function getColorValue(color: string): string {
  switch (color) {
    case "green": return "#22c55e";
    case "blue": return "#3b82f6";
    case "yellow": return "#eab308";
    case "purple": return "#8b5cf6";
    case "orange": return "#f97316";
    case "red": return "#ef4444";
    default: return "#9ca3af";
  }
}