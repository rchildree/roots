import assert from 'node:assert/strict';
import {checkStructure,structurallySound} from '../dist/parser.js';
// Positions are grapheme indices into the displayed word (inclusive).
const ob=(text,category,start,end=start+[...text].length-1)=>({text,category,start,end});
const types=(observations,length)=>checkStructure(observations,length).map(p=>p.type);

// ἐκελεύομεν: ἐ0 κ1 ε2 λ3 ε4 ύ5 ο6 μ7 ε8 ν9
const good=[ob('ἐ','Augment',0),ob('κελεύ','Present stem',1),ob('ο','Thematic vowel',6),ob('μεν','Personal ending',7)];
assert.deepEqual(checkStructure(good,10),[]);
assert.deepEqual(structurallySound(good,10),good);

// A piece selected after one that must follow it.
assert.deepEqual(types([ob('ο','Augment',6),ob('κελεύ','Present stem',1)],10),['order']);
assert.deepEqual(types([ob('ο','Thematic vowel',6),ob('λεύ','Present stem',3),ob('ε','Tense / mood marker',2)],10),['order']);
// Two labels claiming the same letters.
assert.deepEqual(types([ob('ἐκ','Augment',0),ob('κελεύ','Present stem',1)],10),['overlap']);
// An ending must reach the end of the word, wherever its letters also occur.
assert.deepEqual(types([ob('ε','Personal ending',8)],10),['not-final']);
assert.deepEqual(types([ob('μεν','Personal ending',7)],10),[]);
// μένομεν: the first μεν is not the ending although the letters match.
assert.deepEqual(types([ob('μέν','Personal ending',0)],7),['not-final']);
assert.deepEqual(types([ob('ειν','Infinitive ending',2)],5),[]);
assert.deepEqual(types([ob('οντ','Nominal ending',2)],7),['not-final']);

// Problems name the observations involved and explain themselves.
const [problem]=checkStructure([ob('ο','Augment',6),ob('κελεύ','Present stem',1)],10);
assert.deepEqual(problem.indexes,[0,1]);
assert.match(problem.message,/augment/i);
assert.match(problem.message,/present stem/i);

// Conflicting observations are withheld from narrowing; sound ones are kept.
const mixed=[ob('ο','Augment',6),ob('κελεύ','Present stem',1),ob('μεν','Personal ending',7)];
assert.deepEqual(structurallySound(mixed,10),[mixed[2]]);

// Observations without positions (older callers) are not judged.
assert.deepEqual(checkStructure([{text:'μεν',category:'Personal ending'},{text:'ἐ',category:'Augment'}],10),[]);
console.log('Structure checks passed.');
