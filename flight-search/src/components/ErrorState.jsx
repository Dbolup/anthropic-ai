import './ErrorState.css';

export default function ErrorState({ message, onRetry }) {
  return (
    <div className="error-state" role="alert" aria-live="assertive">
      <span className="error-icon" aria-hidden="true">⚠️</span>
      <p className="error-title">Something went wrong</p>
      <p className="error-message">{message || 'An unexpected error occurred. Please try again.'}</p>
      {onRetry && (
        <button className="retry-btn" onClick={onRetry}>
          Try Again
        </button>
      )}
    </div>
  );
}
