import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import { BatchCreateModal } from "./BatchCreateModal";
import { Job } from "@/types/job";

const mockJobs: Job[] = [
  {
    id: "1",
    title: "Software Engineer",
    company: "Test Company",
    source: "linkedin",
    created_at: "2023-01-01T00:00:00Z",
    updated_at: "2023-01-01T00:00:00Z",
    tags: [],
  },
  {
    id: "2",
    title: "Frontend Developer",
    company: "Another Company",
    source: "indeed",
    created_at: "2023-01-02T00:00:00Z",
    updated_at: "2023-01-02T00:00:00Z",
    tags: [],
  },
];

describe("BatchCreateModal", () => {
  it("renders the modal when open", () => {
    render(
      <BatchCreateModal
        isOpen={true}
        onClose={jest.fn()}
        onSubmit={jest.fn()}
        selectedJobs={mockJobs}
      />
    );
    
    expect(screen.getByText("Create Batch Job")).toBeInTheDocument();
    expect(screen.getByText("Select an operation to perform on 2 job(s).")).toBeInTheDocument();
  });

  it("does not render the modal when closed", () => {
    render(
      <BatchCreateModal
        isOpen={false}
        onClose={jest.fn()}
        onSubmit={jest.fn()}
        selectedJobs={mockJobs}
      />
    );
    
    expect(screen.queryByText("Create Batch Job")).not.toBeInTheDocument();
  });

  it("calls onClose when the cancel button is clicked", () => {
    const onClose = jest.fn();
    render(
      <BatchCreateModal
        isOpen={true}
        onClose={onClose}
        onSubmit={jest.fn()}
        selectedJobs={mockJobs}
      />
    );
    
    fireEvent.click(screen.getByText("Cancel"));
    expect(onClose).toHaveBeenCalled();
  });

  it("calls onSubmit with the selected operation type when the create button is clicked", () => {
    const onSubmit = jest.fn();
    render(
      <BatchCreateModal
        isOpen={true}
        onClose={jest.fn()}
        onSubmit={onSubmit}
        selectedJobs={mockJobs}
      />
    );
    
    // Select "score" operation
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "score" } });
    fireEvent.click(screen.getByText("Create Batch Job"));
    
    expect(onSubmit).toHaveBeenCalledWith("score", ["1", "2"]);
  });
});