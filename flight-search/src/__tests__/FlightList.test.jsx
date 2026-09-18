import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import FlightList from '../components/FlightList';

vi.mock('../components/FlightList.css', () => ({}));
vi.mock('../components/FlightCard.css', () => ({}));

const makeFlight = (id, pricePerPassenger, passengers = 2) => ({
  id,
  airline: 'Delta Air Lines',
  airlineCode: 'DL',
  origin: 'JFK',
  destination: 'LAX',
  date: '2026-12-01',
  departureTime: '9:00 AM',
  arrivalTime: '12:30 PM',
  durationMinutes: 330,
  duration: '5h 30m',
  stops: 0,
  stopsLabel: 'Nonstop',
  pricePerPassenger,
  totalPrice: pricePerPassenger * passengers,
  passengers,
});

const baseParams = {
  origin: 'JFK',
  destination: 'LAX',
  departureDate: '2026-12-01',
  returnDate: '',
  passengers: 2,
  tripType: 'oneway',
};

describe('FlightList', () => {
  it('renders outbound flight cards', () => {
    const results = { outbound: [makeFlight('f1', 300), makeFlight('f2', 400)], inbound: null };
    render(<FlightList results={results} searchParams={baseParams} />);
    expect(screen.getAllByRole('article').length).toBe(2);
  });

  it('shows empty state when no outbound flights', () => {
    const results = { outbound: [], inbound: null };
    render(<FlightList results={results} searchParams={baseParams} />);
    expect(screen.getByText(/no flights found/i)).toBeInTheDocument();
  });

  it('renders inbound section for round-trip with return date', () => {
    const params = { ...baseParams, tripType: 'roundtrip', returnDate: '2026-12-08' };
    const results = {
      outbound: [makeFlight('f1', 300)],
      inbound: [makeFlight('f2', 350)],
    };
    render(<FlightList results={results} searchParams={params} />);
    expect(screen.getByText(/LAX.*JFK/)).toBeInTheDocument();
  });

  it('does not render inbound section for one-way trips', () => {
    const results = { outbound: [makeFlight('f1', 300)], inbound: null };
    render(<FlightList results={results} searchParams={baseParams} />);
    expect(screen.queryByText(/LAX.*JFK/)).not.toBeInTheDocument();
  });
});
