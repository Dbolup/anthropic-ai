import './FlightCard.css';

export default function FlightCard({ flight }) {
  const {
    airline,
    airlineCode,
    origin,
    destination,
    departureTime,
    arrivalTime,
    duration,
    stopsLabel,
    pricePerPassenger,
    totalPrice,
    passengers,
  } = flight;

  return (
    <article className="flight-card" aria-label={`${airline} flight from ${origin} to ${destination}`}>
      {/* Airline */}
      <div className="flight-airline">
        <span className="airline-code" aria-hidden="true">
          {airlineCode}
        </span>
        <span className="airline-name">{airline}</span>
      </div>

      {/* Route / Times */}
      <div className="flight-route">
        <div className="flight-endpoint">
          <span className="endpoint-time">{departureTime}</span>
          <span className="endpoint-iata">{origin.toUpperCase()}</span>
        </div>

        <div className="flight-middle">
          <span className="flight-duration">{duration}</span>
          <div className="flight-line" aria-hidden="true">
            <span className="line" />
            {flight.stops > 0 && (
              <span className="stop-dot" title={`${flight.stops} stop(s)`} />
            )}
            <span className="plane-icon" aria-hidden="true">✈</span>
          </div>
          <span className="flight-stops">{stopsLabel}</span>
        </div>

        <div className="flight-endpoint">
          <span className="endpoint-time">{arrivalTime}</span>
          <span className="endpoint-iata">{destination.toUpperCase()}</span>
        </div>
      </div>

      {/* Price */}
      <div className="flight-price">
        <span className="price-total" aria-label={`Total price $${totalPrice}`}>
          ${totalPrice.toLocaleString()}
        </span>
        {passengers > 1 && (
          <span className="price-per-person">
            ${pricePerPassenger.toLocaleString()} / person
          </span>
        )}
        <button className="select-btn" aria-label={`Select ${airline} flight for $${totalPrice}`}>
          Select
        </button>
      </div>
    </article>
  );
}
