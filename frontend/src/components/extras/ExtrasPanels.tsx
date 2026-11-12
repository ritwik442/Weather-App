import { useQuery } from '@tanstack/react-query';
import { api } from '../../lib/api';
import { AqiPanel } from './AqiPanel';
import { MapPanel } from './MapPanel';
import { VideosPanel } from './VideosPanel';
import { WikipediaPanel } from './WikipediaPanel';

interface Props {
  lat: number;
  lon: number;
  name: string;
}

export function ExtrasPanels({ lat, lon, name }: Props) {
  const extras = useQuery({
    queryKey: ['extras', lat, lon, name],
    queryFn: ({ signal }) => api.extras(lat, lon, name, signal),
    staleTime: 10 * 60 * 1000,
    retry: false,
  });

  if (extras.isLoading) {
    return (
      <div className="rounded-xl border border-stone-200 bg-white p-4 text-sm text-stone-600">
        Loading extras…
      </div>
    );
  }

  if (!extras.data) return null;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <MapPanel piece={extras.data.map} locationName={name} />
      <AqiPanel piece={extras.data.air_quality} />
      <WikipediaPanel piece={extras.data.wikipedia} />
      <VideosPanel piece={extras.data.videos} locationName={name} />
    </div>
  );
}
