// Candidate-based morphology. Imported paradigms are a documented subset.
export const FIELDS_BY_KIND={Finite:['person','tense','voice','mood'],Infinitive:['tense','voice'],Participle:['tense','voice','case','number','gender']};
export const FIELDS=FIELDS_BY_KIND.Finite;
export function kindOf(a){return a.kind||'Finite'}
export function fold(s){return s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase().replace(/ς/g,'σ')}
export function exact(s){return s.normalize('NFD').replace(/[\u0304\u0306]/g,'').normalize('NFC')}
export function available(analyses,unit,kind){return analyses.filter(a=>a.unit<=unit&&(!kind||kindOf(a)===kind))}
export function distinct(values){return [...new Set(values)]}
export function formTypes(analyses){return distinct(analyses.map(a=>kindOf(a)==='Finite'?(a.mood==='Imperative'?'Imperative':'Finite'):kindOf(a)))}
// Infer a type only from the meaning of explicitly named components. Ambiguous
// personal endings remain ambiguous when both finite and imperative forms exist.
export function inferFormChoice(observations,analyses,unit){
 let types=['Finite','Infinitive','Imperative','Participle'];
 for(const o of observations){let permitted=null;if(o.category==='Augment')permitted=['Finite'];if(o.category==='Personal ending')permitted=['Finite','Imperative'];if(o.category==='Infinitive ending')permitted=['Infinitive'];if(o.category==='Nominal ending')permitted=['Participle'];if(o.category==='Tense / mood marker'&&fold(o.text)==='οι')permitted=['Finite'];if(permitted)types=types.filter(t=>permitted.includes(t))}
 types=types.filter(t=>{const kind=t==='Imperative'?'Finite':t,pool=available(analyses,unit,kind);return t==='Imperative'?pool.some(a=>a.mood==='Imperative'):t==='Finite'?pool.some(a=>a.mood!=='Imperative'):pool.length>0});
 return observations.length&&types.length===1?types[0]:'';
}
export function analysesForWord(analyses,word,unit,kind){return available(analyses,unit,kind).filter(a=>exact(a.word)===exact(word))}
// Observations are hypotheses. Ambiguous or unannotated components do not narrow.
export function supports(a,o){
 const token=fold(o.text),word=fold(a.word);if(!token)return false;
 switch(o.category){
  case 'Augment':return kindOf(a)==='Finite'&&a.mood==='Indicative'&&['Imperfect','Aorist','Pluperfect'].includes(a.tense)&&word.includes(token);
  case 'Reduplication':return true; // Reduplication can belong to more than one system.
  case 'Present stem':return ['Present','Imperfect'].includes(a.tense)&&word.includes(token);
  case 'Future stem':return a.tense==='Future'&&word.includes(token);
  case 'Aorist stem':return a.tense==='Aorist'&&word.includes(token);
  case 'Perfect stem':return ['Perfect','Pluperfect'].includes(a.tense)&&word.includes(token);
  case 'Personal ending':return kindOf(a)==='Finite'&&word.endsWith(token);
  case 'Nominal ending':return kindOf(a)==='Participle'&&word.endsWith(token);
  case 'Infinitive ending':return kindOf(a)==='Infinitive'&&word.endsWith(token);
  case 'Tense / mood marker':case 'Tense marker':return token==='οι'?kindOf(a)==='Finite'&&a.mood==='Optative'&&word.includes(token):true;
  case 'Thematic vowel':return true;
  default:return true;
 }
}
export function filterByObservations(analyses,observations){return analyses.filter(a=>observations.every(o=>supports(a,o)))}
export function possibilities(analyses,kind='Finite'){return Object.fromEntries(FIELDS_BY_KIND[kind].map(key=>[key,distinct(analyses.map(a=>a[key]).filter(Boolean))]))}
export function grammaticalTuples(analyses,kind='Finite'){return distinct(analyses.map(a=>FIELDS_BY_KIND[kind].map(k=>a[k]).join('|')))}
export function parseMatches(a,answer){return a.lemma===answer.lemma&&FIELDS_BY_KIND[kindOf(a)].every(k=>a[k]===answer[k])}
export function answerIsValid(analyses,word,unit,answer,kind='Finite'){return analysesForWord(analyses,word,unit,kind).some(a=>parseMatches(a,answer))}
// Structural checks need only where each piece was selected, not morphology
// data: pieces cannot share letters, they occur in a fixed order, and an
// ending closes the word. They do not show that a piece is correctly labeled.
export const PIECE_ORDER={'Augment':0,'Reduplication':1,'Present stem':2,'Future stem':2,'Aorist stem':2,'Perfect stem':2,'Tense / mood marker':3,'Tense marker':3,'Thematic vowel':4,'Personal ending':5,'Infinitive ending':5,'Nominal ending':5};
const ENDINGS=['Personal ending','Infinitive ending','Nominal ending'];
const positioned=o=>Number.isInteger(o.start)&&Number.isInteger(o.end);
const named=o=>`${o.category.toLowerCase()} “${o.text}”`;
export function checkStructure(observations,wordLength){
 const problems=[];
 observations.forEach((a,i)=>{
  if(!positioned(a))return;
  if(ENDINGS.includes(a.category)&&Number.isInteger(wordLength)&&a.end!==wordLength-1)problems.push({type:'not-final',indexes:[i],message:`An ending is the last piece of the word, but the ${named(a)} stops before the final letter.`});
  observations.forEach((b,j)=>{
   if(j<=i||!positioned(b))return;
   if(a.start<=b.end&&b.start<=a.end){problems.push({type:'overlap',indexes:[i,j],message:`The ${named(a)} and the ${named(b)} share letters. Each letter belongs to one piece.`});return}
   const ra=PIECE_ORDER[a.category],rb=PIECE_ORDER[b.category];
   if(ra===undefined||rb===undefined||ra===rb)return;
   const [first,second]=ra<rb?[a,b]:[b,a];
   if(first.start>second.start)problems.push({type:'order',indexes:[i,j],message:`The ${first.category.toLowerCase()} comes before the ${second.category.toLowerCase()} in a verb, but “${first.text}” was selected after “${second.text}”.`});
  });
 });
 return problems;
}
// Observations not involved in any structural problem; only these should narrow.
export function structurallySound(observations,wordLength){const flagged=new Set(checkStructure(observations,wordLength).flatMap(p=>p.indexes));return observations.filter((_,i)=>!flagged.has(i))}
// Word-piece segmentations (dist/segments.js) are keyed by spelling, verb and
// tense-voice-mood. A piece is [text, role]; a fused piece joins roles with ' + '.
const TENSE_CODE={Present:'P',Imperfect:'I',Future:'F',Aorist:'A',Perfect:'X',Pluperfect:'Y'};
const MOOD_CODE={Indicative:'I',Subjunctive:'S',Optative:'O',Imperative:'D',Infinitive:'N',Participle:'P'};
export function segmentKey(a){return `${a.word}|${a.lemma}|${TENSE_CODE[a.tense]}${a.voice[0]}${MOOD_CODE[a.mood]}`}
// A few spellings are cut differently by person (ᾔειν); those keys end in a person code such as 3S.
const personCode=a=>a.person?a.person[0]+(a.person.endsWith('singular')?'S':'P'):'';
export function segmentsFor(a,segments){const key=segmentKey(a);return segments[key]||segments[`${key}|${personCode(a)}`]||null}
export function pieceRoles(piece){return piece[1].split(' + ')}

// ---- Checking a labelled selection against word pieces ----
// A learner's label is right when its letters are exactly one of the spans
// that label may cover in some analysis of the form. Several spans can be
// right: the personal ending of ἦγον is ν, or ον as textbooks print it; the
// future stem of παύσομεν is παύσ, or παύ with σ as its marker.
export const CATEGORIES=['Augment','Reduplication','Present stem','Future stem','Aorist stem','Perfect stem','Tense / mood marker','Thematic vowel','Personal ending','Infinitive ending','Nominal ending'];
const STEM_ROLES=['Present stem','Future stem','Aorist stem','Perfect stem','Verb stem'];
const TENSE_MARKERS=['Future marker','Aorist marker','Perfect marker'];
const MARKER_ROLES=[...TENSE_MARKERS,'Passive marker'];
const VOWEL_ROLES=['Thematic vowel','Tense vowel','Subjunctive vowel'];
const ENDING_ROLES=['Personal ending','Infinitive ending','Nominal ending'];
const SYSTEM_STEM={Present:'Present stem',Imperfect:'Present stem',Future:'Future stem',Aorist:'Aorist stem',Perfect:'Perfect stem',Pluperfect:'Perfect stem'};
const ENDING_OF_KIND={Finite:'Personal ending',Infinitive:'Infinitive ending',Participle:'Nominal ending'};
const segmenter=new Intl.Segmenter('el',{granularity:'grapheme'});
const graphemeCount=text=>[...segmenter.segment(text)].length;
const layouts=new WeakMap();
const onlyVowels=text=>/^[αεηιουω]+$/.test(fold(text));
// Pieces with their grapheme positions in the word.
export function layout(pieces){if(!layouts.has(pieces))layouts.set(pieces,measure(pieces));return layouts.get(pieces)}
function measure(pieces){let at=0;return pieces.map(([text,role])=>{const n=graphemeCount(text),piece={start:at,end:at+n-1,text,roles:role.split(' + ')};at+=n;return piece})}
export function acceptableSpans(a,pieces,category){
 const L=layout(pieces),has=(p,roles)=>p.roles.some(r=>roles.includes(r)),out=[];
 const span=(i,j)=>out.push({start:L[i].start,end:L[j].end,text:L.slice(i,j+1).map(p=>p.text).join('')});
 switch(category){
  case 'Augment':L.forEach((p,i)=>{if(p.roles.includes(category))span(i,i)});break;
  // Perfect reduplication (λε-λυκα) and present reduplication (δί-δωμι) share the one label.
  case 'Reduplication':L.forEach((p,i)=>{if(has(p,['Reduplication','Present reduplication']))span(i,i)});break;
  case 'Present stem':case 'Future stem':case 'Aorist stem':case 'Perfect stem':{
   if(SYSTEM_STEM[a.tense]!==category)break;
   const first=L.findIndex(p=>has(p,STEM_ROLES));if(first<0)break;
   // The stem runs at least to its last wholly-stem piece. It may also take
   // in a marker (παύ-σ), or a letter shared with what follows (πέμ-ψ, τιμ-ῶ).
   let whole=first;for(let i=first;i<L.length&&has(L[i],STEM_ROLES);i++)if(L[i].roles.every(r=>STEM_ROLES.includes(r)||r==='Augment'))whole=i;
   const ends=[whole];for(let j=whole+1;j<L.length&&(has(L[j],STEM_ROLES)||has(L[j],MARKER_ROLES))&&!has(L[j],ENDING_ROLES);j++)ends.push(j);
   // A prefix or reduplication directly before it may be counted in (ἀπο-θάν, πε-ποίη-κ).
   const starts=[first];for(let i=first-1;i>=0&&has(L[i],['Reduplication','Present reduplication','Prefix']);i--)starts.push(i);
   for(const s of starts)for(const e of ends)span(s,e);break}
  case 'Tense / mood marker':case 'Tense marker':L.forEach((p,i)=>{
   if(!has(p,[...MARKER_ROLES,'Optative marker','Subjunctive vowel','Participle marker'])||has(p,['Infinitive ending','Nominal ending']))return;
   if(has(p,['Personal ending'])&&!onlyVowels(p.text))return;
   span(i,i);
   // Markers side by side count together (θ-η, θ-η-σ).
   for(let j=i+1;j<L.length&&has(L[j],MARKER_ROLES)&&!has(L[j],ENDING_ROLES)&&has(p,MARKER_ROLES);j++)span(i,j);
   // First aorist and perfect: σ or κ together with the tense vowel (-σα-, -κα-).
   const next=L[i+1];if(has(p,MARKER_ROLES)&&next&&next.roles.includes('Tense vowel')&&onlyVowels(next.text))span(i,i+1)});break;
  case 'Thematic vowel':L.forEach((p,i)=>{if(has(p,VOWEL_ROLES)&&!has(p,['Infinitive ending','Nominal ending'])&&onlyVowels(p.text))span(i,i)});break;
  case 'Personal ending':case 'Infinitive ending':case 'Nominal ending':{
   if(ENDING_OF_KIND[kindOf(a)]!==category)break;
   let e=L.length-1;const movable=L[e].roles[0]==='Movable ν';if(movable)e--;
   if(e<0||!L[e].roles.includes(category))break;
   // The bare ending, or the ending with the vowel and marker before it, as
   // textbooks print endings (-ν or -ον, -μεν or -ομεν, -ες or -οντες).
   // The passive marker's vowel counts the same way (-ν or -ην).
   const joins=p=>(has(p,[...VOWEL_ROLES,'Optative marker','Participle marker'])||(p.roles.includes('Passive marker')&&onlyVowels(p.text)))&&!has(p,TENSE_MARKERS);
   const starts=[e];for(let i=e-1;i>=0&&joins(L[i]);i--)starts.push(i);
   for(const s of starts){span(s,e);if(movable)span(s,e+1)}break}
 }
 return out;
}
// Narrowing by pieces: the analysis has that kind of piece, spelled that way.
export function supportsByPieces(a,o,pieces){const token=fold(o.text);return !!token&&acceptableSpans(a,pieces,o.category).some(s=>fold(s.text)===token)}
// An analysis without pieces falls back to the older letter check, and must at least contain the letters.
export function filterByPieces(analyses,observations,segments){return analyses.filter(a=>{const pieces=segmentsFor(a,segments);return observations.every(o=>pieces?supportsByPieces(a,o,pieces):supports(a,o)&&fold(a.word).includes(fold(o.text)))})}
// Is this label true of these letters in this form? `analyses` are the
// analyses of the displayed spelling. Forms without pieces are 'unchecked'.
export function verifyObservation(o,analyses,segments){
 const checked=analyses.map(a=>[a,segmentsFor(a,segments)]).filter(x=>x[1]);
 if(!checked.length||!positioned(o))return {status:'unchecked',message:'Not checked: this form has no word-piece data yet.'};
 const same=s=>s.start===o.start&&s.end===o.end,overlaps=s=>s.start<=o.end&&o.start<=s.end,name=o.category.toLowerCase();
 let present=false,near=false,piece=false,movable=false;
 for(const [a,pieces] of checked){
  const spans=acceptableSpans(a,pieces,o.category);
  if(spans.some(same))return {status:'correct',message:''};
  if(spans.length)present=true;if(spans.some(overlaps))near=true;
  for(const p of layout(pieces))if(same(p)){piece=true;if(p.roles[0]==='Movable ν')movable=true}
  for(const c of CATEGORIES)if(c!==o.category&&acceptableSpans(a,pieces,c).some(same))piece=true;
 }
 // An analysis without pieces might still support the label: do not call it wrong.
 if(analyses.some(a=>!segmentsFor(a,segments)&&supports(a,o)))return {status:'unchecked',message:'Not checked: one analysis of this form has no word-piece data yet.'};
 if(movable)return {status:'movable',message:'This final ν is movable ν. It may be counted with the ending, but it is not a piece with a label of its own.'};
 if(near)return {status:'boundary',message:`There is a ${name} here, but it does not begin and end where you selected.`};
 if(piece)return {status:'label',message:present?`These letters are a piece of the word, but they are not the ${name}.`:`These letters are a piece of the word, but this form has no ${name}.`};
 if(present)return {status:'misplaced',message:`This form has a ${name}, but not in these letters.`};
 return {status:'absent',message:`This form has no ${name}, and these letters do not line up with a piece of the word.`};
}
export const isWrong=verdict=>!['correct','unchecked'].includes(verdict.status);
