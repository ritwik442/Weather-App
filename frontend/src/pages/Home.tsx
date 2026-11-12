import { useQuery } from '@tanstack/react-query';
import { useEffect, useMemo, useState } from 'react';
import { CandidatePicker } from '../components/CandidatePicker';
import { CurrentWeatherCard } from '../components/CurrentWeatherCard';
import { ErrorMessage } from '../components/ErrorMessage';
import { ExtrasPanels } from '../components/extras/ExtrasPanels';
import { ForecastList } from '../components/ForecastList';
import { LoadingState, SkeletonBlock } from '../components/LoadingState';
import { SearchBar } from '../components/SearchBar';
import { TipsPanel } from '../components/TipsPanel';
import { UnitToggle } from '../components/UnitToggle';
import { useGeolocation } from '../hooks/useGeolocation';
import { useUnit } from '../hooks/useUnit';
import { api, ApiError } from '../lib/api';
import type { LocationCandidate } from '../types/api';

interface Query {
  text: string;
  index?: number;
}

export function Home() {
  const [unit, setUnit] = useUnit();
  const [query, setQuery] = useState<Query | null>(null);
  const { status: geoStatus, request: requestGeo, reset: resetGeo } = useGeolocation();

  // Promote a successful geolocation into a query the moment it arrives.
  useEffect(() => {
    if (geoStatus.kind === 'ok') {
      setQuery({ text: `${geoStatus.lat}, ${geoStatus.lon}` });
    }
  }, [geoStatus]);

  const weather = useQuery({
    queryKey: ['weather', query?.text, query?.index ?? null],
    queryFn: ({ signal }) => api.weather(query!.text, query!.index, signal),
    enabled: !!query,
    retry: (failureCount, err) => {
      if (err instanceof ApiError && err.code === 'LOCATION_AMBIGUOUS') return false;
      if (err instanceof ApiError && err.code === 'LOCATION_NOT_FOUND') return false;
      return failureCount < 1;
    },
    staleTime: 5 * 60 * 1000,
  });

  const ambiguousCandidates = useMemo<LocationCandidate[]>(() => {
    if (!(weather.error instanceof ApiError)) return [];
    if (weather.error.code !== 'LOCATION_AMBIGUOUS') return [];
    const raw = weather.error.details['candidates'];
    return Array.isArray(raw) ? (raw as LocationCandidate[]) : [];
  }, [weather.error]);

  const geoMessage = geoStatusMessage(geoStatus);

  return (
    <div className="mx-auto w-full max-w-4xl space-y-6 px-4 py-8 md:px-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-semibold text-stone-900">Weather App</h1>
          <p className="text-sm text-stone-500">
            Current conditions, 5-day outlook, and practical tips.
          </p>
        </div>
        <UnitToggle unit={unit} onChange={setUnit} />
      </header>

      <SearchBar
        onSubmit={(text) => {
          resetGeo();
          setQuery({ text });
        }}
        onUseMyLocation={requestGeo}
        geolocating={geoStatus.kind === 'loading'}
      />

      {geoMessage && (
        <p className="text-sm text-stone-600" role="status" aria-live="polite">
          {geoMessage}
        </p>
      )}

      {query && weather.isLoading && (
        <div className="space-y-6">
          <LoadingState label={`Looking up “${query.text}”…`} />
          <SkeletonBlock className="h-40" />
          <SkeletonBlock className="h-28" />
        </div>
      )}

      {weather.error && ambiguousCandidates.length > 0 && (
        <CandidatePicker
          candidates={ambiguousCandidates}
          onPick={(index) => setQuery({ text: query!.text, index })}
        />
      )}

      {weather.error && ambiguousCandidates.length === 0 && (
        <ErrorMessage error={weather.error} onRetry={() => weather.refetch()} />
      )}

      {weather.data && (
        <>
          <CurrentWeatherCard
            location={weather.data.location}
            current={weather.data.current}
            unit={unit}
          />
          <TipsPanel tips={weather.data.tips} />
          <ForecastList days={weather.data.daily} unit={unit} />
          <ExtrasPanels
            lat={weather.data.location.lat}
            lon={weather.data.location.lon}
            name={weather.data.location.display_name.split(',')[0]?.trim() || weather.data.location.display_name}
          />
        </>
      )}

      {!query && !geoMessage && (
        <p className="text-sm text-stone-500">
          Start by searching for a place or using your current location.
        </p>
      )}
    </div>
  );
}

function geoStatusMessage(s: ReturnType<typeof useGeolocation>['status']): string | null {
  switch (s.kind) {
    case 'denied':
      return 'Location permission denied. Try searching by name instead.';
    case 'unsupported':
      return "Your browser doesn't support geolocation. Search by name or coordinates.";
    case 'timeout':
      return "Couldn't get your location in time. Try again, or search by name.";
    case 'error':
      return `Location error: ${s.message}`;
    default:
      return null;
  }
}
