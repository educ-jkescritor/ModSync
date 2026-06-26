import type { ReviewReport } from "./types";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export async function analyzePdf(file: File): Promise<ReviewReport> {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: "POST",
    body
  });

  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.detail ?? "PDF analysis failed.");
  }

  return response.json();
}

export async function submitFeedback(payload: {
  upload_id?: number;
  technology: string;
  decision: string;
  faculty_rationale?: string;
  original_recommendation: string;
}): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/feedback`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: jsonStringify(payload),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail ?? "Failed to save feedback.");
  }
}

// Simple helper to avoid type errors
function jsonStringify(obj: any): string {
  return JSON.stringify(obj);
}


