import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';
import { cToF, type Unit } from '../../lib/units';
import type { DailyTemperature } from '../../types/api';

interface Props {
  rows: DailyTemperature[];
  unit: Unit;
}

export function TemperatureChart({ rows, unit }: Props) {
  const data = rows.map((r) => ({
    date: r.date.slice(5),
    max: convert(r.temp_max, unit),
    min: convert(r.temp_min, unit),
    mean: convert(r.temp_mean, unit),
  }));

  return (
    <div className="h-72 w-full">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="#e7e5e4" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fill: '#57534e', fontSize: 11 }}
            axisLine={{ stroke: '#d6d3d1' }}
            tickLine={{ stroke: '#d6d3d1' }}
          />
          <YAxis
            width={40}
            tick={{ fill: '#57534e', fontSize: 11 }}
            axisLine={{ stroke: '#d6d3d1' }}
            tickLine={{ stroke: '#d6d3d1' }}
            unit={unit === 'c' ? '°C' : '°F'}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              border: '1px solid #d6d3d1',
              borderRadius: 6,
              fontSize: 12,
            }}
            labelStyle={{ color: '#44403c', fontWeight: 500 }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          <Line
            type="monotone"
            dataKey="max"
            name="Max"
            stroke="#1c1917"
            strokeWidth={2}
            dot={false}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="mean"
            name="Mean"
            stroke="#78716c"
            strokeWidth={1.5}
            dot={false}
            connectNulls
          />
          <Line
            type="monotone"
            dataKey="min"
            name="Min"
            stroke="#a8a29e"
            strokeWidth={2}
            strokeDasharray="4 4"
            dot={false}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

function convert(v: number | null, unit: Unit): number | null {
  if (v === null || v === undefined || Number.isNaN(v)) return null;
  return unit === 'c' ? v : cToF(v);
}
