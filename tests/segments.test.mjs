import assert from 'node:assert/strict';
import {paradigms} from '../dist/paradigms.js';
import {segments} from '../dist/segments.js';
import {trainingExamples} from '../dist/training-examples.js';
import {segmentKey,segmentsFor,pieceRoles,exact} from '../dist/parser.js';

const show=pieces=>pieces.map(([text,role])=>`${text}:${role}`).join(' | ');
const expectPieces=(key,expected)=>{assert(segments[key],`missing segmentation for ${key}`);assert.equal(show(segments[key]),expected,key)};

// 1. Hand-checked cases covering each mechanism.
expectPieces('λύομεν|λύω|PAI','λύ:Present stem | ο:Thematic vowel | μεν:Personal ending');
expectPieces('ἐκελεύομεν|κελεύω|IAI','ἐ:Augment | κελεύ:Present stem | ο:Thematic vowel | μεν:Personal ending');
expectPieces('κελεύω|κελεύω|PAI','κελεύ:Present stem | ω:Thematic vowel + Personal ending');
expectPieces('παύσομεν|παύω|FAI','παύ:Verb stem | σ:Future marker | ο:Thematic vowel | μεν:Personal ending');
expectPieces('ἔλυσα|λύω|AAI','ἔ:Augment | λυ:Verb stem | σ:Aorist marker | α:Tense vowel + Personal ending');
// ψ and ξ hide the σ: the letter is both stem-final consonant and marker.
expectPieces('πέμψομεν|πέμπω|FAI','πέμ:Verb stem | ψ:Verb stem + Future marker | ο:Thematic vowel | μεν:Personal ending');
expectPieces('γράψασα|γράφω|AAP','γρά:Verb stem | ψ:Verb stem + Aorist marker | ασ:Tense vowel + Participle marker | α:Nominal ending');
// Liquid and second aorists have no separable marker.
expectPieces('ἔμεινα|μένω|AAI','ἔ:Augment | μειν:Aorist stem | α:Tense vowel + Personal ending');
expectPieces('ἔπαθον|πάσχω|AAI','ἔ:Augment | παθ:Aorist stem | ο:Thematic vowel | ν:Personal ending');
// A temporal augment is fused with the stem's first vowel.
expectPieces('ἦγον|ἄγω|IAI','ἦ:Augment + Present stem | γ:Present stem | ο:Thematic vowel | ν:Personal ending');
// Compounds: the augment follows the prefix.
expectPieces('ἀπέθανον|ἀποθνῄσκω|AAI','ἀπ:Prefix | έ:Augment | θαν:Aorist stem | ο:Thematic vowel | ν:Personal ending');
expectPieces('ὑπήκουον|ὑπακούω|IAI','ὑπ:Prefix | ή:Augment + Present stem | κου:Present stem | ο:Thematic vowel | ν:Personal ending');
expectPieces('συνεβούλευσα|συμβουλεύω|AAI','συν:Prefix | ε:Augment | βούλευ:Verb stem | σ:Aorist marker | α:Tense vowel + Personal ending');
expectPieces('ἀποθνῄσκομεν|ἀποθνῄσκω|PAI','ἀπο:Prefix | θνῄσκ:Present stem | ο:Thematic vowel | μεν:Personal ending');
// Contraction fuses the stem's final vowel with what follows.
expectPieces('ἀδικοῦμεν|ἀδικέω|PAI','ἀδικ:Present stem | οῦ:Present stem + Thematic vowel | μεν:Personal ending');
// Mood vowels and markers.
expectPieces('κελεύωμεν|κελεύω|PAS','κελεύ:Present stem | ω:Subjunctive vowel | μεν:Personal ending');
expectPieces('κελεύοιμεν|κελεύω|PAO','κελεύ:Present stem | οι:Optative marker | μεν:Personal ending');
// Perfect reduplication and marker.
expectPieces('πεποίηκα|ποιέω|XAI','πε:Reduplication | ποίη:Verb stem | κ:Perfect marker | α:Tense vowel + Personal ending');
// Infinitives and participles.
expectPieces('κελεύειν|κελεύω|PAN','κελεύ:Present stem | ειν:Thematic vowel + Infinitive ending');
expectPieces('γράφοντες|γράφω|PAP','γράφ:Present stem | ο:Thematic vowel | ντ:Participle marker | ες:Nominal ending');
expectPieces('βουλόμενος|βούλομαι|PMP','βουλ:Present stem | ό:Thematic vowel | μεν:Participle marker | ος:Nominal ending');
// Endings a learner cannot take apart stay whole: -εις, -ουσι.
expectPieces('κελεύεις|κελεύω|PAI','κελεύ:Present stem | εις:Thematic vowel + Personal ending');
expectPieces('κελεύῃς|κελεύω|PAS','κελεύ:Present stem | ῃ:Subjunctive vowel | ς:Personal ending');
expectPieces('κελεύουσι|κελεύω|PAI','κελεύ:Present stem | ουσι:Thematic vowel + Personal ending');
// Transparent endings stay cut; the checker may accept vowel and ending together.
expectPieces('ἐκέλευες|κελεύω|IAI','ἐ:Augment | κέλευ:Present stem | ε:Thematic vowel | ς:Personal ending');
// Movable ν is its own piece, never an ending.
expectPieces('κελεύουσιν|κελεύω|PAI','κελεύ:Present stem | ουσι:Thematic vowel + Personal ending | ν:Movable ν');
expectPieces('ἐκέλευσεν|κελεύω|AAI','ἐ:Augment | κέλευ:Verb stem | σ:Aorist marker | ε:Tense vowel + Personal ending | ν:Movable ν');
expectPieces('ἐκέλευσε|κελεύω|AAI','ἐ:Augment | κέλευ:Verb stem | σ:Aorist marker | ε:Tense vowel + Personal ending');
expectPieces('γράφουσιν|γράφω|PAP','γράφ:Present stem | ου:Thematic vowel + Participle marker | σι:Nominal ending | ν:Movable ν');
// Aorist and future passive: θ and its vowel are both the passive marker.
expectPieces('ἐλύθην|λύω|API','ἐ:Augment | λύ:Verb stem | θ:Passive marker | η:Passive marker | ν:Personal ending');
expectPieces('ἐλύθη|λύω|API','ἐ:Augment | λύ:Verb stem | θ:Passive marker | η:Passive marker + Personal ending');
expectPieces('ἐλήφθην|λαμβάνω|API','ἐ:Augment | λήφ:Verb stem | θ:Passive marker | η:Passive marker | ν:Personal ending');
expectPieces('λυθῶμεν|λύω|APS','λυ:Verb stem | θ:Passive marker | ῶ:Passive marker + Subjunctive vowel | μεν:Personal ending');
expectPieces('λυθείην|λύω|APO','λυ:Verb stem | θ:Passive marker | ε:Passive marker | ίη:Optative marker | ν:Personal ending');
expectPieces('λυθῆναι|λύω|APN','λυ:Verb stem | θ:Passive marker | ῆ:Passive marker | ναι:Infinitive ending');
expectPieces('λυθείς|λύω|APP','λυ:Verb stem | θ:Passive marker | εί:Passive marker + Participle marker | ς:Nominal ending');
expectPieces('λυθέντος|λύω|APP','λυ:Verb stem | θ:Passive marker | έ:Passive marker | ντ:Participle marker | ος:Nominal ending');
expectPieces('λυθήσομαι|λύω|FPI','λυ:Verb stem | θ:Passive marker | ή:Passive marker | σ:Future marker | ο:Thematic vowel | μαι:Personal ending');
// Aorist middle and the imperatives.
expectPieces('ἐλυσάμην|λύω|AMI','ἐ:Augment | λυ:Verb stem | σ:Aorist marker | ά:Tense vowel | μην:Personal ending');
expectPieces('ἐλύσω|λύω|AMI','ἐ:Augment | λύ:Verb stem | σ:Aorist marker | ω:Tense vowel + Personal ending');
expectPieces('λῦσαι|λύω|AMD','λῦ:Verb stem | σ:Aorist marker | αι:Personal ending');
expectPieces('λῦσον|λύω|AAD','λῦ:Verb stem | σ:Aorist marker | ον:Personal ending');
expectPieces('λυέτω|λύω|PAD','λυ:Present stem | έ:Thematic vowel | τω:Personal ending');
// Perfect middle and pluperfect.
expectPieces('λέλυμαι|λύω|XMI','λέ:Reduplication | λυ:Perfect stem | μαι:Personal ending');
expectPieces('λελυμένος|λύω|XMP','λε:Reduplication | λυ:Perfect stem | μέν:Participle marker | ος:Nominal ending');
expectPieces('ἐλελύκη|λύω|YAI','ἐ:Augment | λε:Reduplication | λύ:Verb stem | κ:Perfect marker | η:Tense vowel + Personal ending');
expectPieces('ἐλελύκειν|λύω|YAI','ἐ:Augment | λε:Reduplication | λύ:Verb stem | κ:Perfect marker | ει:Tense vowel + Personal ending | ν:Movable ν');
expectPieces('ἐλελύμην|λύω|YMI','ἐ:Augment | λε:Reduplication | λύ:Perfect stem | μην:Personal ending');
assert.deepEqual(segments['λέλυμαι|λύω|XPI'],segments['λέλυμαι|λύω|XMI']);
// -μι verbs: present reduplication, stem vowel in its own grade, endings added directly.
expectPieces('δίδωμι|δίδωμι|PAI','δί:Present reduplication | δω:Present stem | μι:Personal ending');
expectPieces('δίδομεν|δίδωμι|PAI','δί:Present reduplication | δο:Present stem | μεν:Personal ending');
expectPieces('διδόασι|δίδωμι|PAI','δι:Present reduplication | δό:Present stem | ασι:Personal ending');
expectPieces('ἐδίδουν|δίδωμι|IAI','ἐ:Augment | δί:Present reduplication | δ:Present stem | ου:Present stem + Thematic vowel | ν:Personal ending');
expectPieces('διδόναι|δίδωμι|PAN','δι:Present reduplication | δό:Present stem | ναι:Infinitive ending');
expectPieces('διδούς|δίδωμι|PAP','δι:Present reduplication | δ:Present stem | ού:Present stem + Participle marker | ς:Nominal ending');
expectPieces('διδοίην|δίδωμι|PAO','δι:Present reduplication | δο:Present stem | ίη:Optative marker | ν:Personal ending');
expectPieces('διδῶμεν|δίδωμι|PAS','δι:Present reduplication | δ:Present stem | ῶ:Present stem + Subjunctive vowel | μεν:Personal ending');
expectPieces('ἔδωκα|δίδωμι|AAI','ἔ:Augment | δω:Verb stem | κ:Aorist marker | α:Tense vowel + Personal ending');
expectPieces('ἔδομεν|δίδωμι|AAI','ἔ:Augment | δο:Aorist stem | μεν:Personal ending');
expectPieces('τίθημι|τίθημι|PAI','τί:Present reduplication | θη:Present stem | μι:Personal ending');
expectPieces('ἔθου|τίθημι|AMI','ἔ:Augment | θ:Aorist stem | ου:Aorist stem + Personal ending');
expectPieces('ἵσταμεν|ἵστημι|PAI','ἵ:Present reduplication | στα:Present stem | μεν:Personal ending');
expectPieces('ἔστην|ἵστημι|AAI','ἔ:Augment | στη:Aorist stem | ν:Personal ending');
expectPieces('ἔστη|ἵστημι|AAI','ἔ:Augment | στη:Aorist stem');
expectPieces('ἕστηκα|ἵστημι|XAI','ἕ:Reduplication | στη:Verb stem | κ:Perfect marker | α:Tense vowel + Personal ending');
expectPieces('δείκνυμι|δείκνυμι|PAI','δείκ:Present stem | νυ:Present stem | μι:Personal ending');
expectPieces('κεῖμαι|κεῖμαι|PMI','κεῖ:Present stem | μαι:Personal ending');
// Irregular forms cut from hand-given stems.
expectPieces('ἴμεν|εἶμι|PAI','ἴ:Present stem | μεν:Personal ending');
expectPieces('ἰόντων|εἶμι|PAD','ἰ:Present stem | ό:Thematic vowel | ντων:Personal ending');
expectPieces('ἦν|εἰμί|IAI','ἦ:Augment + Present stem | ν:Personal ending');
expectPieces('ὤν|εἰμί|PAP','ὤν:Thematic vowel + Participle marker + Nominal ending');
expectPieces('ἑστᾶσι|ἵστημι|XAI','ἑ:Reduplication | στ:Perfect stem | ᾶσι:Perfect stem + Personal ending');
expectPieces('ἦρκται|ἄρχω|XMI','ἦρκ:Perfect stem | ται:Personal ending');
expectPieces('ἧκα|ἵημι|AAI','ἧ:Augment + Verb stem | κ:Aorist marker | α:Tense vowel + Personal ending');
expectPieces('ἔγνων|γιγνώσκω|AAI','ἔ:Augment | γνω:Aorist stem | ν:Personal ending');
expectPieces('βαλῶ|βάλλω|FAI','βαλ:Future stem | ῶ:Future marker + Thematic vowel + Personal ending');
expectPieces('ᾔειν|εἶμι|IAI|1S','ᾔ:Augment + Present stem | ει:Tense vowel | ν:Personal ending');
// Present and imperfect passives share the middle's pieces.
assert.deepEqual(segments['λύομαι|λύω|PPI'],segments['λύομαι|λύω|PMI']);
console.log('Hand-checked segmentations passed.');

// 2. Every segmentation spells its word, and every key belongs to an analysis.
const byKey=new Map(paradigms.map(a=>[segmentKey(a),a]));
const RANK={'Prefix':0,'Augment':1,'Reduplication':2,'Present reduplication':2,'Present stem':3,'Future stem':3,'Aorist stem':3,'Perfect stem':3,'Verb stem':3,'Future marker':4,'Aorist marker':4,'Perfect marker':4,'Passive marker':4,'Thematic vowel':5,'Tense vowel':5,'Subjunctive vowel':5,'Optative marker':5,'Participle marker':6,'Personal ending':7,'Infinitive ending':7,'Nominal ending':7,'Movable ν':8};
for(const [key,pieces] of Object.entries(segments)){
 const a=byKey.get(key.split('|').slice(0,3).join('|'));assert(a,`segmentation without an analysis: ${key}`);
 assert.equal(pieces.map(p=>p[0]).join('').normalize('NFC'),exact(a.word).normalize('NFC'),key);
 let previous=-1;
 for(const piece of pieces){
  assert(piece[0].length>0,key);
  const ranks=pieceRoles(piece).map(role=>{assert(role in RANK,`unknown role ${role} in ${key}`);return RANK[role]});
  // 3. Pieces follow the fixed order, within a fused piece and across pieces.
  for(let i=1;i<ranks.length;i++)assert(ranks[i-1]<ranks[i],`roles out of order inside a piece: ${key}`);
  assert(previous<=ranks[0],`pieces out of order: ${key} ${show(pieces)}`);
  previous=ranks.at(-1);
 }
 // An ending, alone or fused, closes every form.
 const body=pieces.filter(p=>p[1]!=='Movable ν');
 assert(pieces.length-body.length<=1&&(body.length===pieces.length||pieces.at(-1)[1]==='Movable ν'),`misplaced movable ν: ${key}`);
 // Every form closes with an ending, except bare-stem forms of -μι verbs (ἔστη, ἵστη, ἐδίδου).
 const bare=pieceRoles(body.at(-1)).every(role=>RANK[role]<=3)&&['Indicative','Imperative'].includes(a.mood);
 assert(bare||pieceRoles(body.at(-1)).some(role=>RANK[role]===7),`no ending: ${key}`);
 if(pieces.some(p=>pieceRoles(p).includes('Present reduplication')))assert(['Present','Imperfect'].includes(a.tense),key);
 // Augments belong only to past indicatives.
 if(pieces.some(p=>pieceRoles(p).includes('Augment')))assert(a.mood==='Indicative'&&['Imperfect','Aorist','Pluperfect'].includes(a.tense),key);
 // Every pluperfect and every regular imperfect or aorist indicative shows where its augment is, or that it has none.
 if(pieces.some(p=>pieceRoles(p).includes('Passive marker')))assert(a.voice==='Passive'&&['Aorist','Future'].includes(a.tense),key);
 if(pieces.some(p=>pieceRoles(p).includes('Reduplication')))assert(['Perfect','Pluperfect'].includes(a.tense),key);
}
console.log('Segment spelling and order checks passed.');

// 4. Coverage is reported, and may only grow.
const covered=paradigms.filter(a=>segmentsFor(a,segments)).length;
const generated=paradigms.filter(a=>a.source==='generated');
const generatedCovered=generated.filter(a=>segmentsFor(a,segments)).length;
console.log(`Segmented ${covered} of ${paradigms.length} analyses (${generatedCovered} of ${generated.length} generated).`);
assert(generatedCovered/generated.length>=0.97,'generated coverage fell below 97%');
assert.equal(covered,paradigms.length,'every analysis should have a segmentation');
// The two model verbs are covered almost completely.
for(const lemma of ['λύω','παύω']){const all=paradigms.filter(a=>a.lemma===lemma),done=all.filter(a=>segmentsFor(a,segments));assert(done.length/all.length>=0.97,`${lemma}: only ${done.length} of ${all.length} forms are cut`)}

// 5. Curated training pieces never cut a word where the segmentation does not.
const WORDS={present:'P',imperfect:'I',future:'F',aorist:'A',perfect:'X',pluperfect:'Y',active:'A',middle:'M',passive:'P',indicative:'I',subjunctive:'S',optative:'O',imperative:'D',infinitive:'N',participle:'P'};
const cuts=texts=>{const out=new Set();let n=0;for(const t of texts.slice(0,-1)){n+=[...t.normalize('NFD').replace(/\p{M}/gu,'')].length;out.add(n)}return out};
let compared=0;
for(const example of trainingExamples){
 const [lemma,description]=example.parse.split(' · ');
 const codes=description.split(' ').map(w=>WORDS[w]).filter(Boolean);if(codes.length!==3)continue;
 const pieces=segments[`${example.word}|${lemma}|${codes.join('')}`];if(!pieces)continue;
 const mine=cuts(pieces.map(p=>p[0]));
 for(const cut of cuts(example.pieces.map(p=>p[0])))assert(mine.has(cut),`training example ${example.word} cuts at ${cut}; segmentation is ${show(pieces)}`);
 compared++;
}
console.log(`Training examples agree with segmentations (${compared} compared).`);
assert(compared>=10,'too few training examples have a segmentation to compare');
