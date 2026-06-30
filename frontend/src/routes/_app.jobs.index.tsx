import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { PageBody } from "@/components/sirafit/shell";
import { PageHeader, Panel, Tag, EmptyState } from "@/components/sirafit/bits";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { getJobs, type JobSearchParams } from "@/lib/api/jobs";
import type { JobListResponse } from "@/types/job";

export const Route = createFileRoute("/_app/jobs/")({
  head: () => ({ meta: [{ title: "Jobs Explorer · SiraFit" }] }),
  component: JobsExplorer,
});

function JobsExplorer() {
  const [data, setData] = useState<JobListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Search and filter state
  const [searchTerm, setSearchTerm] = useState("");
  const [activeSearch, setActiveSearch] = useState("");
  const [companyFilter, setCompanyFilter] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [sourceFilter, setSourceFilter] = useState("");
  const [page, setPage] = useState(0);
  const [sortBy, setSortBy] = useState("created_at");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  
  const limit = 50;

  const fetchJobs = async () => {
    setLoading(true);
    setError(null);
    
    const params: JobSearchParams = {
      skip: page * limit,
      limit,
      sort_by: sortBy,
      sort_order: sortOrder,
    };
    
    if (activeSearch) params.search = activeSearch;
    if (companyFilter) params.company = companyFilter;
    if (locationFilter) params.location = locationFilter;
    if (sourceFilter) params.source = sourceFilter;
    
    try {
      const result = await getJobs(params);
      setData(result);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [page, activeSearch, companyFilter, locationFilter, sourceFilter, sortBy, sortOrder]);

  const handleSearch = () => {
    setActiveSearch(searchTerm);
    setPage(0);
  };

  const handleClearFilters = () => {
    setSearchTerm("");
    setActiveSearch("");
    setCompanyFilter("");
    setLocationFilter("");
    setSourceFilter("");
    setPage(0);
  };

  const hasFilters = activeSearch || companyFilter || locationFilter || sourceFilter;

  const formatSalary = (job: any) => {
    if (!job.salary_min && !job.salary_max) return "—";
    const currency = job.currency || "$";
    if (job.salary_min && job.salary_max) {
      return `${currency}${(job.salary_min / 1000).toFixed(0)}k–${(job.salary_max / 1000).toFixed(0)}k`;
    }
    if (job.salary_max) return `${currency}${(job.salary_max / 1000).toFixed(0)}k`;
    return `${currency}${(job.salary_min / 1000).toFixed(0)}k+`;
  };

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      const now = new Date();
      const diffMs = now.getTime() - d.getTime();
      const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
      const diffDays = Math.floor(diffHours / 24);
      
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    } catch {
      return dateStr;
    }
  };

  return (
    <PageBody>
      <PageHeader
        eyebrow="Pipeline"
        title="Jobs Explorer"
        description={data ? `${data.total} jobs imported. Filter, search, and triage.` : "Browse and manage imported jobs"}
        actions={
          <>
            <Link to="/jobs/history" className="rounded-md bg-card px-3 py-1.5 text-sm font-medium ring-1 ring-border hover:bg-muted">Import history</Link>
            <Link to="/jobs/import" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background ring-1 ring-foreground hover:bg-foreground/90">Import jobs</Link>
          </>
        }
      />

      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <div className="relative flex max-w-md flex-1 gap-2">
            <Input 
              placeholder="Search role, company, description…" 
              className="h-9 bg-card" 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            />
            <Button size="sm" onClick={handleSearch} disabled={loading}>
              Search
            </Button>
          </div>
          {hasFilters && (
            <Button variant="outline" size="sm" onClick={handleClearFilters}>
              Clear filters
            </Button>
          )}
          <div className="ml-auto font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            {data ? `${data.jobs.length} showing` : "—"}
          </div>
        </div>

        {/* Quick Filters */}
        <div className="flex flex-wrap gap-2">
          <Input 
            placeholder="Company" 
            className="h-8 w-40 bg-card text-xs" 
            value={companyFilter}
            onChange={(e) => { setCompanyFilter(e.target.value); setPage(0); }}
          />
          <Input 
            placeholder="Location" 
            className="h-8 w-40 bg-card text-xs" 
            value={locationFilter}
            onChange={(e) => { setLocationFilter(e.target.value); setPage(0); }}
          />
          <select 
            className="h-8 rounded-md border border-border bg-card px-2 text-xs"
            value={sourceFilter}
            onChange={(e) => { setSourceFilter(e.target.value); setPage(0); }}
          >
            <option value="">All sources</option>
            <option value="linkedin">LinkedIn</option>
            <option value="indeed">Indeed</option>
            <option value="glassdoor">Glassdoor</option>
            <option value="greenhouse">Greenhouse</option>
            <option value="lever">Lever</option>
            <option value="description">Description</option>
            <option value="url">URL</option>
          </select>
          <select 
            className="h-8 rounded-md border border-border bg-card px-2 text-xs"
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [field, order] = e.target.value.split("-");
              setSortBy(field);
              setSortOrder(order as "asc" | "desc");
            }}
          >
            <option value="created_at-desc">Newest first</option>
            <option value="created_at-asc">Oldest first</option>
            <option value="company-asc">Company A-Z</option>
            <option value="company-desc">Company Z-A</option>
            <option value="title-asc">Title A-Z</option>
            <option value="title-desc">Title Z-A</option>
          </select>
        </div>
      </div>

      <Panel>
        {loading ? (
          <div className="flex items-center justify-center px-4 py-12 text-sm text-muted-foreground">
            <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-border border-t-foreground" />
            Loading jobs...
          </div>
        ) : error ? (
          <div className="px-4 py-8 text-center">
            <div className="text-sm text-destructive">{error}</div>
            <Button variant="outline" size="sm" className="mt-3" onClick={fetchJobs}>Retry</Button>
          </div>
        ) : !data || data.jobs.length === 0 ? (
          <EmptyState
            title="No jobs found"
            body={hasFilters ? "Try adjusting your filters" : "Import some jobs to get started"}
            action={<Link to="/jobs/import" className="rounded-md bg-foreground px-3 py-1.5 text-sm font-medium text-background">Import jobs</Link>}
          />
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="border-b border-border bg-muted/40 font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
                  <tr>
                    <th className="px-4 py-2.5 font-semibold">#</th>
                    <th className="px-4 py-2.5 font-semibold">Company</th>
                    <th className="px-4 py-2.5 font-semibold">Role</th>
                    <th className="px-4 py-2.5 font-semibold">Location</th>
                    <th className="px-4 py-2.5 font-semibold">Salary</th>
                    <th className="px-4 py-2.5 font-semibold">Source</th>
                    <th className="px-4 py-2.5 font-semibold">Tags</th>
                    <th className="px-4 py-2.5 font-semibold">Imported</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {data.jobs.map((j, i) => (
                    <tr key={j.id} className="group hover:bg-muted/30">
                      <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground tabular-nums">
                        {String(page * limit + i + 1).padStart(3, "0")}
                      </td>
                      <td className="px-4 py-3 font-medium">{j.company}</td>
                      <td className="px-4 py-3">
                        <Link 
                          to="/jobs/$jobId" 
                          params={{ jobId: j.id }} 
                          className="text-muted-foreground hover:text-foreground hover:underline"
                        >
                          {j.title}
                        </Link>
                      </td>
                      <td className="px-4 py-3 text-xs text-muted-foreground">{j.location || "—"}</td>
                      <td className="px-4 py-3 text-xs text-muted-foreground tabular-nums">{formatSalary(j)}</td>
                      <td className="px-4 py-3"><Tag>{j.source}</Tag></td>
                      <td className="px-4 py-3">
                        <div className="flex flex-wrap gap-1">
                          {j.tags.slice(0, 3).map((t) => (<Tag key={t}>{t}</Tag>))}
                          {j.tags.length > 3 && <Tag>+{j.tags.length - 3}</Tag>}
                        </div>
                      </td>
                      <td className="px-4 py-3 font-mono text-[11px] text-muted-foreground tabular-nums">
                        {formatDate(j.created_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <footer className="flex items-center justify-between border-t border-border bg-muted/30 px-4 py-2 text-[11px] text-muted-foreground">
              <div>
                Showing {page * limit + 1}–{Math.min((page + 1) * limit, data.total)} of {data.total}
              </div>
              <div className="flex gap-1.5">
                <button 
                  className="rounded border border-border bg-card px-2 py-0.5 hover:bg-muted disabled:opacity-50"
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                >
                  ←
                </button>
                <span className="px-2">Page {page + 1} of {Math.ceil(data.total / limit)}</span>
                <button 
                  className="rounded border border-border bg-card px-2 py-0.5 hover:bg-muted disabled:opacity-50"
                  onClick={() => setPage(p => p + 1)}
                  disabled={(page + 1) * limit >= data.total}
                >
                  →
                </button>
              </div>
            </footer>
          </>
        )}
      </Panel>
    </PageBody>
  );
}