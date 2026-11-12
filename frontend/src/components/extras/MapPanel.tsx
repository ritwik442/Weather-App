import { ExternalLink, MapPin } from 'lucide-react';
import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet';
import { Icon } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { ExtraPiece, MapExtraValue } from '../../types/api';

// Leaflet's default icon relies on asset bundling that Vite doesn't do out of
// the box. Pointing to the CDN keeps the pin visible without build hacks.
const defaultIcon = new Icon({
  iconUrl: 'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl:
    'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl:
    'https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

interface Props {
  piece: ExtraPiece<MapExtraValue>;
  locationName: string;
}

export function MapPanel({ piece, locationName }: Props) {
  if (!piece.value) return null;
  const { lat, lon, google_maps_url } = piece.value;
  return (
    <section
      aria-label="Map"
      className="overflow-hidden rounded-xl border border-stone-200 bg-white"
    >
      <header className="flex items-center justify-between border-b border-stone-200 px-4 py-3">
        <h3 className="flex items-center gap-2 text-sm font-medium uppercase tracking-wide text-stone-500">
          <MapPin aria-hidden className="h-4 w-4" />
          Map
        </h3>
        <a
          href={google_maps_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1 text-xs font-medium text-stone-700 hover:text-stone-950"
        >
          Open in Google Maps
          <ExternalLink aria-hidden className="h-3 w-3" />
        </a>
      </header>
      <div className="h-72 w-full">
        <MapContainer
          center={[lat, lon]}
          zoom={11}
          scrollWheelZoom={false}
          className="h-full w-full"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url={piece.value.osm_tile_url_template}
          />
          <Marker position={[lat, lon]} icon={defaultIcon}>
            <Popup>{locationName}</Popup>
          </Marker>
        </MapContainer>
      </div>
    </section>
  );
}
