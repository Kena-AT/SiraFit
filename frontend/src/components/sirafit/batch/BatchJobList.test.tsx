import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BatchJobList } from "./BatchJobList";
import { getBatchJobs, retryBatchJob, cancelBatchJob } from "@/lib/api/batch";

// Mock the API functions
jest.mock("@/lib/api/batch");

const mockGetBatchJobs = getBatchJobs as jest.MockedFunction<typeof getBatchJobs>;
const mockRetryBatchJob = retryBatchJob as jest.MockedFunction<typeof retryBatchJob>;
const mockCancelBatchJob = cancelBatchJob as jest.MockedFunction<typeof cancelBatchJob>;

const mockJobs = [
  {
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
    created_at: "2023-01-01T00:00:00Z",
    updated_at: "2023-01-01T00:05:00Z",
  },
  {
    id: "2",
    user_id: "user1",
    operation_type: "score",
    status: "failed",
    total_items: 3,
    processed_items: 3,
    succeeded_items: 0,
    failed_items: 3,
    payload: { job_ids: ["6", "7", "8"] },
    result_summary: {},
    cancel_requested: false,
    created_at: "2023-01-02T00:00:00Z",
    updated_at: "2023-01-02T00:05:00Z",
  },
];

describe("BatchJobList", () => {
  beforeEach(() => {
    mockGetBatchJobs.mockClear();
    mockRetryBatchJob.mockClear();
    mockCancelBatchJob.mockClear();
  });

  it("shows a loading state initially", () => {
    mockGetBatchJobs.mockImplementation(() => new Promise(() => {}));
    render(<BatchJobList onViewDetails={jest.fn()} />);
    
    expect(screen.getAllByRole("progressbar")).toHaveLength(3);
  });

  it("shows an error message when fetching jobs fails", async () => {
    mockGetBatchJobs.mockRejectedValue(new Error("Failed to fetch"));
    render(<BatchJobList onViewDetails={jest.fn()} />);
    
    expect(await screen.findByText("Error")).toBeInTheDocument();
    expect(screen.getByText("Failed to fetch batch jobs.")).toBeInTheDocument();
  });

  it("shows a message when there are no jobs", async () => {
    mockGetBatchJobs.mockResolvedValue({ jobs: [], total: 0, skip: 0, limit: 50 });
    render(<BatchJobList onViewDetails={jest.fn()} />);
    
    expect(await screen.findByText("No Batch Jobs")).toBeInTheDocument();
    expect(screen.getByText("You haven't created any batch jobs yet.")).toBeInTheDocument();
  });

  it("renders a list of batch jobs", async () => {
    mockGetBatchJobs.mockResolvedValue({ jobs: mockJobs, total: 2, skip: 0, limit: 50 });
    render(<BatchJobList onViewDetails={jest.fn()} />);
    
    expect(await screen.findByText("Analyze Batch Job")).toBeInTheDocument();
    expect(screen.getByText("Score Batch Job")).toBeInTheDocument();
  });

  it("calls onViewDetails when the view details button is clicked", async () => {
    mockGetBatchJobs.mockResolvedValue({ jobs: mockJobs, total: 2, skip: 0, limit: 50 });
    const onViewDetails = jest.fn();
    render(<BatchJobList onViewDetails={onViewDetails} />);
    
    fireEvent.click(await screen.findByText("View Details"));
    expect(onViewDetails).toHaveBeenCalledWith("1");
  });

  it("calls retryBatchJob when the retry button is clicked", async () => {
    mockGetBatchJobs.mockResolvedValue({ jobs: mockJobs, total: 2, skip: 0, limit: 50 });
    mockRetryBatchJob.mockResolvedValue(mockJobs[1]);
    render(<BatchJobList onViewDetails={jest.fn()} />);
    
    fireEvent.click(await screen.findByText("Retry"));
    expect(mockRetryBatchJob).toHaveBeenCalledWith("2");
  });

  it("calls cancelBatchJob when the cancel button is clicked", async () => {
    const runningJob = { ...mockJobs[0], status: "running" };
    mockGetBatchJobs.mockResolvedValue({ jobs: [runningJob], total: 1, skip: 0, limit: 50 });
    mockCancelBatchJob.mockResolvedValue({ ...runningJob, cancel_requested: true });
    render(<BatchJobList onViewDetails={jest.fn()} />);
    
    fireEvent.click(await screen.findByText("Cancel"));
    expect(mockCancelBatchJob).toHaveBeenCalledWith("1");
  });

  it("refreshes the list when the refresh button is clicked", async () => {
    mockGetBatchJobs.mockResolvedValue({ jobs: mockJobs, total: 2, skip: 0, limit: 50 });
    render(<BatchJobList onViewDetails={jest.fn()} />);
    
    // Wait for initial render
    await screen.findByText("Analyze Batch Job");
    
    // Change the mock to return different data
    const newJobs = [
      { ...mockJobs[0], status: "running" },
    ];
    mockGetBatchJobs.mockResolvedValue({ jobs: newJobs, total: 1, skip: 0, limit: 50 });
    
    fireEvent.click(screen.getByText("Refresh"));
    expect(await screen.findByText("Running")).toBeInTheDocument();
  });
});