import { useState } from 'react';
import { validateSearchForm, todayISO } from '../utils/validation';
import './SearchForm.css';

const today = todayISO();

export default function SearchForm({ onSearch, loading }) {
  const [form, setForm] = useState({
    origin: '',
    destination: '',
    departureDate: '',
    returnDate: '',
    passengers: 1,
    tripType: 'roundtrip',
  });
  const [errors, setErrors] = useState({});

  function handleChange(e) {
    const { name, value, type } = e.target;
    setForm((prev) => {
      const next = { ...prev, [name]: type === 'number' ? Number(value) : value };
      if (name === 'tripType' && value === 'oneway') next.returnDate = '';
      return next;
    });
    // Clear the error for the field being edited
    if (errors[name]) setErrors((prev) => ({ ...prev, [name]: undefined }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    const validationErrors = validateSearchForm(form);
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors);
      return;
    }
    setErrors({});
    onSearch(form);
  }

  return (
    <form
      className="search-form"
      onSubmit={handleSubmit}
      aria-label="Flight search"
      noValidate
    >
      {/* Trip type toggle */}
      <fieldset className="trip-type-fieldset">
        <legend className="sr-only">Trip type</legend>
        <label className={`trip-type-label${form.tripType === 'roundtrip' ? ' active' : ''}`}>
          <input
            type="radio"
            name="tripType"
            value="roundtrip"
            checked={form.tripType === 'roundtrip'}
            onChange={handleChange}
          />
          Round-trip
        </label>
        <label className={`trip-type-label${form.tripType === 'oneway' ? ' active' : ''}`}>
          <input
            type="radio"
            name="tripType"
            value="oneway"
            checked={form.tripType === 'oneway'}
            onChange={handleChange}
          />
          One-way
        </label>
      </fieldset>

      <div className="form-grid">
        {/* Origin */}
        <div className="form-group">
          <label htmlFor="origin">From</label>
          <input
            id="origin"
            name="origin"
            type="text"
            placeholder="City or airport (e.g. JFK)"
            value={form.origin}
            onChange={handleChange}
            autoComplete="off"
            aria-describedby={errors.origin ? 'origin-error' : undefined}
            aria-invalid={!!errors.origin}
          />
          {errors.origin && (
            <span id="origin-error" className="field-error" role="alert">
              {errors.origin}
            </span>
          )}
        </div>

        {/* Destination */}
        <div className="form-group">
          <label htmlFor="destination">To</label>
          <input
            id="destination"
            name="destination"
            type="text"
            placeholder="City or airport (e.g. LAX)"
            value={form.destination}
            onChange={handleChange}
            autoComplete="off"
            aria-describedby={errors.destination ? 'destination-error' : undefined}
            aria-invalid={!!errors.destination}
          />
          {errors.destination && (
            <span id="destination-error" className="field-error" role="alert">
              {errors.destination}
            </span>
          )}
        </div>

        {/* Departure date */}
        <div className="form-group">
          <label htmlFor="departureDate">Departure</label>
          <input
            id="departureDate"
            name="departureDate"
            type="date"
            min={today}
            value={form.departureDate}
            onChange={handleChange}
            aria-describedby={errors.departureDate ? 'departureDate-error' : undefined}
            aria-invalid={!!errors.departureDate}
          />
          {errors.departureDate && (
            <span id="departureDate-error" className="field-error" role="alert">
              {errors.departureDate}
            </span>
          )}
        </div>

        {/* Return date (only for round-trip) */}
        {form.tripType === 'roundtrip' && (
          <div className="form-group">
            <label htmlFor="returnDate">
              Return <span className="optional">(optional)</span>
            </label>
            <input
              id="returnDate"
              name="returnDate"
              type="date"
              min={form.departureDate || today}
              value={form.returnDate}
              onChange={handleChange}
              aria-describedby={errors.returnDate ? 'returnDate-error' : undefined}
              aria-invalid={!!errors.returnDate}
            />
            {errors.returnDate && (
              <span id="returnDate-error" className="field-error" role="alert">
                {errors.returnDate}
              </span>
            )}
          </div>
        )}

        {/* Passengers */}
        <div className="form-group passengers-group">
          <label htmlFor="passengers">Passengers</label>
          <input
            id="passengers"
            name="passengers"
            type="number"
            min={1}
            max={9}
            value={form.passengers}
            onChange={handleChange}
            aria-describedby={errors.passengers ? 'passengers-error' : undefined}
            aria-invalid={!!errors.passengers}
          />
          {errors.passengers && (
            <span id="passengers-error" className="field-error" role="alert">
              {errors.passengers}
            </span>
          )}
        </div>
      </div>

      <button type="submit" className="search-btn" disabled={loading}>
        {loading ? (
          <>
            <span className="spinner" aria-hidden="true" /> Searching…
          </>
        ) : (
          '🔍 Search Flights'
        )}
      </button>
    </form>
  );
}
