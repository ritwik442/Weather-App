export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
  };
}

export interface LocationCandidate {
  display_name: string;
  lat: number;
  lon: number;
  country: string | null;
  region: string | null;
  timezone: string | null;
  source: string;
}

export interface CurrentWeather {
  temperature: number | null;
  feels_like: number | null;
  humidity: number | null;
  wind_speed: number | null;
  wind_direction: number | null;
  precipitation: number | null;
  precipitation_probability: number | null;
  uv_index: number | null;
  visibility: number | null;
  pressure: number | null;
  weather_code: number | null;
  is_day: boolean | null;
  time: string | null;
  timezone: string | null;
  sunrise: string | null;
  sunset: string | null;
  temp_max_today: number | null;
  temp_min_today: number | null;
}

export interface ForecastDay {
  date: string;
  temp_min: number | null;
  temp_max: number | null;
  precipitation_sum: number | null;
  precipitation_probability_max: number | null;
  weather_code: number | null;
  uv_index_max: number | null;
}

export interface Tip {
  code: string;
  message: string;
  severity: 'info' | 'warning';
}

export interface WeatherBundle {
  location: LocationCandidate;
  current: CurrentWeather;
  daily: ForecastDay[];
  tips: Tip[];
}

export interface LocationResolveResponse {
  query: string;
  candidates: LocationCandidate[];
}

export interface StoredLocation {
  id: number;
  query_text: string;
  display_name: string;
  lat: number;
  lon: number;
  country: string | null;
  region: string | null;
  timezone: string | null;
  source: string;
  created_at: string;
}

export interface DailyTemperature {
  date: string;
  temp_min: number | null;
  temp_max: number | null;
  temp_mean: number | null;
  precipitation_sum: number | null;
  weather_code: number | null;
}

export interface SavedRequest {
  id: number;
  location: StoredLocation;
  start_date: string;
  end_date: string;
  notes: string | null;
  created_at: string;
  updated_at: string;
  daily: DailyTemperature[];
}

export type SavedRequestListItem = Omit<SavedRequest, 'daily'>;

export interface SavedRequestListResponse {
  total: number;
  items: SavedRequestListItem[];
}

export interface CreateRequestPayload {
  location: string;
  start_date: string;
  end_date: string;
  notes?: string | null;
  location_index?: number | null;
}

export interface UpdateRequestPayload {
  location?: string | null;
  start_date?: string | null;
  end_date?: string | null;
  notes?: string | null;
  location_index?: number | null;
}

export interface ExtraPiece<T> {
  value: T | null;
  error: string | null;
}

export interface YoutubeExtraValue {
  videos: Array<{
    id: string;
    title: string | null;
    channel: string | null;
    published_at: string | null;
    thumbnail: string | null;
    url: string;
  }>;
  search_url: string;
  has_key: boolean;
}

export interface WikipediaExtraValue {
  title: string | null;
  extract: string | null;
  url: string | null;
  thumbnail: string | null;
}

export interface AirQualityExtraValue {
  time: string | null;
  european_aqi: number | null;
  us_aqi: number | null;
  pm10: number | null;
  pm2_5: number | null;
  ozone: number | null;
}

export interface MapExtraValue {
  lat: number;
  lon: number;
  google_maps_url: string;
  osm_tile_url_template: string;
}

export interface LocationExtras {
  videos: ExtraPiece<YoutubeExtraValue>;
  wikipedia: ExtraPiece<WikipediaExtraValue>;
  air_quality: ExtraPiece<AirQualityExtraValue>;
  map: ExtraPiece<MapExtraValue>;
}
