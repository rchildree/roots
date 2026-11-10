import assert from 'node:assert/strict';
import {paradigms} from '../dist/paradigms.js';
import {segments} from '../dist/segments.js';
import {available,analysesForWord,filterByPieces,filterByObservations,grammaticalTuples,verifyObservation,distinct,segmentsFor} from '../dist/parser.js';

const letters=word=>Array.from(new Intl.Segmenter('el',{granularity:'grapheme'}).segment(word),x=>x.segment);
// Label the first (or nth) occurrence of `text` in `word`.
const pick=(word,text,category,nth=0)=>{const l=letters(word),t=letters(text);let seen=0;for(let i=0;i+t.length<=l.length;i++)if(t.every((c,j)=>l[i+j]===c)&&seen++===nth)return {text,category,start:i,end:i+t.length-1};throw new Error(`${text} not in ${word}`)};
const status=(word,text,category,nth)=>verifyObservation(pick(word,text,category,nth),analysesForWord(paradigms,word,20),segments).status;

// The original false positives are now rejected, each for its own reason.
assert.equal(status('ἐκέλευες','λευ','Augment'),'misplaced');
assert.equal(status('ἐκελεύομεν','ο','Augment'),'label');
assert.equal(status('ἐκελεύομεν','ελεύομεν','Personal ending'),'boundary');
assert.equal(status('ἐκελεύομεν','εν','Personal ending'),'boundary');
assert.equal(status('παύσομεν','ύ','Future stem'),'boundary');
assert.equal(status('κελεύομεν','κελεύ','Aorist stem'),'label');
assert.equal(status('κελεύομεν','ελ','Reduplication'),'absent');
// μένομεν: only the final μεν is the ending.
assert.equal(status('μένομεν','μέν','Personal ending'),'label');
assert.equal(status('μένομεν','μεν','Personal ending'),'correct');
console.log('Wrong labels are rejected.');

// Correct labels, including the alternatives a textbook would accept.
for(const [word,text,category,nth] of [
 ['ἐκελεύομεν','ἐ','Augment'],['ἐκελεύομεν','κελεύ','Present stem'],['ἐκελεύομεν','ο','Thematic vowel'],
 ['ἐκελεύομεν','μεν','Personal ending'],['ἐκελεύομεν','ομεν','Personal ending'],
 ['ἦγον','ἦ','Augment'],['ἦγον','ἦγ','Present stem'],['ἦγον','ν','Personal ending'],['ἦγον','ον','Personal ending'],
 ['κελεύεις','εις','Personal ending'],['κελεύουσι','ουσι','Personal ending'],
 ['κελεύουσιν','ουσι','Personal ending'],['κελεύουσιν','ουσιν','Personal ending'],
 ['παύσομεν','παύσ','Future stem'],['παύσομεν','παύ','Future stem'],['παύσομεν','σ','Tense / mood marker'],
 ['πέμψομεν','πέμψ','Future stem'],['πέμψομεν','ψ','Tense / mood marker'],
 ['ἐκέλευσα','σ','Tense / mood marker'],['ἐκέλευσα','σα','Tense / mood marker'],['ἐκέλευσα','α','Personal ending'],
 ['πεποίηκα','πε','Reduplication'],['πεποίηκα','πεποίηκ','Perfect stem'],['πεποίηκα','κ','Tense / mood marker'],
 ['ἀποθάνοιμεν','ἀποθάν','Aorist stem'],['ἀποθάνοιμεν','θάν','Aorist stem'],['ἀποθάνοιμεν','οι','Tense / mood marker'],
 ['κελεύωμεν','ω','Tense / mood marker'],['κελεύωμεν','ω','Thematic vowel'],
 ['ἀδικοῦμεν','ἀδικ','Present stem'],['ἀδικοῦμεν','οῦ','Thematic vowel'],['ἀδικοῦμεν','οῦμεν','Personal ending'],
 ['κελεύειν','ειν','Infinitive ending'],['βούλεσθαι','σθαι','Infinitive ending'],['βούλεσθαι','εσθαι','Infinitive ending'],
 ['γράφοντες','ες','Nominal ending'],['γράφοντες','οντες','Nominal ending'],['γράφοντες','ντ','Tense / mood marker'],
 // aorist and future passive, perfect middle, pluperfect, imperative
 ['ἐλύθην','θη','Tense / mood marker'],['ἐλύθην','θ','Tense / mood marker'],['ἐλύθην','λύθ','Aorist stem'],['ἐλύθην','λύ','Aorist stem'],
 ['ἐλύθην','ν','Personal ending'],['ἐλύθην','ην','Personal ending'],
 ['λυθήσομαι','θήσ','Tense / mood marker'],['λυθήσομαι','λυθήσ','Future stem'],['λυθήσομαι','ομαι','Personal ending'],
 ['λυθέντος','έντος','Nominal ending'],['λυθέντος','ος','Nominal ending'],['λυθῶμεν','ῶμεν','Personal ending'],
 ['λέλυμαι','λέ','Reduplication'],['λέλυμαι','λέλυ','Perfect stem'],['λέλυμαι','μαι','Personal ending'],
 ['ἐλελύκη','ἐ','Augment'],['ἐλελύκη','λε','Reduplication'],['ἐλελύκη','κ','Tense / mood marker'],['ἐλελύκη','η','Personal ending'],
 ['ἐλυσάμην','σά','Tense / mood marker'],['ἐλυσάμην','άμην','Personal ending'],['λῦσον','ον','Personal ending'],
])assert.equal(status(word,text,category,nth),'correct',`${word}: ${text} as ${category}`);
// -μι verbs
for(const [word,text,category] of [['δίδωμι','δί','Reduplication'],['δίδωμι','δω','Present stem'],['δίδωμι','δίδω','Present stem'],['δίδωμι','μι','Personal ending'],
 ['ἐδίδουν','ἐ','Augment'],['ἔδωκα','κ','Tense / mood marker'],['ἔδομεν','δο','Aorist stem'],['ἵσταμεν','ἵ','Reduplication'],['διδοίην','ίη','Tense / mood marker'],['διδόναι','ναι','Infinitive ending']])
 assert.equal(status(word,text,category),'correct',`${word}: ${text} as ${category}`);
assert.equal(status('δίδωμι','δί','Augment'),'label');
for(const [word,text,category] of [['ἐδίδουν','ου','Thematic vowel'],['ἐδίδουν','ουν','Personal ending'],['διδούς','ς','Nominal ending'],['διδούς','ούς','Nominal ending'],['διδούς','ού','Tense / mood marker'],
 ['ἦν','ἦ','Augment'],['ἴμεν','μεν','Personal ending'],['ἕσταμεν','ἕ','Reduplication'],['ἔγνων','γνω','Aorist stem']])
 assert.equal(status(word,text,category),'correct',`${word}: ${text} as ${category}`);
assert.equal(status('ἔστη','η','Personal ending'),'absent');
assert.equal(status('ἐλύθην','θην','Personal ending'),'boundary');
assert.equal(status('ἐλύθην','ἐλύθ','Aorist stem'),'boundary');
assert.equal(status('ἐλελύκη','ἐλε','Reduplication'),'boundary');
console.log('Correct labels are accepted.');

// Movable ν, shortened pieces, and forms without data.
assert.equal(status('κελεύουσιν','ν','Personal ending'),'movable');
assert.equal(status('κελεύουσιν','σιν','Personal ending'),'boundary');
assert.equal(status('ἦγον','γ','Present stem'),'boundary');
assert.equal(status('παύσομεν','παύ','Present stem'),'label');
assert.equal(verifyObservation({text:'ω',category:'Personal ending',start:1,end:1},[{word:'λύω',lemma:'none',tense:'Present',voice:'Active',mood:'Indicative',person:'1st singular'}],segments).status,'unchecked');
console.log('Movable ν, boundaries and unchecked forms are reported.');

// Narrowing uses the kind of piece, not letters found anywhere in a form.
const finite=available(paradigms,20,'Finite');
const pieced=observations=>filterByPieces(finite,observations,segments).filter(a=>segmentsFor(a,segments));
assert.deepEqual(distinct(pieced([{text:'πε',category:'Reduplication'}]).map(a=>a.tense)).sort(),['Perfect','Pluperfect']);
assert(pieced([{text:'δι',category:'Reduplication'}]).every(a=>a.lemma==='δίδωμι'&&['Present','Imperfect'].includes(a.tense)));
assert(pieced([{text:'σ',category:'Tense / mood marker'}]).every(a=>['Future','Aorist'].includes(a.tense)));
// κ marks the perfect system, and the aorist of δίδωμι and τίθημι (ἔδωκα, ἔθηκα, ἧκα).
assert(pieced([{text:'κ',category:'Tense / mood marker'}]).every(a=>['Perfect','Pluperfect'].includes(a.tense)||(a.tense==='Aorist'&&['δίδωμι','τίθημι','ἵημι'].includes(a.lemma))));
assert(pieced([{text:'ω',category:'Thematic vowel'}]).length>0);
assert.equal(filterByPieces(analysesForWord(paradigms,'ἐκέλευες',20),[{text:'λευ',category:'Augment'}],segments).length,0);
assert(filterByObservations(analysesForWord(paradigms,'ἐκέλευες',20),[{text:'λευ',category:'Augment'}]).length>0,'the old letter-matching check accepted this');
// The clues that identified a form before still do.
const u2=available(paradigms,2);
assert.deepEqual(grammaticalTuples(filterByPieces(u2,[{text:'ἐ',category:'Augment'},{text:'λύ',category:'Present stem'},{text:'μεν',category:'Personal ending'}],segments)),['1st plural|Imperfect|Active|Indicative']);
const optative=filterByPieces(finite,[{text:'ἀποθάν',category:'Aorist stem'},{text:'οι',category:'Tense / mood marker'},{text:'μεν',category:'Personal ending'}],segments);
assert.deepEqual(grammaticalTuples(optative),['1st plural|Aorist|Active|Optative']);
console.log('Narrowing by pieces passed.');
