import {
  Compass,
  Droplets,
  Eye,
  Gauge,
  Sunrise,
  Sunset,
  Thermometer,
  Umbrella,
  Wind,
  type LucideIcon,
} from 'lucide-react';
import { describeWeatherCode } from '../lib/weatherCodes';
import {
  formatMm,
  formatPercent,
  formatPressure,
  formatTemperature,
  formatWindKmh,
  type Unit,
} from '../lib/units';
import type { CurrentWeather, LocationCandidate } from '../types/api';

interface Props {
  location: LocationCandidate;
  current: CurrentWeather;
  unit: Unit;
}

export function CurrentWeatherCard({ location, current, unit }: Props) {
  const description = describeWeatherCode(current.weather_code);
  const Icon = description.icon;
  return (
    <section
      aria-label="Current weather"
      className="rounded-xl border border-stone-200 bg-white p-6"
    >
      <header className="flex flex-wrap items-start justify-between gap-2">
        <div>
          <h2 className="text-xl font-semibold text-stone-900">
            {location.display_name}
          </h2>
          <p className="text-xs text-stone-500">
            {current.time ? formatLocalTime(current.time, current.timezone) : 'Right now'}
            {current.timezone ? ` · ${current.timezone}` : ''}
          </p>
        </div>
        <div className="text-right">
          <div className="flex items-center justify-end gap-3">
            <Icon aria-hidden className="h-10 w-10 text-stone-700" />
            <div className="text-4xl font-semibold tabular-nums text-stone-900">
              {formatTemperature(current.temperature, unit)}
            </div>
          </div>
          <div className="text-sm text-stone-600">{description.label}</div>
          <div className="text-xs text-stone-500">
            Feels {formatTemperature(current.feels_like, unit)} · H{' '}
            {formatTemperature(current.temp_max_today, unit)} · L{' '}
            {formatTemperature(current.temp_min_today, unit)}
          </div>
        </div>
      </header>

      <dl className="mt-6 grid grid-cols-2 gap-4 text-sm text-stone-700 md:grid-cols-4">
        <Stat icon={Droplets} label="Humidity" value={formatPercent(current.humidity)} />
        <Stat icon={Wind} label="Wind" value={formatWindKmh(current.wind_speed)} />
        <Stat
          icon={Compass}
          label="Direction"
          value={current.wind_direction !== null ? `${Math.round(current.wind_direction)}°` : '—'}
        />
        <Stat
          icon={Umbrella}
          label="Precipitation"
          value={`${formatMm(current.precipitation)} · ${formatPercent(current.precipitation_probability)}`}
        />
        <Stat
          icon={Thermometer}
          label="UV"
          value={current.uv_index !== null ? current.uv_index.toFixed(1) : '—'}
        />
        <Stat icon={Eye} label="Visibility" value={formatKm(current.visibility)} />
        <Stat icon={Gauge} label="Pressure" value={formatPressure(current.pressure)} />
        <Stat
          icon={Sunrise}
          label="Sunrise / Sunset"
          value={`${formatClock(current.sunrise)} · ${formatClock(current.sunset)}`}
          secondaryIcon={Sunset}
        />
      </dl>
    </section>
  );
}

interface StatProps {
  icon: LucideIcon;
  label: string;
  value: string;
  secondaryIcon?: LucideIcon;
}

function Stat({ icon: Icon, label, value, secondaryIcon: Secondary }: StatProps) {
  return (
    <div className="rounded-lg border border-stone-200 bg-stone-50 px-3 py-3">
      <dt className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-stone-500">
        <Icon aria-hidden className="h-3.5 w-3.5" />
        {Secondary && <Secondary aria-hidden className="h-3.5 w-3.5" />}
        <span>{label}</span>
      </dt>
      <dd className="mt-1 tabular-nums text-stone-900">{value}</dd>
    </div>
  );
}

function formatKm(meters: number | null): string {
  if (meters === null || meters === undefined || Number.isNaN(meters)) return '—';
  return `${(meters / 1000).toFixed(1)} km`;
}

function formatClock(iso: string | null): string {
  if (!iso) return '—';
  const timePart = iso.includes('T') ? iso.split('T')[1] : iso;
  return timePart?.slice(0, 5) ?? '—';
}

function formatLocalTime(iso: string, tz: string | null): string {
  try {
    const d = new Date(iso);
    return d.toLocaleString(undefined, {
      dateStyle: 'medium',
      timeStyle: 'short',
      timeZone: tz ?? undefined,
    });
  } catch {
    return iso;
  }
}
