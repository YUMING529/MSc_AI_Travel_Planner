export async function generateTrip(preferences) {
  let response;
  try {
    response = await fetch('/api/trips/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(preferences),
      signal: AbortSignal.timeout(450000),
    });
  } catch (error) {
    throw new Error(error.name === 'TimeoutError'
      ? 'Planning timed out. Please try again.'
      : 'Cannot reach the planner. Check that the Flask server is running and try again.');
  }
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.error?.message || 'The planner could not complete your request. Please try again.');
  if (!data?.trip?.itinerary?.days || !data.trip.itinerary.costs) throw new Error('The planner returned an incomplete itinerary. Please try again.');
  return data.trip;
}
