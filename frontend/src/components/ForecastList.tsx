import { describeWeatherCode } from '../lib/weatherCodes';
import { formatPercent, formatTemperature, type Unit } from '../lib/units';
import type { ForecastDay } from '../types/api';

interface Props {
  days: ForecastDay[];
  unit: Unit;
}

export function ForecastList({ days, unit }: Props) {
  if (!days.length) return null;
  return (
    <section
      aria-label="5-day forecast"
      className="rounded-xl border border-stone-200 bg-white p-6"
    >
      <h2 className="text-sm font-medium uppercase tracking-wide text-stone-500">
        Next 5 days
      </h2>
      <ol className="mt-4 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {days.map((d) => {
          const info = describeWeatherCode(d.weather_code);
          const Icon = info.icon;
          return (
            <li
              key={d.date}
              className="rounded-lg border border-stone-200 bg-stone-50 p-3"
            >
              <div className="text-xs font-medium uppercase tracking-wide text-stone-500">
                {formatDay(d.date)}
              </div>
              <div className="mt-2 flex items-center justify-between">
                <Icon aria-hidden className="h-7 w-7 text-stone-700" />
                <div className="text-right">
                  <div className="text-base font-semibold tabular-nums text-stone-900">
                    {formatTemperature(d.temp_max, unit)}
                  </div>
                  <div className="text-xs tabular-nums text-stone-500">
                    {formatTemperature(d.temp_min, unit)}
                  </div>
                </div>
              </div>
              <div className="mt-2 text-xs text-stone-600">{info.label}</div>
              <div className="text-xs text-stone-500">
                Rain {formatPercent(d.precipitation_probability_max)}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

function formatDay(iso: string): string {
  try {
    const d = new Date(`${iso}T12:00:00Z`);
    return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' });
  } catch {
    return iso;
  }
}
