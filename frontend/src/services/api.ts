import type { Meeting, MeetingStatusResponse } from "../types/meeting";

const API_BASE = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, init);
  } catch {
    throw new Error("Cannot reach the server. Check that the backend is running.");
  }
  if (!response.ok) {
    let message = `Request failed (${response.status}).`;
    try {
      const body = await response.json();
      if (typeof body.detail === "string") message = body.detail;
    } catch {
      // Keep the status-based message when the server response is not JSON.
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export function uploadAudio(file: File): Promise<Meeting> {
  const form = new FormData();
  form.append("audio", file);
  return request<Meeting>("/api/meetings/upload", { method: "POST", body: form });
}

export function startProcessing(id: string): Promise<Meeting> {
  return request<Meeting>(`/api/meetings/${id}/process`, { method: "POST" });
}

export function getMeeting(id: string): Promise<Meeting> {
  return request<Meeting>(`/api/meetings/${id}`);
}

export function getMeetingStatus(id: string): Promise<MeetingStatusResponse> {
  return request<MeetingStatusResponse>(`/api/meetings/${id}/status`);
}

export function downloadUrl(id: string, format: string): string {
  return `${API_BASE}/api/meetings/${id}/download/${format}`;
}
