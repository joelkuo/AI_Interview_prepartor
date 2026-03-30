import { AnalysisResult, RehearsalResponse, SlideData } from "../types";

const BASE_URL = "http://localhost:8000";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`API ${res.status}: ${err}`);
  }
  return res.json() as Promise<T>;
}

export const apiClient = {
  async health(): Promise<{ status: string }> {
    return request("/api/health");
  },

  async createRehearsal(title: string, slides: SlideData[]): Promise<RehearsalResponse> {
    return request("/api/rehearsals", {
      method: "POST",
      body: JSON.stringify({ title, slides }),
    });
  },

  async listRehearsals(): Promise<{ rehearsals: RehearsalResponse[]; total: number }> {
    return request("/api/rehearsals");
  },

  async uploadAudio(rehearsalId: number, blob: Blob, filename: string): Promise<{ size_bytes: number }> {
    const formData = new FormData();
    formData.append("audio", blob, filename);
    const res = await fetch(`${BASE_URL}/api/rehearsals/${rehearsalId}/audio`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Upload failed ${res.status}: ${err}`);
    }
    return res.json();
  },

  async startAnalysis(rehearsalId: number): Promise<{ status: string }> {
    return request(`/api/rehearsals/${rehearsalId}/analyze`, { method: "POST" });
  },

  async getResults(rehearsalId: number): Promise<AnalysisResult> {
    return request(`/api/rehearsals/${rehearsalId}/results`);
  },

  async deleteRehearsal(rehearsalId: number): Promise<void> {
    const res = await fetch(`${BASE_URL}/api/rehearsals/${rehearsalId}`, { method: "DELETE" });
    if (!res.ok && res.status !== 204) {
      throw new Error(`Delete failed ${res.status}`);
    }
  },

  getExportUrl(rehearsalId: number): string {
    return `${BASE_URL}/api/rehearsals/${rehearsalId}/export`;
  },
};
