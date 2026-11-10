import assert from 'node:assert/strict';
import {textbook} from '../dist/curriculum.js';
import {FIELDS_BY_KIND,kindOf,available} from '../dist/parser.js';
const {units,vocabulary,analyses}=textbook;
assert.equal(new Set(units.map(u=>u.id)).size,units.length);
assert(units.every((u,i)=>i===0||units[i-1].id<u.id));
const known=new Map(vocabulary.map(v=>[v.lemma,v]));
for(const a of analyses){
  assert(a.word&&a.lemma&&known.has(a.lemma),`Missing lemma for ${JSON.stringify(a)}`);
  assert(Number.isInteger(a.unit)&&a.unit>=known.get(a.lemma).unit&&a.unit<=20,`Invalid unit for ${JSON.stringify(a)}`);
  const kind=kindOf(a);assert(FIELDS_BY_KIND[kind],`Unsupported kind ${kind}`);
  for(const key of FIELDS_BY_KIND[kind])assert(a[key],`Missing ${key} on ${JSON.stringify(a)}`);
}
assert(available(analyses,2,'Finite').length>6);
assert(available(analyses,2,'Infinitive').length>0);
assert.equal(available(analyses,7,'Participle').length,0);
assert(available(analyses,8,'Participle').length>0);
console.log(`Validated ${analyses.length} analyses in ${textbook.id}.`);
assert(!analyses.some(a=>a.lemma==='ὁράω'&&a.word==='ὀψάς'&&a.source==='generated'),'Unreviewed alternative aorist stem leaked into exercises');
console.log('Unchecked irregular alternatives are excluded.');
assert(analyses.every(a=>/^[\p{Script=Greek}\p{M}]+$/u.test(a.word)), 'Dataset contains a malformed word form');
assert(available(analyses,11,'Finite').some(a=>a.lemma==='δέχομαι'&&a.word==='δέχομαι'&&a.voice==='Middle'));
assert(!available(analyses,10,'Finite').some(a=>a.lemma==='δέχομαι'));
console.log('Greek text and middle-deponent introduction checks passed.');
