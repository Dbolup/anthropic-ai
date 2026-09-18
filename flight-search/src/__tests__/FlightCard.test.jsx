import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import FlightCard from '../components/FlightCard';

vi.mock('../components/FlightCard.css', () => ({}));

const mockFlight = {
  id: 'AA-1-12345',
  airline: 'American Airlines',
  airlineCode: 'AA',
  origin: 'JFK',
  destination: 'LAX',
  date: '2026-12-01',
  departureTime: '8:00 AM',
  arrivalTime: '11:30 AM',
  durationMinutes: 330,
  duration: '5h 30m',
  stops: 0,
  stopsLabel: 'Nonstop',
  pricePerPassenger: 250,
  totalPrice: 500,
  passengers: 2,
};

describe('FlightCard', () => {
  it('displays airline name', () => {
    render(<FlightCard flight={mockFlight} />);
    expect(screen.getByText('American Airlines')).toBeInTheDocument();
  });

  it('displays departure and arrival times', () => {
    render(<FlightCard flight={mockFlight} />);
    expect(screen.getByText('8:00 AM')).toBeInTheDocument();
    expect(screen.getByText('11:30 AM')).toBeInTheDocument();
  });

  it('displays flight duration', () => {
    render(<FlightCard flight={mockFlight} />);
    expect(screen.getByText('5h 30m')).toBeInTheDocument();
  });

  it('displays stops information', () => {
    render(<FlightCard flight={mockFlight} />);
    expect(screen.getByText('Nonstop')).toBeInTheDocument();
  });

  it('displays total price', () => {
    render(<FlightCard flight={mockFlight} />);
    expect(screen.getByText('$500')).toBeInTheDocument();
  });

  it('shows per-person price when passengers > 1', () => {
    render(<FlightCard flight={mockFlight} />);
    expect(screen.getByText(/\$250.*person/i)).toBeInTheDocument();
  });

  it('does not show per-person price for single passenger', () => {
    const singleFlight = { ...mockFlight, passengers: 1, totalPrice: 250 };
    render(<FlightCard flight={singleFlight} />);
    expect(screen.queryByText(/person/i)).not.toBeInTheDocument();
  });

  it('displays origin and destination IATA codes', () => {
    render(<FlightCard flight={mockFlight} />);
    expect(screen.getByText('JFK')).toBeInTheDocument();
    expect(screen.getByText('LAX')).toBeInTheDocument();
  });

  it('has a Select button', () => {
    render(<FlightCard flight={mockFlight} />);
    expect(screen.getByRole('button', { name: /select/i })).toBeInTheDocument();
  });
});
