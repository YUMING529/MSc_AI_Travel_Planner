export function validSavedTrip(trip) {
  if (!trip || typeof trip.id!=='string' || typeof trip.destination!=='string' || !Array.isArray(trip.interests) || !trip.interests.every(x=>typeof x==='string')) return false;
  if (!Number.isFinite(Number(trip.budget)) || Number(trip.budget)<=0 || !Number.isInteger(trip.travellers) || trip.travellers<1) return false;
  if (![trip.start,trip.end].every(d=>typeof d==='string'&&/^\d{4}-\d{2}-\d{2}$/.test(d)&&Number.isFinite(Date.parse(d))) || trip.end<trip.start) return false;
  if (trip.notes!==undefined && typeof trip.notes!=='string') return false;
  if (trip.itinerary?.warnings!==undefined && (!Array.isArray(trip.itinerary.warnings)||!trip.itinerary.warnings.every(w=>typeof w==='string'))) return false;
  if (!trip.itinerary) return trip.destination==='London'; // Legacy offline saves.
  return Array.isArray(trip.itinerary.days) && trip.itinerary.days.length>0 && trip.itinerary.days.every(d=>d&&typeof d.date==='string'&&Array.isArray(d.activities)&&d.activities.every(a=>a&&typeof a.title==='string'&&['time','period','description','note','travel','setting','weatherReason','indoorAlternative'].every(k=>a[k]===undefined||typeof a[k]==='string')&&Array.isArray(a.tags)&&a.tags.every(t=>typeof t==='string')&&Number.isFinite(a.cost)&&a.cost>=0)) && Array.isArray(trip.itinerary.costs) && trip.itinerary.costs.length>0 && trip.itinerary.costs.every(c=>c&&typeof c.label==='string'&&Number.isFinite(c.value)&&c.value>=0);
}
export function readSavedTrips(storage) {
  try {const parsed=JSON.parse(storage.getItem('tripmind-trips')||'[]');return Array.isArray(parsed)?parsed.filter(validSavedTrip).map(t=>{const w=t.itinerary?.weather;if(w&&(!Array.isArray(w.days)||!w.days.every(d=>d&&typeof d.date==='string'&&typeof d.reason==='string'&&['summary','status','recommendation'].every(k=>d[k]===undefined||typeof d[k]==='string')&&['temperatureMin','temperatureMax','rainProbability','windSpeed'].every(k=>d[k]===undefined||Number.isFinite(d[k]))))){const copy={...t,itinerary:{...t.itinerary}};delete copy.itinerary.weather;return copy;}return t;}):[];} catch {return [];}
}
