/**
 * Flight search service.
 * In a real app this would call an external flights API.
 * Here we use a deterministic mock that returns plausible results
 * based on the search parameters, and simulates async latency.
 */

const AIRLINES = [
  { code: 'AA', name: 'American Airlines' },
  { code: 'DL', name: 'Delta Air Lines' },
  { code: 'UA', name: 'United Airlines' },
  { code: 'WN', name: 'Southwest Airlines' },
  { code: 'B6', name: 'JetBlue Airways' },
  { code: 'AS', name: 'Alaska Airlines' },
  { code: 'NK', name: 'Spirit Airlines' },
  { code: 'F9', name: 'Frontier Airlines' },
];

const STOPS_OPTIONS = [
  { label: 'Nonstop', value: 0 },
  { label: '1 stop', value: 1 },
  { label: '2 stops', value: 2 },
];

function seededRandom(seed) {
  let s = seed;
  return function () {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

function formatTime(totalMinutes) {
  const h = Math.floor(totalMinutes / 60) % 24;
  const m = totalMinutes % 60;
  const period = h < 12 ? 'AM' : 'PM';
  const displayH = h === 0 ? 12 : h > 12 ? h - 12 : h;
  return `${displayH}:${String(m).padStart(2, '0')} ${period}`;
}

function minutesToDuration(minutes) {
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m > 0 ? `${h}h ${m}m` : `${h}h`;
}

function seedFromString(str) {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = (Math.imul(31, hash) + str.charCodeAt(i)) | 0;
  }
  return Math.abs(hash);
}

function generateFlights({ origin, destination, date, passengers, isReturn = false }) {
  const seed = seedFromString(`${origin}${destination}${date}${isReturn}`);
  const rand = seededRandom(seed);

  const count = 3 + Math.floor(rand() * 5); // 3–7 results
  const flights = [];

  for (let i = 0; i < count; i++) {
    const airline = AIRLINES[Math.floor(rand() * AIRLINES.length)];
    const stops = STOPS_OPTIONS[Math.floor(rand() * STOPS_OPTIONS.length)];

    const durationMinutes = 90 + Math.floor(rand() * 480) + stops.value * 60; // 90m–9h
    const departureMinutes = 300 + Math.floor(rand() * 900); // 5 AM – 8 PM spread
    const arrivalMinutes = departureMinutes + durationMinutes;

    const basePrice = 80 + Math.floor(rand() * 700);
    const pricePerPassenger = basePrice;
    const totalPrice = pricePerPassenger * passengers;

    flights.push({
      id: `${airline.code}-${i}-${seed}`,
      airline: airline.name,
      airlineCode: airline.code,
      origin,
      destination,
      date,
      departureTime: formatTime(departureMinutes),
      arrivalTime: formatTime(arrivalMinutes),
      durationMinutes,
      duration: minutesToDuration(durationMinutes),
      stops: stops.value,
      stopsLabel: stops.label,
      pricePerPassenger,
      totalPrice,
      passengers,
    });
  }

  // Sort by departure time (price is secondary sort for ties)
  return flights.sort((a, b) => a.pricePerPassenger - b.pricePerPassenger);
}

/**
 * Search for available flights.
 * @param {Object} params
 * @param {string} params.origin       - IATA airport code or city name
 * @param {string} params.destination  - IATA airport code or city name
 * @param {string} params.departureDate - ISO date string (YYYY-MM-DD)
 * @param {string} [params.returnDate]  - ISO date string (YYYY-MM-DD), optional
 * @param {number} params.passengers   - Number of passengers
 * @returns {Promise<{ outbound: Flight[], inbound: Flight[] | null }>}
 */
export async function searchFlights({ origin, destination, departureDate, returnDate, passengers }) {
  // Simulate network latency (800ms – 1.5s)
  await new Promise((resolve) => setTimeout(resolve, 800 + Math.random() * 700));

  // Simulate occasional API errors (5% chance) for error-state testing
  if (Math.random() < 0.05) {
    throw new Error('Unable to reach the flights service. Please try again.');
  }

  const outbound = generateFlights({ origin, destination, date: departureDate, passengers });

  const inbound = returnDate
    ? generateFlights({ origin: destination, destination: origin, date: returnDate, passengers, isReturn: true })
    : null;

  return { outbound, inbound };
}
