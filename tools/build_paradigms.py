#!/usr/bin/env python3
"""Import Ancient Greek paradigms into Roots.

Requires PyYAML. Source test fixtures and their MIT license are in data/.
Only explicit source forms and matching vocabulary entries are included.
"""
import csv, json, re, unicodedata, sys
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parent.parent

def canon(s):
    return unicodedata.normalize('NFC',''.join(c for c in unicodedata.normalize('NFD',s) if c not in '\u0304\u0306'))

def variants(value):
    for item in value.split('/'):
        if '(ν)' in item:
            yield canon(item.replace('(ν)',''))
            yield canon(item.replace('(ν)','ν'))
        elif '(' not in item and ')' not in item:
            yield canon(item)

TENSE={'P':'Present','I':'Imperfect','F':'Future','A':'Aorist','X':'Perfect','Y':'Pluperfect'}
VOICE={'A':'Active','M':'Middle','P':'Passive'}
MOOD={'I':'Indicative','S':'Subjunctive','O':'Optative','D':'Imperative'}

def min_unit(code, voice):
    t,_,m=code
    if m=='N': base=16 if t=='F' else 3 if t=='X' else 2
    elif m=='P': base=8
    elif m=='D': base=11
    elif m=='I': base=3 if t in 'XY' else 2
    elif m in 'SO': base=3 if t in 'PA' else 16 if t=='F' and m=='O' else 11
    else:return 99
    if voice=='Passive': base=max(base,5)
    if voice=='Middle': base=max(base,7)
    return base

rows=list(csv.DictReader((ROOT/'data/hansen-quinn-vocabulary.csv').open(encoding='utf-8-sig',newline='')))
vocab={canon(row['PRINCIPAL PARTS'].split()[0]):row for row in rows}
records={}
for path in sorted((ROOT/'data/greek-inflexion').glob('*_test.yaml')):
    for entry in yaml.safe_load(path.read_text()):
        lemma=canon(str(entry.get('lemma','')))
        if lemma not in vocab:continue
        row=vocab[lemma]; vunit=int(row['FIRST APPEARANCE IN SELECTION'])
        for code,value in entry.items():
            if not isinstance(code,str) or not re.fullmatch(r'[PIFAXY][AMP][ISOD]\.[123][SP]',code):continue
            tense,voice,mood=code[:3]; person=code[4]+('st' if code[4]=='1' else 'nd' if code[4]=='2' else 'rd')+(' singular' if code[5]=='S' else ' plural')
            if not isinstance(value,str):continue
            for word in variants(value):
                # In non-aorist systems the middle and passive share forms.
                voices=[VOICE[voice]]
                if voice=='M' and tense in 'PIX Y'.replace(' ',''):voices.append('Passive')
                for v in voices:
                    u=max(vunit,min_unit(code[:3],v))
                    if u>20:continue
                    r={'word':word,'lemma':lemma,'tense':TENSE[tense],'voice':v,'mood':MOOD[mood],'person':person,'unit':u}
                    key=(word,lemma,TENSE[tense],v,MOOD[mood],person)
                    if key not in records or u<records[key]['unit']:records[key]=r
# Import infinitives and participles explicitly present in the same fixtures.
CASE={'N':'Nominative','G':'Genitive','D':'Dative','A':'Accusative','V':'Vocative'}
NUMBER={'S':'Singular','P':'Plural'}
GENDER={'M':'Masculine','F':'Feminine','N':'Neuter'}
athematic={'δίδωμι','τίθημι','ἵστημι','ἵημι','δείκνυμι'}
for path in sorted((ROOT/'data/greek-inflexion').glob('*_test.yaml')):
    for entry in yaml.safe_load(path.read_text()):
        lemma=canon(str(entry.get('lemma','')))
        if lemma not in vocab:continue
        vunit=int(vocab[lemma]['FIRST APPEARANCE IN SELECTION'])
        for code,value in entry.items():
            if not isinstance(code,str) or not isinstance(value,str):continue
            if not re.fullmatch(r'[PIFAXY][AMP]N|[PIFAXY][AMP]P\.[NGDAV][SP][MFN]',code):continue
            tense,voice,kind=code[:3]
            for word in variants(value):
                voices=[VOICE[voice]]
                if voice=='M' and tense in 'PXY':voices.append('Passive')
                for v in voices:
                    u=max(vunit,min_unit(code[:3],v),14 if kind=='P' and lemma in athematic else 0)
                    if u>20:continue
                    kind_name='Infinitive' if kind=='N' else 'Participle'
                    r={'word':word,'lemma':lemma,'tense':TENSE[tense],'voice':v,'mood':kind_name,'kind':kind_name,'person':'','unit':u}
                    if kind=='P':r.update({'case':CASE[code[4]],'number':NUMBER[code[5]],'gender':GENDER[code[6]]})
                    key=(word,lemma,TENSE[tense],v,kind_name,r.get('case',''),r.get('number',''),r.get('gender',''))
                    if key not in records or u<records[key]['unit']:records[key]=r

# Supplement the checked fixtures with generated, regular thematic active forms.
# Require the generator's principal-part anchors to agree with the supplied list.
# Generated records are marked so they can be reviewed separately.
sys.path.insert(0,str(ROOT/'data/greek-inflexion'))
from greek_inflexion import GreekInflexion
stem_path=ROOT/'data/greek-inflexion'
generator=GreekInflexion(str(stem_path/'stemming.yaml'),str(stem_path/'morphgnt_lexicon.yaml'))
lexicon=yaml.safe_load((stem_path/'morphgnt_lexicon.yaml').read_text())
# The generator only produces the aorist third singular, with its movable nu,
# when this tag is requested.
GENERATOR_TAGS={'AAI.3S':{'final-nu-aai.3s'}}
existing_slots={(r['lemma'],r['tense'],r['voice'],r['mood'],r['person']) for r in records.values() if r.get('kind','Finite')=='Finite'}
for raw,info in lexicon.items():
    lemma=canon(raw)
    if lemma not in vocab or not lemma.endswith('ω'):continue
    row=vocab[lemma];vunit=int(row['FIRST APPEARANCE IN SELECTION'])
    stem=info.get('stems',{}).get('1-','')
    base=''.join(c for c in unicodedata.normalize('NFD',str(stem)) if not unicodedata.combining(c))
    if not base or '{' in base:continue
    principal=row['PRINCIPAL PARTS'].split()
    generated_present={canon(x) for x in generator.generate(raw,'PAI.1S')}
    lemma_bare=''.join(c for c in unicodedata.normalize('NFD',lemma) if not unicodedata.combining(c))
    if base[-1] in 'αεο':
        # Contract verbs list their uncontracted dictionary form; the generated
        # first person is contracted. Check the lexical stem instead.
        if not generated_present or base!=lemma_bare[:-1]:continue
    elif canon(lemma) not in generated_present:continue
    def single_plain(*names,allow_second=False):
        stems=info.get('stems',{})
        values=[stems.get(name) for name in names]
        if not all(isinstance(value,str) and value and '/' not in value for value in values):return False
        stripped=[value.replace('{2nd}','') if allow_second else value for value in values]
        if any('{' in value or '}' in value for value in stripped):return False
        if allow_second and any('{2nd}' in value for value in values) and not all('{2nd}' in value for value in values):return False
        return True
    # A matching augmented principal part is not enough when the unaugmented
    # stem has multiple alternatives. Such branches need independent review.
    anchors={'P':single_plain('1-'),'I':single_plain('1+')}
    for tense,index,names in [('F',1,('2-',)),('A',2,('3-','3+')),('X',3,('4-','4+'))]:
        key=tense+'AI.1S'
        anchors[tense]=single_plain(*names,allow_second=tense=='A') and len(principal)>index and canon(principal[index]) in {canon(x) for x in generator.generate(raw,key)}
    for tense,mood in [('P','I'),('I','I'),('F','I'),('A','I'),('X','I'),('P','S'),('P','O'),('A','S'),('A','O')]:
        if not anchors[tense]:continue
        code=tense+'A'+mood; unit=max(vunit,min_unit(code,'Active'))
        for pn in ['1S','2S','3S','1P','2P','3P']:
            person=pn[0]+('st' if pn[0]=='1' else 'nd' if pn[0]=='2' else 'rd')+(' singular' if pn[1]=='S' else ' plural')
            slot=(lemma,TENSE[tense],'Active',MOOD[mood],person)
            if slot in existing_slots:continue
            for value,details in generator.generate(raw,code+'.'+pn,tags=GENERATOR_TAGS.get(code+'.'+pn)).items():
                # A thematic verb's athematic by-forms are later Greek (εἴχοσαν for εἶχον).
                if all('{athematic}' in str(d.get('stem','')) for d in details):continue
                for word in variants(value):
                    key=(word,lemma,TENSE[tense],'Active',MOOD[mood],person)
                    records.setdefault(key,{'word':word,'lemma':lemma,'tense':TENSE[tense],'voice':'Active','mood':MOOD[mood],'person':person,'unit':unit,'source':'generated'})


    # Supplement active infinitives and participles where the principal-part
    # anchor matches. Existing fixture slots retain precedence.
    for tense in ['P','A','X']:
        if not anchors[tense]:continue
        for kind in ['N','P']:
            code=tense+'A'+kind
            unit=max(vunit,min_unit(code,'Active'))
            kind_name='Infinitive' if kind=='N' else 'Participle'
            slots=[None] if kind=='N' else [c+n+g for c in 'NGDAV' for n in 'SP' for g in 'MFN']
            for cn in slots:
                generated_key=code if cn is None else code+'.'+cn
                case=CASE[cn[0]] if cn else '';number=NUMBER[cn[1]] if cn else '';gender=GENDER[cn[2]] if cn else ''
                if any(r['lemma']==lemma and r['tense']==TENSE[tense] and r['voice']=='Active' and r['mood']==kind_name and r.get('case','')==case and r.get('number','')==number and r.get('gender','')==gender for r in records.values()):continue
                for value in generator.generate(raw,generated_key):
                    for word in variants(value):
                        key=(word,lemma,TENSE[tense],'Active',kind_name,case,number,gender)
                        record={'word':word,'lemma':lemma,'tense':TENSE[tense],'voice':'Active','mood':kind_name,'kind':kind_name,'person':'','unit':unit,'source':'generated'}
                        if cn:record.update({'case':case,'number':number,'gender':gender})
                        records.setdefault(key,record)


# Additional ordinary present stems, explicitly transcribed from the supplied
# first principal parts. Only the present system is generated from this file.
extra_path=ROOT/'data/manual_present_stems.yaml'
extra=yaml.safe_load(extra_path.read_text())
extra_generator=GreekInflexion(str(stem_path/'stemming.yaml'),str(extra_path))
for raw in extra:
    lemma=canon(raw)
    if lemma not in vocab:continue
    row=vocab[lemma];vunit=int(row['FIRST APPEARANCE IN SELECTION'])
    for code in ['PAI','PAS','PAO','PAN','PAP']:
        unit=max(vunit,min_unit(code,'Active'))
        if code[-1]=='N':slots=[None]
        elif code[-1]=='P':slots=[c+n+g for c in 'NGDAV' for n in 'SP' for g in 'MFN']
        else:slots=['1S','2S','3S','1P','2P','3P']
        for slot in slots:
            keycode=code if slot is None else code+'.'+slot
            for value in extra_generator.generate(raw,keycode):
                for word in variants(value):
                    if code[-1] in 'ISO':
                        person=slot[0]+('st' if slot[0]=='1' else 'nd' if slot[0]=='2' else 'rd')+(' singular' if slot[1]=='S' else ' plural')
                        record={'word':word,'lemma':lemma,'tense':'Present','voice':'Active','mood':MOOD[code[-1]],'person':person,'unit':unit,'source':'generated'}
                        key=(word,lemma,'Present','Active',MOOD[code[-1]],person)
                    else:
                        kind='Infinitive' if slot is None else 'Participle'
                        case=CASE[slot[0]] if slot else '';number=NUMBER[slot[1]] if slot else '';gender=GENDER[slot[2]] if slot else ''
                        record={'word':word,'lemma':lemma,'tense':'Present','voice':'Active','mood':kind,'kind':kind,'person':'','unit':unit,'source':'generated'}
                        if slot:record.update({'case':case,'number':number,'gender':gender})
                        key=(word,lemma,'Present','Active',kind,case,number,gender)
                    records.setdefault(key,record)


# A small reviewed set of thematic middle-deponent present stems. Their
# contracted/noncontracted present anchors are checked before generation.
middle_path=ROOT/'data/manual_middle_stems.yaml'
manual_middle=yaml.safe_load(middle_path.read_text())
manual_middle_generator=GreekInflexion(str(stem_path/'stemming.yaml'),str(middle_path))
middle_expected={'ἡγέομαι':'ἡγοῦμαι','ἀφικνέομαι':'ἀφικνοῦμαι','μηχανάομαι':'μηχανῶμαι'}
for raw in ['δέχομαι','βούλομαι','μάχομαι','πυνθάνομαι','ἡγέομαι','κεῖμαι',*manual_middle]:
    lemma=canon(raw);middle_generator=manual_middle_generator if raw in manual_middle else generator
    middle_lexicon=manual_middle if raw in manual_middle else lexicon
    if lemma not in vocab or raw not in middle_lexicon:continue
    info=middle_lexicon[raw];stem=info.get('stems',{}).get('1-','')
    if not isinstance(stem,str) or not stem or '/' in stem or ('{' in stem and raw!='κεῖμαι'):continue
    anchors={canon(x) for x in middle_generator.generate(raw,'PMI.1S')}
    if canon(middle_expected.get(lemma,lemma)) not in anchors:continue
    vunit=int(vocab[lemma]['FIRST APPEARANCE IN SELECTION'])
    for code in (['PMI','PMD','PMN','PMP'] if raw=='κεῖμαι' else ['PMI','PMS','PMO','PMD','PMN','PMP']):
        kind=code[-1];unit=max(vunit,min_unit(code,'Middle'))
        if kind=='N':slots=[None]
        elif kind=='P':slots=[c+n+g for c in 'NGDAV' for n in 'SP' for g in 'MFN']
        elif kind=='D':slots=['2S','3S','2P','3P']
        else:slots=['1S','2S','3S','1P','2P','3P']
        for slot in slots:
            keycode=code if slot is None else code+'.'+slot
            for value in middle_generator.generate(raw,keycode):
                for word in variants(value):
                    if not re.fullmatch(r'[\u0370-\u03ff\u1f00-\u1fff\u0300-\u036f]+',word):continue
                    if kind in 'ISOD':
                        person=slot[0]+('st' if slot[0]=='1' else 'nd' if slot[0]=='2' else 'rd')+(' singular' if slot[1]=='S' else ' plural')
                        record={'word':word,'lemma':lemma,'tense':'Present','voice':'Middle','mood':MOOD[kind],'person':person,'unit':unit,'source':'generated'}
                        key=(word,lemma,'Present','Middle',MOOD[kind],person)
                    else:
                        form_kind='Infinitive' if slot is None else 'Participle'
                        case=CASE[slot[0]] if slot else '';number=NUMBER[slot[1]] if slot else '';gender=GENDER[slot[2]] if slot else ''
                        record={'word':word,'lemma':lemma,'tense':'Present','voice':'Middle','mood':form_kind,'kind':form_kind,'person':'','unit':unit,'source':'generated'}
                        if slot:record.update({'case':case,'number':number,'gender':gender})
                        key=(word,lemma,'Present','Middle',form_kind,case,number,gender)
                    records.setdefault(key,record)

result=sorted(records.values(),key=lambda r:(r['unit'],r['lemma'],r['word'],r['tense'],r['voice'],r['mood'],r['person']))
(ROOT/'dist/paradigms.js').write_text('// Generated by tools/build_paradigms.py; see data/greek-inflexion/LICENSE.\nexport const paradigms = '+json.dumps(result,ensure_ascii=False,separators=(',',':'))+';\n')
print(f'{len(result)} analyses, {len({r["word"] for r in result})} forms, {len({r["lemma"] for r in result})} verbs')
