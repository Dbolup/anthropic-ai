import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SearchForm from '../components/SearchForm';

// Suppress CSS import errors in test environment
vi.mock('../components/SearchForm.css', () => ({}));

const tomorrow = new Date(Date.now() + 86400000).toISOString().split('T')[0];
const dayAfterTomorrow = new Date(Date.now() + 2 * 86400000).toISOString().split('T')[0];

describe('SearchForm', () => {
  let onSearch;

  beforeEach(() => {
    onSearch = vi.fn();
  });

  function renderForm(loading = false) {
    return render(<SearchForm onSearch={onSearch} loading={loading} />);
  }

  it('renders all required fields', () => {
    renderForm();
    expect(screen.getByLabelText(/from/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/to/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/departure/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/passengers/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /search flights/i })).toBeInTheDocument();
  });

  it('shows return date field when round-trip is selected', () => {
    renderForm();
    expect(screen.getByLabelText(/return/i)).toBeInTheDocument();
  });

  it('hides return date field when one-way is selected', async () => {
    const user = userEvent.setup();
    renderForm();
    await user.click(screen.getByRole('radio', { name: /one-way/i }));
    expect(screen.queryByLabelText(/return/i)).not.toBeInTheDocument();
  });

  it('shows validation error when origin is empty on submit', async () => {
    const user = userEvent.setup();
    renderForm();
    await user.click(screen.getByRole('button', { name: /search flights/i }));
    expect(await screen.findByText(/valid origin/i)).toBeInTheDocument();
    expect(onSearch).not.toHaveBeenCalled();
  });

  it('shows error when origin and destination are the same', async () => {
    const user = userEvent.setup();
    renderForm();
    await user.type(screen.getByLabelText(/from/i), 'JFK');
    await user.type(screen.getByLabelText(/to/i), 'JFK');
    fireEvent.change(screen.getByLabelText(/departure/i), { target: { value: tomorrow } });
    await user.click(screen.getByRole('button', { name: /search flights/i }));
    expect(await screen.findByText(/different/i)).toBeInTheDocument();
  });

  it('shows error when no departure date', async () => {
    const user = userEvent.setup();
    renderForm();
    await user.type(screen.getByLabelText(/from/i), 'JFK');
    await user.type(screen.getByLabelText(/to/i), 'LAX');
    await user.click(screen.getByRole('button', { name: /search flights/i }));
    expect(await screen.findByText(/departure date/i)).toBeInTheDocument();
  });

  it('calls onSearch with form values when form is valid', async () => {
    const user = userEvent.setup();
    renderForm();

    // Switch to one-way to avoid needing a return date
    await user.click(screen.getByRole('radio', { name: /one-way/i }));
    await user.type(screen.getByLabelText(/from/i), 'JFK');
    await user.type(screen.getByLabelText(/to/i), 'LAX');
    fireEvent.change(screen.getByLabelText(/departure/i), { target: { value: tomorrow } });

    await user.click(screen.getByRole('button', { name: /search flights/i }));

    await waitFor(() => expect(onSearch).toHaveBeenCalledOnce());
    const call = onSearch.mock.calls[0][0];
    expect(call.origin).toBe('JFK');
    expect(call.destination).toBe('LAX');
    expect(call.departureDate).toBe(tomorrow);
    expect(call.tripType).toBe('oneway');
    expect(call.passengers).toBe(1);
  });

  it('disables the submit button while loading', () => {
    renderForm(true);
    expect(screen.getByRole('button', { name: /searching/i })).toBeDisabled();
  });
});
