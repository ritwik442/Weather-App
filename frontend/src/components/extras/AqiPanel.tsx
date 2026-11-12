import { Leaf } from 'lucide-react';
import type { AirQualityExtraValue, ExtraPiece } from '../../types/api';

interface Props {
  piece: ExtraPiece<AirQualityExtraValue>;
}

export function AqiPanel({ piece }: Props) {
  return (
    <section
      aria-label="Air quality"
      className="rounded-xl border border-stone-200 bg-white p-4"
    >
      <h3 className="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-stone-500">
        <Leaf aria-hidden className="h-4 w-4" />
        Air quality
      </h3>
      {piece.value ? (
        <dl className="mt-3 grid grid-cols-2 gap-3 text-sm sm:grid-cols-3">
          <Metric label="European AQI" value={piece.value.european_aqi} suffix="" category={aqiCategory(piece.value.european_aqi, 'eu')} />
          <Metric label="US AQI" value={piece.value.us_aqi} suffix="" category={aqiCategory(piece.value.us_aqi, 'us')} />
          <Metric label="PM2.5" value={piece.value.pm2_5} suffix=" µg/m³" />
          <Metric label="PM10" value={piece.value.pm10} suffix=" µg/m³" />
          <Metric label="Ozone" value={piece.value.ozone} suffix=" µg/m³" />
        </dl>
      ) : (
        <p className="mt-2 text-sm text-stone-600">Air quality unavailable right now.</p>
      )}
    </section>
  );
}

interface MetricProps {
  label: string;
  value: number | null;
  suffix?: string;
  category?: string;
}

function Metric({ label, value, suffix = '', category }: MetricProps) {
  return (
    <div className="rounded-lg border border-stone-200 bg-stone-50 p-3">
      <dt className="text-xs font-medium uppercase tracking-wide text-stone-500">
        {label}
      </dt>
      <dd className="mt-1 tabular-nums text-stone-900">
        {value === null || value === undefined ? '—' : `${Math.round(value * 10) / 10}${suffix}`}
      </dd>
      {category && <p className="mt-1 text-xs text-stone-600">{category}</p>}
    </div>
  );
}

function aqiCategory(value: number | null, scale: 'eu' | 'us'): string | undefined {
  if (value === null || value === undefined) return undefined;
  if (scale === 'eu') {
    if (value <= 20) return 'Good';
    if (value <= 40) return 'Fair';
    if (value <= 60) return 'Moderate';
    if (value <= 80) return 'Poor';
    if (value <= 100) return 'Very poor';
    return 'Extremely poor';
  }
  if (value <= 50) return 'Good';
  if (value <= 100) return 'Moderate';
  if (value <= 150) return 'Unhealthy — sensitive groups';
  if (value <= 200) return 'Unhealthy';
  if (value <= 300) return 'Very unhealthy';
  return 'Hazardous';
}
