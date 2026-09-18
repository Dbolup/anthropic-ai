/**
 * Validation helpers for the flight search form.
 */

export function validateSearchForm({ origin, destination, departureDate, returnDate, passengers }) {
  const errors = {};

  if (!origin || origin.trim().length < 2) {
    errors.origin = 'Please enter a valid origin (city or airport code).';
  }

  if (!destination || destination.trim().length < 2) {
    errors.destination = 'Please enter a valid destination (city or airport code).';
  }

  if (origin && destination && origin.trim().toLowerCase() === destination.trim().toLowerCase()) {
    errors.destination = 'Origin and destination must be different.';
  }

  if (!departureDate) {
    errors.departureDate = 'Please select a departure date.';
  } else {
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const dep = new Date(departureDate);
    if (dep < today) {
      errors.departureDate = 'Departure date cannot be in the past.';
    }
  }

  if (returnDate) {
    const dep = new Date(departureDate);
    const ret = new Date(returnDate);
    if (ret <= dep) {
      errors.returnDate = 'Return date must be after the departure date.';
    }
  }

  if (!passengers || passengers < 1 || passengers > 9) {
    errors.passengers = 'Passenger count must be between 1 and 9.';
  }

  return errors;
}

export function todayISO() {
  return new Date().toISOString().split('T')[0];
}
