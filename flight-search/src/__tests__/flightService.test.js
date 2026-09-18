import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { searchFlights } from '../services/flightService';

describe('searchFlights', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  /**
   * Mock Math.random so that:
   *  - first call (setTimeout latency) returns 0.5  → 800 + 350 = 1150ms delay
   *  - second call (5% error gate) returns 0.5      → 0.5 >= 0.05 → no error
   */
  function mockRandomForSuccess() {
    vi.spyOn(Math, 'random').mockReturnValue(0.5);
  }

  /**
   * Mock Math.random so that:
   *  - first call (latency)   returns 0.5  → 1150ms delay
   *  - second call (error gate) returns 0  → 0 < 0.05 → error fires
   */
  function mockRandomForError() {
    vi.spyOn(Math, 'random')
      .mockReturnValueOnce(0.5)
      .mockReturnValue(0);
  }

  it('resolves with outbound flights and null inbound for one-way', async () => {
    mockRandomForSuccess();

    const promise = searchFlights({
      origin: 'JFK',
      destination: 'LAX',
      departureDate: '2026-12-01',
      returnDate: null,
      passengers: 2,
    });

    await vi.runAllTimersAsync();
    const result = await promise;

    expect(result).toHaveProperty('outbound');
    expect(result).toHaveProperty('inbound', null);
    expect(Array.isArray(result.outbound)).toBe(true);
    expect(result.outbound.length).toBeGreaterThan(0);
  });

  it('resolves with both outbound and inbound flights for round-trip', async () => {
    mockRandomForSuccess();

    const promise = searchFlights({
      origin: 'JFK',
      destination: 'LAX',
      departureDate: '2026-12-01',
      returnDate: '2026-12-08',
      passengers: 1,
    });

    await vi.runAllTimersAsync();
    const result = await promise;

    expect(Array.isArray(result.outbound)).toBe(true);
    expect(Array.isArray(result.inbound)).toBe(true);
    expect(result.outbound.length).toBeGreaterThan(0);
    expect(result.inbound.length).toBeGreaterThan(0);
  });

  it('flight objects have required fields', async () => {
    mockRandomForSuccess();

    const promise = searchFlights({
      origin: 'ORD',
      destination: 'MIA',
      departureDate: '2026-11-15',
      returnDate: null,
      passengers: 3,
    });

    await vi.runAllTimersAsync();
    const result = await promise;
    const flight = result.outbound[0];

    expect(flight).toHaveProperty('id');
    expect(flight).toHaveProperty('airline');
    expect(flight).toHaveProperty('airlineCode');
    expect(flight).toHaveProperty('departureTime');
    expect(flight).toHaveProperty('arrivalTime');
    expect(flight).toHaveProperty('duration');
    expect(flight).toHaveProperty('stops');
    expect(flight).toHaveProperty('stopsLabel');
    expect(flight).toHaveProperty('pricePerPassenger');
    expect(flight).toHaveProperty('totalPrice');
    expect(flight.totalPrice).toBe(flight.pricePerPassenger * 3);
  });

  it('throws an error when the simulated API error fires', async () => {
    mockRandomForError();

    // Attach the rejection handler before advancing timers to avoid
    // the unhandled-rejection warning that fires between the timer
    // advance and the subsequent `await expect(...).rejects` call.
    const rejection = expect(
      searchFlights({
        origin: 'SFO',
        destination: 'BOS',
        departureDate: '2026-10-10',
        returnDate: null,
        passengers: 1,
      }),
    ).rejects.toThrow(/unable to reach/i);

    await vi.runAllTimersAsync();
    await rejection;
  });

  it('outbound results are sorted by price ascending', async () => {
    mockRandomForSuccess();

    const promise = searchFlights({
      origin: 'DEN',
      destination: 'SEA',
      departureDate: '2027-01-20',
      returnDate: null,
      passengers: 1,
    });

    await vi.runAllTimersAsync();
    const { outbound } = await promise;

    for (let i = 1; i < outbound.length; i++) {
      expect(outbound[i].pricePerPassenger).toBeGreaterThanOrEqual(
        outbound[i - 1].pricePerPassenger,
      );
    }
  });
});
