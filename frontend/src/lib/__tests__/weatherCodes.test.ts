import { describe, expect, it } from 'vitest';
import { describeWeatherCode } from '../weatherCodes';

describe('describeWeatherCode', () => {
  it('labels clear sky', () => {
    expect(describeWeatherCode(0).label).toBe('Clear sky');
  });

  it('labels drizzle range', () => {
    for (let code = 51; code <= 57; code++) {
      expect(describeWeatherCode(code).label).toBe('Drizzle');
    }
  });

  it('labels rain and snow ranges distinctly', () => {
    expect(describeWeatherCode(61).label).toBe('Rain');
    expect(describeWeatherCode(73).label).toBe('Snow');
    expect(describeWeatherCode(81).label).toBe('Rain showers');
    expect(describeWeatherCode(86).label).toBe('Snow showers');
  });

  it('returns Unknown for null/unknown code', () => {
    expect(describeWeatherCode(null).label).toBe('Unknown');
    expect(describeWeatherCode(999).label).toBe('Unknown');
  });

  it('returns a component icon for every case', () => {
    for (const c of [0, 2, 48, 55, 65, 75, 82, 86, 95, 99, null, 999]) {
      expect(typeof describeWeatherCode(c as number | null).icon).toBe('object');
    }
  });
});
