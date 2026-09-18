import './LoadingState.css';

export default function LoadingState({ message = 'Searching for the best flights…' }) {
  return (
    <div className="loading-state" role="status" aria-live="polite" aria-label={message}>
      <div className="loading-plane" aria-hidden="true">✈️</div>
      <p className="loading-text">{message}</p>
      <div className="loading-bar" aria-hidden="true">
        <div className="loading-bar-fill" />
      </div>
    </div>
  );
}
