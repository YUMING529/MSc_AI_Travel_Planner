import React,{useState} from 'react';
import Icon from '../components/Icon';
import {dates,money,duration} from '../data/mockTrip';
export default function MyTrips({trips,onView,onPlan,onDelete,onUndo,deleted}) {
  const [query,setQuery]=useState('');
  const [sort,setSort]=useState('saved');
  const shown=trips.filter(t=>t.destination.toLowerCase().includes(query.trim().toLowerCase()));
  if(sort==='start') shown.sort((a,b)=>a.start.localeCompare(b.start));
  if(sort==='destination') shown.sort((a,b)=>a.destination.localeCompare(b.destination));
  return <section className="saved-page">
    <div className="eyebrow">YOUR SAVED PLANS</div>
    <div className="saved-heading"><div><h1>My Trips</h1><p className="muted">Compare your plans, revisit the details, and keep what matters.</p></div><button className="primary" onClick={onPlan}>Plan a Trip <Icon name="arrow"/></button></div>
    {deleted&&<div className="saved-undo" role="status"><span>Deleted {deleted.trip.destination} · {dates(deleted.trip)}. You can undo your last deletion until you refresh.</span><button className="text-button" onClick={onUndo}>Undo delete</button></div>}
    {trips.length>0&&<div className="saved-tools">
      <label>Search destination<input type="search" placeholder="e.g. London" value={query} onChange={e=>setQuery(e.target.value)}/></label>
      <label>Sort by<select value={sort} onChange={e=>setSort(e.target.value)}><option value="saved">Recently saved</option><option value="start">Travel date (earliest first)</option><option value="destination">Destination (A–Z)</option></select></label>
      <p className="muted" aria-live="polite">{shown.length} of {trips.length} saved plans</p>
    </div>}
    {shown.length>0?<div className="saved-grid">{shown.map(t=><article className="saved-card card" key={t.id}>
      <div className="saved-body"><div className="saved-card-top"><span className="tiny-tag">{t.itinerary?.mode==='qwen'?'Qwen · AI plan':'Sample plan'}</span><button className="delete-trip" onClick={()=>onDelete(t.id)} aria-label={'Delete '+t.destination+' trip, '+dates(t)}>Delete</button></div>
      <h2>{t.destination}</h2><p className="muted">{dates(t)}<br/>{duration(t)} {duration(t)===1?'day':'days'} · {t.travellers} traveller{t.travellers>1?'s':''}</p>
      <div className="tags">{t.interests.map(i=><span key={i}>{i}</span>)}</div>
      <dl className="saved-costs"><div><dt>Group budget</dt><dd>{money(t.budget)}</dd></div>{Number.isFinite(t.itinerary?.total)&&<div><dt>Estimated total</dt><dd className={t.itinerary.total>Number(t.budget)?'amber':''}>{money(t.itinerary.total)}{t.itinerary.total>Number(t.budget)&&<small>Over budget</small>}</dd></div>}</dl>
      <div className="saved-bottom"><button className="text-button" onClick={()=>onView(t)}>View Plan <Icon name="arrow" size={17}/></button></div></div>
    </article>)}</div>:<div className="empty card"><Icon name="save" size={36}/><h2>{trips.length?'No matching trips.':'Your next escape is waiting.'}</h2><p>{trips.length?'Try another destination or clear your search.':'Generate a plan and save it here to come back to later.'}</p><button className="primary" onClick={trips.length?()=>setQuery(''):onPlan}>{trips.length?'Clear search':'Plan my first trip'}</button></div>}
    <p className="prototype-note">Trips are saved in this browser only. Clearing browser data removes your saved plans.</p>
  </section>;
}
