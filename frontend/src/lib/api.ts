const BASE_URL = "/api";

export interface FieldError {
  field: string;
  issue: string;
}

export class ApiError extends Error {
  type: string;
  fields: FieldError[];
  status: number;

  constructor(message: string, type: string, status: number, fields: FieldError[] = []) {
    super(message);
    this.name = "ApiError";
    this.type = type;
    this.fields = fields;
    this.status = status;
  }

  /** Convert field-level errors to a Record<fieldName, message> for inline display */
  toFieldErrors(): Record<string, string> {
    const result: Record<string, string> = {};
    for (const f of this.fields) {
      result[f.field] = f.issue;
    }
    return result;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    // Structured error response from our backend
    if (body.error && typeof body.error === "object") {
      throw new ApiError(
        body.error.message || "API request failed",
        body.error.type || "SERVER_ERROR",
        res.status,
        body.error.fields || []
      );
    }
    throw new ApiError(
      body.detail || "API request failed",
      "SERVER_ERROR",
      res.status
    );
  }
  // 204 No Content
  if (res.status === 204) {
    return undefined as T;
  }
  return res.json();
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "POST", body: JSON.stringify(body) }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: "PUT", body: JSON.stringify(body) }),
  delete: <T>(path: string) => request<T>(path, { method: "DELETE" }),
};
