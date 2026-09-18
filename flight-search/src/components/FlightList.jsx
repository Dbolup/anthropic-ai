import FlightCard from './FlightCard';
import './FlightList.css';

export default function FlightList({ results, searchParams }) {
  const { outbound, inbound } = results;
  const { origin, destination, departureDate, returnDate, passengers, tripType } = searchParams;

  const passengerLabel = `${passengers} ${passengers === 1 ? 'passenger' : 'passengers'}`;

  return (
    <section className="flight-list-section" aria-label="Flight search results">
      {/* Outbound flights */}
      <div className="flight-group">
        <h2 className="group-heading">
          {origin.toUpperCase()} → {destination.toUpperCase()}
          <span className="group-meta">
            {departureDate} · {passengerLabel}
          </span>
        </h2>

        {outbound.length === 0 ? (
          <EmptyState origin={origin} destination={destination} date={departureDate} />
        ) : (
          <ul className="flight-list" role="list">
            {outbound.map((flight) => (
              <li key={flight.id}>
                <FlightCard flight={flight} />
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Inbound / return flights */}
      {tripType === 'roundtrip' && inbound && (
        <div className="flight-group">
          <h2 className="group-heading">
            {destination.toUpperCase()} → {origin.toUpperCase()}
            <span className="group-meta">
              {returnDate} · {passengerLabel}
            </span>
          </h2>

          {inbound.length === 0 ? (
            <EmptyState origin={destination} destination={origin} date={returnDate} />
          ) : (
            <ul className="flight-list" role="list">
              {inbound.map((flight) => (
                <li key={flight.id}>
                  <FlightCard flight={flight} />
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}

function EmptyState({ origin, destination, date }) {
  return (
    <div className="empty-state" role="status" aria-live="polite">
      <span className="empty-icon" aria-hidden="true">✈️</span>
      <p className="empty-title">No flights found</p>
      <p className="empty-sub">
        We couldn't find any available flights from{' '}
        <strong>{origin.toUpperCase()}</strong> to{' '}
        <strong>{destination.toUpperCase()}</strong> on {date}. Try adjusting
        your search.
      </p>
    </div>
  );
}
