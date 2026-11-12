import {
  CircleHelp,
  Cloud,
  CloudDrizzle,
  CloudFog,
  CloudLightning,
  CloudRain,
  CloudSnow,
  CloudSun,
  Snowflake,
  Sun,
  Zap,
  type LucideIcon,
} from 'lucide-react';

export interface WeatherCodeInfo {
  label: string;
  icon: LucideIcon;
}

export function describeWeatherCode(code: number | null): WeatherCodeInfo {
  if (code === null || code === undefined) return { label: 'Unknown', icon: CircleHelp };

  // WMO weather interpretation codes.
  if (code === 0) return { label: 'Clear sky', icon: Sun };
  if (code === 1) return { label: 'Mainly clear', icon: CloudSun };
  if (code === 2) return { label: 'Partly cloudy', icon: CloudSun };
  if (code === 3) return { label: 'Overcast', icon: Cloud };
  if (code === 45 || code === 48) return { label: 'Fog', icon: CloudFog };
  if (code >= 51 && code <= 57) return { label: 'Drizzle', icon: CloudDrizzle };
  if (code >= 61 && code <= 67) return { label: 'Rain', icon: CloudRain };
  if (code >= 71 && code <= 77) return { label: 'Snow', icon: CloudSnow };
  if (code >= 80 && code <= 82) return { label: 'Rain showers', icon: CloudRain };
  if (code === 85 || code === 86) return { label: 'Snow showers', icon: Snowflake };
  if (code === 95) return { label: 'Thunderstorm', icon: CloudLightning };
  if (code === 96 || code === 99) return { label: 'Thunderstorm w/ hail', icon: Zap };

  return { label: 'Unknown', icon: CircleHelp };
}
