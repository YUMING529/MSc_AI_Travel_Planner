import test from 'node:test';
import assert from 'node:assert/strict';
import {readSavedTrips,validSavedTrip} from '../src/services/savedTrips.js';
import {money,duration} from '../src/data/mockTrip.js';
test('currency preserves pence and date duration is stable across DST',()=>{
 assert.equal(money(12.34),'£12.34');assert.equal(money(1200),'£1,200');
 assert.equal(duration({start:'2026-10-24',end:'2026-10-26'}),3);
});
test('corrupt browser data cannot crash saved trips',()=>{
 for(const value of ['{','null','{}','[null,{},3]']) assert.deepEqual(readSavedTrips({getItem:()=>value}),[]);
 assert.deepEqual(readSavedTrips({getItem:()=>{throw Error('denied')}}),[]);
 const trip={id:'1',destination:'Cardiff',start:'2026-11-01',end:'2026-11-01',travellers:2,budget:200,interests:[],itinerary:{days:[{date:'2026-11-01',activities:[{title:'Museum',tags:[],cost:0}]}],costs:[{label:'Food',value:30}]}};
 assert.equal(validSavedTrip(trip),true);
 assert.equal(validSavedTrip({...trip,itinerary:{days:[{}],costs:[]}}),false);
 assert.equal(validSavedTrip({...trip,travellers:1.5}),false);
});
test('malformed activity objects are rejected without discarding other valid entries',()=>{
 const valid={id:'old',destination:'London',start:'2026-11-01',end:'2026-11-02',travellers:1,budget:500,interests:[]};
 const broken={...valid,id:'broken',itinerary:{days:[null],costs:[{label:'Food',value:10}]}};
 assert.deepEqual(readSavedTrips({getItem:()=>JSON.stringify([broken,valid])}),[valid]);
});
