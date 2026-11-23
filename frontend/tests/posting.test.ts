import assert from 'node:assert/strict';
import test from 'node:test';
import { postingMaterial, groupPostings } from '../src/posting.ts';

test('formats provided posting fields in source order and keeps the description intact', () => {
  assert.equal(postingMaterial({ Location:' Pune ', Company:' ', Industry:'Retail' }, 'Line 1\nLine 2'),
    'Location: Pune\nIndustry: Retail\nJob description:\nLine 1\nLine 2');
  assert.equal(postingMaterial({}, '  '), '');
});

test('insights count distinct cases, preserve missing data and respect review decisions', () => {
  const entity = (value:string, review_status:string) => ({type:'location_claim', value, review_status});
  const item = {id:1, title:'Test', case_ref:'RC-1', assessment:'Insufficient evidence', entities:[
    entity('Pune','confirmed'), entity(' PUNE ','needs_review'), entity('Delhi','rejected'), entity('Mumbai','needs_review'),
  ]};
  const cases = [item, {...item, id:2, entities:[]}];
  const groups = groupPostings(cases, 'location_claim', false);
  assert.deepEqual(groups.map(g => [g.key, g.cases.length]), [['',1],['mumbai',1],['pune',1]]);
  assert.deepEqual(groupPostings(cases, 'location_claim', true).map(g => g.key), ['', 'pune']);
  assert.equal(groupPostings(cases, 'industry_claim', false)[0].cases.length, 2);
});
