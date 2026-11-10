// This is an inventory, not a claim that generated forms or segmentations are reviewed.
import {readFile} from 'node:fs/promises';
import {vocabulary} from '../dist/vocabulary.js';
import {paradigms} from '../dist/paradigms.js';
const dcc=JSON.parse(await readFile(new URL('../data/dcc-verbs.json',import.meta.url),'utf8'));
const canonical=s=>s.normalize('NFC');
const verbs=new Map(vocabulary.map(v=>[canonical(v.lemma),v]));
const analyses=new Map();
for(const a of paradigms){const k=canonical(a.lemma);analyses.set(k,(analyses.get(k)||0)+1)}
const records=dcc.map(x=>({...x, hq:verbs.has(canonical(x.candidate)), analyses:analyses.get(canonical(x.candidate))||0}));
const withForms=records.filter(x=>x.analyses>0);
const missing=records.filter(x=>!x.analyses);
const hqMissing=vocabulary.filter(x=>!analyses.has(canonical(x.lemma)));
console.log(`DCC verb entries: ${records.length}`);
console.log(`Exact headword matches with one or more existing analyses: ${withForms.length}`);
console.log(`DCC entries without an exact headword match in the analysis set: ${missing.length}`);
console.log(`DCC entries matching Hansen & Quinn vocabulary exactly: ${records.filter(x=>x.hq).length}`);
console.log(`Hansen & Quinn verbs with no existing analyses: ${hqMissing.length}`);
console.log('\nDCC entries without exact matches (aliases, dialects, and missing coverage require review):');
for(const x of missing)console.log(`${x.frequencyRank}\t${x.candidate}\t${x.partOfSpeech}`);
console.log('\nHansen & Quinn verbs without analyses:');
for(const x of hqMissing)console.log(`${x.lemma}\tunit ${x.unit}`);
console.log('\nAn existing analysis is not proof of a complete paradigm, a reviewed form, or a verified word-piece annotation.');
