import type {
  ApiErrorBody,
  LocationResolveResponse,
  WeatherBundle,
} from '../types/api';

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1';

export class ApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly details: Record<string, unknown>;

  constructor(status: number, code: string, message: string, details: Record<string, unknown>) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      headers: { Accept: 'application/json', ...(init?.headers ?? {}) },
      ...init,
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Network error';
    throw new ApiError(0, 'NETWORK_ERROR', message, {});
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const text = await response.text();
  const parsed: unknown = text ? safeParse(text) : null;

  if (!response.ok) {
    const body = parsed as Partial<ApiErrorBody> | null;
    const err = body?.error;
    throw new ApiError(
      response.status,
      err?.code ?? 'HTTP_ERROR',
      err?.message ?? `HTTP ${response.status}`,
      err?.details ?? {},
    );
  }

  return parsed as T;
}

function safeParse(text: string): unknown {
  try {
    return JSON.parse(text);
  } catch {
    return text;
  }
}

export const api = {
  health: () => request<{ status: string }>('/health'),

  autocomplete: (q: string, signal?: AbortSignal) =>
    request<LocationResolveResponse>(
      `/locations/autocomplete?q=${encodeURIComponent(q)}`,
      { signal },
    ),

  resolve: (q: string, signal?: AbortSignal) =>
    request<LocationResolveResponse>(
      `/locations/resolve?q=${encodeURIComponent(q)}`,
      { signal },
    ),

  weather: (q: string, locationIndex?: number, signal?: AbortSignal) => {
    const params = new URLSearchParams({ q });
    if (locationIndex !== undefined) params.set('location_index', String(locationIndex));
    return request<WeatherBundle>(`/weather/current?${params.toString()}`, { signal });
  },
};
