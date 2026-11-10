import {paradigms} from '../paradigms.js?v=2';
import {vocabulary} from '../vocabulary.js?v=2';
// A curriculum pack provides its metadata, ordered units, vocabulary, and
// source-backed analyses with their first eligible unit.
export const textbook={
 id:'hansen-quinn',title:'Hansen & Quinn',subtitle:'Greek: An Intensive Course',
 units:Array.from({length:19},(_,i)=>({id:i+2,label:`Through Unit ${i+2}`})),
 vocabulary,analyses:paradigms
};
