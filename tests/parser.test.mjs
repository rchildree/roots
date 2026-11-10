import assert from 'node:assert/strict';
import {paradigms} from '../dist/paradigms.js';
import {available,analysesForWord,filterByObservations,grammaticalTuples,answerIsValid,formTypes,inferFormChoice} from '../dist/parser.js';
const u2=available(paradigms,2);
const find=(word)=>analysesForWord(paradigms,word,20);
assert(find('ἔλυον').some(x=>x.person==='1st singular'));
assert(find('ἔλυον').some(x=>x.person==='3rd plural'));
assert(find('λύει').some(x=>x.voice==='Active'&&x.person==='3rd singular'));
assert(find('λύει').some(x=>x.voice==='Passive'&&x.person==='2nd singular'));
assert(!analysesForWord(paradigms,'λύει',2).some(x=>x.voice==='Passive'));
let a=filterByObservations(u2,[{text:'ἐ',category:'Augment'},{text:'λύ',category:'Present stem'},{text:'μεν',category:'Personal ending'}]);
assert.deepEqual(grammaticalTuples(a),['1st plural|Imperfect|Active|Indicative']);
let withVowel=filterByObservations(u2,[{text:'ἐ',category:'Augment'},{text:'λύ',category:'Present stem'},{text:'μεν',category:'Personal ending'},{text:'ο',category:'Thematic vowel'}]);
assert.deepEqual(grammaticalTuples(a),grammaticalTuples(withVowel));
assert(answerIsValid(paradigms,'ἔλυον',2,{lemma:'λύω',tense:'Imperfect',voice:'Active',mood:'Indicative',person:'1st singular'}));
assert(answerIsValid(paradigms,'ἔλυον',2,{lemma:'λύω',tense:'Imperfect',voice:'Active',mood:'Indicative',person:'3rd plural'}));
assert(!answerIsValid(paradigms,'ἔλυον',2,{lemma:'λύω',tense:'Aorist',voice:'Active',mood:'Indicative',person:'3rd plural'}));
console.log('Parser checks passed.');
assert(answerIsValid(paradigms,'λύειν',2,{lemma:'λύω',tense:'Present',voice:'Active'},'Infinitive'));
assert(!answerIsValid(paradigms,'λύειν',2,{lemma:'λύω',tense:'Aorist',voice:'Active'},'Infinitive'));
assert.equal(analysesForWord(paradigms,'λύων',7,'Participle').length,0);
assert(answerIsValid(paradigms,'λύων',8,{lemma:'λύω',tense:'Present',voice:'Active',case:'Nominative',number:'Singular',gender:'Masculine'},'Participle'));
assert(!answerIsValid(paradigms,'λύων',8,{lemma:'λύω',tense:'Present',voice:'Active',case:'Accusative',number:'Singular',gender:'Masculine'},'Participle'));
assert(analysesForWord(paradigms,'λῦον',8,'Participle').some(x=>x.case==='Nominative'&&x.gender==='Neuter'));
assert(analysesForWord(paradigms,'λῦον',8,'Participle').some(x=>x.case==='Accusative'&&x.gender==='Neuter'));
console.log('Infinitive and participle checks passed.');

const mixed=available(paradigms,11);
const infinitiveCandidates=filterByObservations(mixed,[{text:'ειν',category:'Infinitive ending'}]);
assert(infinitiveCandidates.length>0);
assert.deepEqual(formTypes(infinitiveCandidates),['Infinitive']);
const personalCandidates=filterByObservations(mixed,[{text:'μεν',category:'Personal ending'}]);
assert(personalCandidates.length>0);
assert(formTypes(personalCandidates).every(k=>k==='Finite'||k==='Imperative'));
console.log('Form-type evidence checks passed.');

assert.equal(inferFormChoice([{category:'Infinitive ending',text:'ειν'}],paradigms,2),'Infinitive');
assert.equal(inferFormChoice([{category:'Personal ending',text:'μεν'}],paradigms,2),'Finite');
assert.equal(inferFormChoice([{category:'Personal ending',text:'ε'}],paradigms,11),'');
assert.equal(inferFormChoice([{category:'Nominal ending',text:'ων'}],paradigms,8),'Participle');
assert.equal(inferFormChoice([{category:'Augment',text:'ἐ'},{category:'Infinitive ending',text:'ειν'}],paradigms,8),'');
console.log('Evidence-driven recognition checks passed.');
assert(answerIsValid(paradigms,'ἀποθάνοιμεν',20,{lemma:'ἀποθνῄσκω',person:'1st plural',tense:'Aorist',voice:'Active',mood:'Optative'}));
console.log('Second-aorist regression check passed.');

const optative=filterByObservations(available(paradigms,20,'Finite'),[{text:'ἀποθάν',category:'Aorist stem'},{text:'οι',category:'Tense / mood marker'},{text:'μεν',category:'Personal ending'}]);
assert.deepEqual(grammaticalTuples(optative),['1st plural|Aorist|Active|Optative']);
assert.equal(inferFormChoice([{text:'οι',category:'Tense / mood marker'}],paradigms,20),'Finite');
console.log('Optative-marker inference checks passed.');

// Data repairs: aorist third singulars exist, with and without movable ν.
assert(answerIsValid(paradigms,'ἐκέλευσε',2,{lemma:'κελεύω',person:'3rd singular',tense:'Aorist',voice:'Active',mood:'Indicative'}));
assert(answerIsValid(paradigms,'ἐκέλευσεν',2,{lemma:'κελεύω',person:'3rd singular',tense:'Aorist',voice:'Active',mood:'Indicative'}));
assert(answerIsValid(paradigms,'ἔμαθεν',20,{lemma:'μανθάνω',person:'3rd singular',tense:'Aorist',voice:'Active',mood:'Indicative'}));
for(const lemma of new Set(paradigms.filter(a=>a.tense==='Aorist'&&a.mood==='Indicative'&&a.voice==='Active'&&a.person==='1st singular').map(a=>a.lemma)))
 assert(paradigms.some(a=>a.lemma===lemma&&a.tense==='Aorist'&&a.mood==='Indicative'&&a.voice==='Active'&&a.person==='3rd singular'),`no aorist third singular for ${lemma}`);
// The later form εἴχοσαν is not offered; the Attic imperfect is.
assert(!paradigms.some(a=>a.word==='εἴχοσαν'));
assert(answerIsValid(paradigms,'εἶχον',20,{lemma:'ἔχω',person:'3rd plural',tense:'Imperfect',voice:'Active',mood:'Indicative'}));
assert(paradigms.some(a=>a.lemma==='ἀποδέχομαι')&&!paradigms.some(a=>a.lemma==='ἀποδεχόμαι'));
console.log('Data repair checks passed.');
