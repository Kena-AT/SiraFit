import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BatchJobCard } from "./BatchJobCard";
import { BatchJob } from "@/lib/api/batch";

const mockJob: BatchJob = {
  id: "1",
  user_id: "user1",
  operation_type: "analyze",
  status: "completed",
  total_items: 5,
  processed_items: 5,
  succeeded_items: 5,
  failed_items: 0,
  payload: { job_ids: ["1", "2", "3", "4", "5"] },
  result_summary: {},
  cancel_requested: false,
  started_at: "2023-01-01T00:00:00Z",
  completed_at: "2023-01-01T00:05:00Z",
  created_at: "2023-01-01T00:00:00Z",
  updated_at: "2023-01-01T00:05:00Z",
};

describe("BatchJobCard", () => {
  it("renders a completed batch job correctly", () => {
    render(<BatchJobCard job={mockJob} />);
    
    expect(screen.getByText("Analyze Batch Job")).toBeInTheDocument();
    expect(screen.getByText("Completed")).toBeInTheDocument();
    expect(screen.getByText("5 / 5 (100%)")).toBeInTheDocument();
  });

  it("renders a failed batch job correctly", () => {
    const failedJob = { ...mockJob, status: "failed", failed_items: 5 };
    render(<BatchJobCard job={failedJob} />);
    
    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getByText("Retry")).toBeInTheDocument();
  });

  it("renders a running batch job correctly", () => {
    const runningJob = { ...mockJob, status: "running", processed_items: 2 };
    render(<BatchJobCard job={runningJob} />);
    
    expect(screen.getByText("Running")).toBeInTheDocument();
    expect(screen.getByText("2 / 5 (40%)")).toBeInTheDocument();
    expect(screen.getByText("Cancel")).toBeInTheDocument();
  });

  it("calls onRetry when the retry button is clicked", () => {
    const failedJob = { ...mockJob, status: "failed" };
    const onRetry = jest.fn();
    render(<BatchJobCard job={failedJob} onRetry={onRetry} />);
    
    fireEvent.click(screen.getByText("Retry"));
    expect(onRetry).toHaveBeenCalledWith("1");
  });

  it("calls onCancel when the cancel button is clicked", () => {
    const runningJob = { ...mockJob, status: "running" };
    const onCancel = jest.fn();
    render(<BatchJobCard job={runningJob} onCancel={onCancel} />);
    
    fireEvent.click(screen.getByText("Cancel"));
    expect(onCancel).toHaveBeenCalledWith("1");
  });

  it("calls onViewDetails when the view details button is clicked", () => {
    const onViewDetails = jest.fn();
    render(<BatchJobCard job={mockJob} onViewDetails={onViewDetails} />);
    
    fireEvent.click(screen.getByText("View Details"));
    expect(onViewDetails).toHaveBeenCalledWith("1");
  });
});