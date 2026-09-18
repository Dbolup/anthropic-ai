import { describe, it, expect } from 'vitest';
import { validateSearchForm, todayISO } from '../utils/validation';

const today = todayISO();
const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
const dayAfterTomorrow = new Date(Date.now() + 2 * 86400000).toISOString().split('T')[0];
const yesterday = new Date(Date.now() - 86400000).toISOString().split('T')[0];

describe('validateSearchForm', () => {
  const validForm = {
    origin: 'JFK',
    destination: 'LAX',
    departureDate: tomorrow,
    returnDate: '',
    passengers: 1,
  };

  it('returns no errors for a valid one-way form', () => {
    expect(validateSearchForm(validForm)).toEqual({});
  });

  it('returns no errors for valid round-trip form', () => {
    const form = { ...validForm, returnDate: dayAfterTomorrow };
    expect(validateSearchForm(form)).toEqual({});
  });

  it('requires origin', () => {
    const errors = validateSearchForm({ ...validForm, origin: '' });
    expect(errors.origin).toBeDefined();
  });

  it('requires origin of at least 2 chars', () => {
    const errors = validateSearchForm({ ...validForm, origin: 'J' });
    expect(errors.origin).toBeDefined();
  });

  it('requires destination', () => {
    const errors = validateSearchForm({ ...validForm, destination: '' });
    expect(errors.destination).toBeDefined();
  });

  it('rejects same origin and destination', () => {
    const errors = validateSearchForm({ ...validForm, destination: 'JFK' });
    expect(errors.destination).toMatch(/different/i);
  });

  it('requires departureDate', () => {
    const errors = validateSearchForm({ ...validForm, departureDate: '' });
    expect(errors.departureDate).toBeDefined();
  });

  it('rejects past departure date', () => {
    const errors = validateSearchForm({ ...validForm, departureDate: yesterday });
    expect(errors.departureDate).toMatch(/past/i);
  });

  it('rejects return date on same day as departure', () => {
    const errors = validateSearchForm({ ...validForm, returnDate: tomorrow });
    expect(errors.returnDate).toMatch(/after/i);
  });

  it('rejects return date before departure', () => {
    const errors = validateSearchForm({ ...validForm, departureDate: dayAfterTomorrow, returnDate: tomorrow });
    expect(errors.returnDate).toMatch(/after/i);
  });

  it('requires at least 1 passenger', () => {
    const errors = validateSearchForm({ ...validForm, passengers: 0 });
    expect(errors.passengers).toBeDefined();
  });

  it('rejects more than 9 passengers', () => {
    const errors = validateSearchForm({ ...validForm, passengers: 10 });
    expect(errors.passengers).toBeDefined();
  });

  it('allows up to 9 passengers', () => {
    expect(validateSearchForm({ ...validForm, passengers: 9 })).toEqual({});
  });
});

describe('todayISO', () => {
  it('returns a valid ISO date string', () => {
    expect(todayISO()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
