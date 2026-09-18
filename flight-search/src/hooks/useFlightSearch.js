import { useState } from 'react';

/**
 * Manages flight search form state and submission.
 */
export function useFlightSearch(onSearch) {
  const [form, setForm] = useState({
    origin: '',
    destination: '',
    departureDate: '',
    returnDate: '',
    passengers: 1,
    tripType: 'roundtrip',
  });

  function handleChange(e) {
    const { name, value, type } = e.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === 'number' ? Number(value) : value,
      // Clear return date when switching to one-way
      ...(name === 'tripType' && value === 'oneway' ? { returnDate: '' } : {}),
    }));
  }

  function handleSubmit(e) {
    e.preventDefault();
    onSearch(form);
  }

  return { form, handleChange, handleSubmit };
}
