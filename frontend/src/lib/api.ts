import type {
  ApiErrorBody,
  CreateRequestPayload,
  LocationExtras,
  LocationResolveResponse,
  SavedRequest,
  SavedRequestListResponse,
  UpdateRequestPayload,
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

export interface ListRequestsParams {
  q?: string;
  sort?: string;
  page?: number;
  pageSize?: number;
}

export type ExportFormat = 'json' | 'csv' | 'xml' | 'md' | 'pdf';

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

  extras: (lat: number, lon: number, name: string, signal?: AbortSignal) => {
    const params = new URLSearchParams({
      lat: String(lat),
      lon: String(lon),
      name,
    });
    return request<LocationExtras>(`/locations/extras?${params.toString()}`, { signal });
  },

  listRequests: (params: ListRequestsParams = {}, signal?: AbortSignal) => {
    const qs = new URLSearchParams();
    if (params.q) qs.set('q', params.q);
    if (params.sort) qs.set('sort', params.sort);
    if (params.page) qs.set('page', String(params.page));
    if (params.pageSize) qs.set('page_size', String(params.pageSize));
    const suffix = qs.toString();
    return request<SavedRequestListResponse>(`/requests${suffix ? `?${suffix}` : ''}`, {
      signal,
    });
  },

  getRequest: (id: number, signal?: AbortSignal) =>
    request<SavedRequest>(`/requests/${id}`, { signal }),

  createRequest: (payload: CreateRequestPayload) =>
    request<SavedRequest>('/requests', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  updateRequest: (id: number, payload: UpdateRequestPayload) =>
    request<SavedRequest>(`/requests/${id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }),

  deleteRequest: (id: number) =>
    request<void>(`/requests/${id}`, { method: 'DELETE' }),

  exportUrl: (format: ExportFormat, ids?: number[]): string => {
    const qs = new URLSearchParams({ format });
    if (ids && ids.length) qs.set('ids', ids.join(','));
    return `${API_BASE_URL}/requests/export?${qs.toString()}`;
  },
};
