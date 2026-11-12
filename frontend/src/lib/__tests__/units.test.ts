import { describe, expect, it } from 'vitest';
import { cToF, formatMm, formatPercent, formatPressure, formatTemperature, formatWindKmh } from '../units';

describe('cToF', () => {
  it('converts 0°C to 32°F', () => {
    expect(cToF(0)).toBe(32);
  });

  it('converts 100°C to 212°F', () => {
    expect(cToF(100)).toBe(212);
  });

  it('is linear for negative values', () => {
    expect(cToF(-40)).toBe(-40);
  });
});

describe('formatTemperature', () => {
  it('shows em dash for null', () => {
    expect(formatTemperature(null, 'c')).toBe('—');
  });

  it('rounds to integer by default', () => {
    expect(formatTemperature(22.4, 'c')).toBe('22°C');
  });

  it('converts to Fahrenheit when requested', () => {
    expect(formatTemperature(0, 'f')).toBe('32°F');
  });

  it('respects digits argument', () => {
    expect(formatTemperature(22.456, 'c', 1)).toBe('22.5°C');
  });
});

describe('format helpers', () => {
  it('formatPercent rounds and adds %', () => {
    expect(formatPercent(42.6)).toBe('43%');
    expect(formatPercent(null)).toBe('—');
  });

  it('formatMm shows one decimal', () => {
    expect(formatMm(2.456)).toBe('2.5 mm');
  });

  it('formatPressure rounds to hPa', () => {
    expect(formatPressure(1013.7)).toBe('1014 hPa');
  });

  it('formatWindKmh converts m/s to km/h', () => {
    expect(formatWindKmh(10)).toBe('36 km/h');
    expect(formatWindKmh(null)).toBe('—');
  });
});
