const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface JobImportData {
    source_type: 'url' | 'description' | 'csv';
    data: string;
}

export const importJobs = async (data: JobImportData) => {
    const response = await fetch(`${API_BASE_URL}/api/v1/jobs/import`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(data),
    });
    if (!response.ok) {
        throw new Error('Failed to import jobs');
    }
    return response.json();
};

export const getImportHistory = async () => {
    const response = await fetch(`${API_BASE_URL}/api/v1/jobs/import/history`, {
        credentials: 'include',
    });
    if (!response.ok) {
        throw new Error('Failed to fetch import history');
    }
    return response.json();
};
