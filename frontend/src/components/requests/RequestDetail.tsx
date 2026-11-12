import { useQuery } from '@tanstack/react-query';
import { ChevronLeft } from 'lucide-react';
import { ErrorMessage } from '../ErrorMessage';
import { LoadingState } from '../LoadingState';
import { api } from '../../lib/api';
import { formatTemperature, type Unit } from '../../lib/units';
import { ExportMenu } from './ExportMenu';
import { TemperatureChart } from './TemperatureChart';

interface Props {
  id: number;
  unit: Unit;
  onBack: () => void;
  onEdit: () => void;
  onDelete: () => void;
}

export function RequestDetail({ id, unit, onBack, onEdit, onDelete }: Props) {
  const query = useQuery({
    queryKey: ['request', id],
    queryFn: ({ signal }) => api.getRequest(id, signal),
    staleTime: 60_000,
  });

  if (query.isLoading) return <LoadingState label="Loading request…" />;
  if (query.error) return <ErrorMessage error={query.error} onRetry={() => query.refetch()} />;
  if (!query.data) return null;

  const r = query.data;

  return (
    <section className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-y-2 gap-x-3">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-1 text-sm text-stone-700 hover:text-stone-950 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-500"
        >
          <ChevronLeft aria-hidden className="h-4 w-4" />
          Back to list
        </button>
        <div className="flex flex-wrap items-center gap-2">
          <ExportMenu ids={[r.id]} label="Export this" />
          <button
            type="button"
            onClick={onEdit}
            className="rounded-full border border-stone-300 bg-white px-3 py-1.5 text-sm font-medium text-stone-800 hover:bg-stone-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-500"
          >
            Edit
          </button>
          <button
            type="button"
            onClick={onDelete}
            className="rounded-full border border-red-700 bg-white px-3 py-1.5 text-sm font-medium text-red-700 hover:bg-red-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-500"
          >
            Delete
          </button>
        </div>
      </div>

      <div className="rounded-xl border border-stone-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-stone-900">
          {r.location.display_name}
        </h2>
        <p className="mt-1 text-sm text-stone-600">
          {r.start_date} → {r.end_date} · {r.daily.length} day{r.daily.length === 1 ? '' : 's'}
        </p>
        {r.notes && <p className="mt-2 text-sm text-stone-700">{r.notes}</p>}
      </div>

      <div className="rounded-xl border border-stone-200 bg-white p-5">
        <h3 className="text-sm font-medium uppercase tracking-wide text-stone-500">
          Temperatures
        </h3>
        <div className="mt-3">
          <TemperatureChart rows={r.daily} unit={unit} />
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-stone-200 bg-white">
        <table className="w-full border-collapse text-sm">
          <thead className="bg-stone-50 text-xs uppercase tracking-wide text-stone-500">
            <tr>
              <th scope="col" className="px-4 py-2 text-left">Date</th>
              <th scope="col" className="px-4 py-2 text-right">Min</th>
              <th scope="col" className="px-4 py-2 text-right">Mean</th>
              <th scope="col" className="px-4 py-2 text-right">Max</th>
              <th scope="col" className="px-4 py-2 text-right">Precip</th>
            </tr>
          </thead>
          <tbody>
            {r.daily.map((row) => (
              <tr key={row.date} className="border-t border-stone-100 text-stone-800">
                <td className="px-4 py-2">{row.date}</td>
                <td className="px-4 py-2 text-right tabular-nums">
                  {formatTemperature(row.temp_min, unit)}
                </td>
                <td className="px-4 py-2 text-right tabular-nums">
                  {formatTemperature(row.temp_mean, unit)}
                </td>
                <td className="px-4 py-2 text-right tabular-nums">
                  {formatTemperature(row.temp_max, unit)}
                </td>
                <td className="px-4 py-2 text-right tabular-nums">
                  {row.precipitation_sum === null ? '—' : `${row.precipitation_sum.toFixed(1)} mm`}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
