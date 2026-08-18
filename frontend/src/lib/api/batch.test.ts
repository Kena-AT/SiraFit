import { apiFetch } from "./client";
import {
  getBatchJobs,
  getBatchJob,
  createBatchJob,
  retryBatchJob,
  cancelBatchJob,
  type BatchJob,
} from "./batch";

// Mock apiFetch
jest.mock("./client");

const mockApiFetch = apiFetch as jest.MockedFunction<typeof apiFetch>;

describe("Batch API Client", () => {
  beforeEach(() => {
    mockApiFetch.mockClear();
  });

  describe("getBatchJobs", () => {
    it("should fetch batch jobs successfully", async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          jobs: [
            {
              id: "1",
              operation_type: "analyze",
              status: "completed",
              total_items: 5,
              processed_items: 5,
            },
          ],
          total: 1,
          skip: 0,
          limit: 50,
        }),
      };
      mockApiFetch.mockResolvedValue(mockResponse as any);

      const result = await getBatchJobs();
      expect(result.jobs).toHaveLength(1);
      expect(result.jobs[0].operation_type).toBe("analyze");
      expect(mockApiFetch).toHaveBeenCalledWith("/api/v1/batch");
    });

    it("should throw an error when fetching batch jobs fails", async () => {
      const mockResponse = {
        ok: false,
        json: jest.fn().mockResolvedValue({ detail: "Failed to fetch" }),
      };
      mockApiFetch.mockResolvedValue(mockResponse as any);

      await expect(getBatchJobs()).rejects.toThrow("Failed to fetch batch jobs");
    });
  });

  describe("getBatchJob", () => {
    it("should fetch a single batch job successfully", async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          id: "1",
          operation_type: "analyze",
          status: "completed",
          total_items: 5,
          processed_items: 5,
        }),
      };
      mockApiFetch.mockResolvedValue(mockResponse as any);

      const result = await getBatchJob("1");
      expect(result.id).toBe("1");
      expect(result.operation_type).toBe("analyze");
      expect(mockApiFetch).toHaveBeenCalledWith("/api/v1/batch/1");
    });

    it("should throw an error when fetching a batch job fails", async () => {
      const mockResponse = {
        ok: false,
        json: jest.fn().mockResolvedValue({ detail: "Failed to fetch" }),
      };
      mockApiFetch.mockResolvedValue(mockResponse as any);

      await expect(getBatchJob("1")).rejects.toThrow("Failed to fetch batch job");
    });
  });

  describe("createBatchJob", () => {
    it("should create a batch job successfully", async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          id: "1",
          operation_type: "analyze",
          status: "pending",
          total_items: 5,
        }),
      };
      mockApiFetch.mockResolvedValue(mockResponse as any);

      const result = await createBatchJob({
        operation_type: "analyze",
        job_ids: ["1", "2", "3", "4", "5"],
      });
      expect(result.id).toBe("1");
      expect(result.operation_type).toBe("analyze");
      expect(mockApiFetch).toHaveBeenCalledWith("/api/v1/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operation_type: "analyze",
          job_ids: ["1", "2", "3", "4", "5"],
        }),
      });
    });

    it("should throw an error when creating a batch job fails", async () => {
      const mockResponse = {
        ok: false,
        json: jest.fn().mockResolvedValue({ detail: "Failed to create" }),
      };
      mockApiFetch.mockResolvedValue(mockResponse as any);

      await expect(
        createBatchJob({
          operation_type: "analyze",
          job_ids: ["1", "2", "3", "4", "5"],
        }),
      ).rejects.toThrow("Failed to create batch job");
    });
  });

  describe("retryBatchJob", () => {
    it("should retry a batch job successfully", async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          id: "2",
          operation_type: "analyze",
          status: "pending",
          total_items: 2,
        }),
      };
      mockApiFetch.mockResolvedValue(mockResponse as any);

      const result = await retryBatchJob("1");
      expect(result.id).toBe("2");
      expect(result.operation_type).toBe("analyze");
      expect(mockApiFetch).toHaveBeenCalledWith("/api/v1/batch/1/retry", {
        method: "POST",
      });
    });

    it("should throw an error when retrying a batch job fails", async () => {
      const mockResponse = {
        ok: false,
        json: jest.fn().mockResolvedValue({ detail: "Failed to retry" }),
      };
      mockApiFetch.mockResolvedValue(mockResponse as any);

      await expect(retryBatchJob("1")).rejects.toThrow("Failed to retry batch job");
    });
  });

  describe("cancelBatchJob", () => {
    it("should cancel a batch job successfully", async () => {
      const mockResponse = {
        ok: true,
        json: jest.fn().mockResolvedValue({
          id: "1",
          operation_type: "analyze",
          status: "running",
          cancel_requested: true,
        }),
      };
      mockApiFetch.mockResolvedValue(mockResponse as any);

      const result = await cancelBatchJob("1");
      expect(result.id).toBe("1");
      expect(result.cancel_requested).toBe(true);
      expect(mockApiFetch).toHaveBeenCalledWith("/api/v1/batch/1/cancel", {
        method: "POST",
      });
    });

    it("should throw an error when cancelling a batch job fails", async () => {
      const mockResponse = {
        ok: false,
        json: jest.fn().mockResolvedValue({ detail: "Failed to cancel" }),
      };
      mockApiFetch.mockResolvedValue(mockResponse as any);

      await expect(cancelBatchJob("1")).rejects.toThrow("Failed to cancel batch job");
    });
  });
});