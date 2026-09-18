import { useState } from 'react';
import SearchForm from './components/SearchForm';
import FlightList from './components/FlightList';
import LoadingState from './components/LoadingState';
import ErrorState from './components/ErrorState';
import { searchFlights } from './services/flightService';
import './App.css';

const STATUS = {
  IDLE: 'idle',
  LOADING: 'loading',
  SUCCESS: 'success',
  ERROR: 'error',
};

export default function App() {
  const [status, setStatus] = useState(STATUS.IDLE);
  const [results, setResults] = useState(null);
  const [searchParams, setSearchParams] = useState(null);
  const [errorMessage, setErrorMessage] = useState('');

  async function handleSearch(formValues) {
    setStatus(STATUS.LOADING);
    setSearchParams(formValues);
    setResults(null);
    setErrorMessage('');

    try {
      const data = await searchFlights({
        origin: formValues.origin.trim().toUpperCase(),
        destination: formValues.destination.trim().toUpperCase(),
        departureDate: formValues.departureDate,
        returnDate: formValues.tripType === 'roundtrip' ? formValues.returnDate : null,
        passengers: formValues.passengers,
      });
      setResults(data);
      setStatus(STATUS.SUCCESS);
    } catch (err) {
      setErrorMessage(err.message);
      setStatus(STATUS.ERROR);
    }
  }

  function handleRetry() {
    if (searchParams) handleSearch(searchParams);
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-inner">
          <span className="logo" aria-label="Flight Search">✈️</span>
          <h1 className="app-title">Flight Search</h1>
          <p className="app-subtitle">Find the best flights for your journey</p>
        </div>
      </header>

      {/* Main content */}
      <main className="app-main">
        <SearchForm onSearch={handleSearch} loading={status === STATUS.LOADING} />

        {status === STATUS.LOADING && <LoadingState />}

        {status === STATUS.ERROR && (
          <ErrorState message={errorMessage} onRetry={handleRetry} />
        )}

        {status === STATUS.SUCCESS && results && (
          <FlightList results={results} searchParams={searchParams} />
        )}
      </main>

      <footer className="app-footer">
        <p>Prices shown are per-booking estimates. Actual fares may vary.</p>
      </footer>
    </div>
  );
}
