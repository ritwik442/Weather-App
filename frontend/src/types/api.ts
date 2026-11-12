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
