export type Unit = 'c' | 'f';

export const UNIT_STORAGE_KEY = 'weather-app.unit';

export function cToF(celsius: number): number {
  return celsius * 1.8 + 32;
}

export function formatTemperature(celsius: number | null, unit: Unit, digits = 0): string {
  if (celsius === null || celsius === undefined || Number.isNaN(celsius)) return '—';
  const value = unit === 'c' ? celsius : cToF(celsius);
  const suffix = unit === 'c' ? '°C' : '°F';
  return `${value.toFixed(digits)}${suffix}`;
}

export function formatWindKmh(speedMs: number | null): string {
  if (speedMs === null || speedMs === undefined || Number.isNaN(speedMs)) return '—';
  return `${(speedMs * 3.6).toFixed(0)} km/h`;
}

export function formatPercent(value: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `${Math.round(value)}%`;
}

export function formatMm(value: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `${value.toFixed(1)} mm`;
}

export function formatPressure(value: number | null): string {
  if (value === null || value === undefined || Number.isNaN(value)) return '—';
  return `${Math.round(value)} hPa`;
}

export function loadUnit(): Unit {
  try {
    const raw = window.localStorage.getItem(UNIT_STORAGE_KEY);
    if (raw === 'c' || raw === 'f') return raw;
  } catch {
    // ignore private-mode / unavailable storage
  }
  return 'c';
}

export function saveUnit(unit: Unit): void {
  try {
    window.localStorage.setItem(UNIT_STORAGE_KEY, unit);
  } catch {
    // ignore
  }
}
