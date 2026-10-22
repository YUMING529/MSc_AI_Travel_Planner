export const destinations=['London', 'Edinburgh', 'Manchester', 'Birmingham', 'Liverpool', 'Glasgow', 'Bristol', 'Leeds', 'Cardiff', 'Belfast', 'Newcastle', 'Nottingham', 'Sheffield', 'Oxford', 'Cambridge', 'Bath', 'York'];
export const interests=['History','Food','Photography','Nature','Shopping','Art & Culture','Nightlife'];
const isoDate=d=>`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
const tomorrow=new Date();tomorrow.setDate(tomorrow.getDate()+1);
const nextDay=new Date(tomorrow);nextDay.setDate(nextDay.getDate()+1);
export const initialPreferences={destination:'London',start:isoDate(tomorrow),end:isoDate(nextDay),currency:'GBP',budget:500,travellers:1,interests:['History','Food','Photography'],notes:''};
export const money=(n,c='GBP')=>new Intl.NumberFormat('en-GB',{style:'currency',currency:c,minimumFractionDigits:0,maximumFractionDigits:2}).format(n);
export const duration=p=>Math.round((new Date(p.end)-new Date(p.start))/86400000)+1;
export const dates=p=>`${new Date(p.start+'T12:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short'})} – ${new Date(p.end+'T12:00:00').toLocaleDateString('en-GB',{day:'numeric',month:'short',year:'numeric'})}`;
export const days=[[
 {time:'10:30 – 12:30',period:'Morning',title:'British Museum',description:'A slow morning exploring ancient civilisations and the museum’s light-filled Great Court.',tags:['History','Photography'],cost:0,icon:'museum',note:'Free permanent collection · Check opening hours',travel:'30 min by Tube + a short walk'},
 {time:'13:00 – 16:00',period:'Afternoon',title:'Borough Market & South Bank',description:'Pick up lunch from the market, then follow the Thames for riverside views.',tags:['Food','Photography'],cost:15,icon:'food',note:'Lunch allowance · Estimated price',travel:'20 min walk to Tower Bridge'},
 {time:'17:30 – 20:30',period:'Evening',title:'Tower Bridge & a local dinner',description:'Catch the evening light by the bridge before a relaxed neighbourhood dinner.',tags:['Photography','Food'],cost:25,icon:'camera',note:'Exterior visit · Dinner allowance'}
],[
 {time:'10:00 – 12:00',period:'Morning',title:'Westminster & St James’s Park',description:'Take in Westminster’s landmarks from outside, then wander through the park.',tags:['History','Nature','Photography'],cost:0,icon:'nature',note:'Outdoor route · Weather dependent',travel:'25 min by Tube + walking'},
 {time:'12:30 – 16:00',period:'Afternoon',title:'Covent Garden & a gallery visit',description:'Enjoy lunch and independent shops, with an optional ticketed art exhibition.',tags:['Art & Culture','Food','Shopping'],cost:60,icon:'museum',note:'£20 lunch + £40 exhibition allowance · Verify availability',travel:'20 min by Tube to King’s Cross'},
 {time:'16:30 – 17:30',period:'Evening',title:'A final bite at King’s Cross',description:'An early dinner near the station, leaving time for your journey home.',tags:['Food'],cost:30,icon:'food',note:'£20 dinner + £10 snacks allowance'}
]];
export function costs(p){const n=Number(p.travellers);return [{label:'Intercity transport',value:120*n},{label:'Accommodation',value:140*Math.ceil(n/2)},{label:'Food',value:90*n},{label:'Activities',value:40*n},{label:'Local transport',value:30*n}];}
