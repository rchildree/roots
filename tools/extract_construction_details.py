#!/usr/bin/env python3
"""Retain source-generator evidence for existing analyses.

Generated records and fixture records are both looked up; `recordSource` says
which. A fixture record gets a derivation only when the generator reproduces it.

These are raw derivations, not checked student-facing segment boundaries.
Requires PyYAML and greek-accentuation, as does build_paradigms.py.
"""
import json
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'data/greek-inflexion'))
from greek_inflexion import GreekInflexion

path = ROOT / 'data/greek-inflexion'
generators = [(name, GreekInflexion(str(path/'stemming.yaml'), str(lexicon))) for name, lexicon in [
    ('morphgnt', path/'morphgnt_lexicon.yaml'),
    ('manual-present', ROOT/'data/manual_present_stems.yaml'),
    ('manual-middle', ROOT/'data/manual_middle_stems.yaml'),
    ('manual-principal-parts', ROOT/'data/manual_principal_part_stems.yaml'),
]]
source = (ROOT/'dist/paradigms.js').read_text(encoding='utf-8').split('export const paradigms = ', 1)[1].strip().removesuffix(';')
records = json.loads(source)
# Must match GENERATOR_TAGS in build_paradigms.py.
GENERATOR_TAGS = {'AAI.3S': {'final-nu-aai.3s'}}
ALTERNATIVES = {'alt-aao-1p-only', 'alt-aao-pl', 'alt-apo-pl', 'alt-xao-pl', 'alt-mi-opt', 'alt-eimi-opt',
                'alt-eimi-imp', 'extra-eimi-pad.3p', 'fpi.2s-ει', 'sigma-loss-imi.2s', 'sigma-loss-pmd.2s',
                'oida-yai3p-variant', 'alt-εἶμι-pao.1s', 'final-nu-aai.3s'}
TENSE = {'Present':'P', 'Imperfect':'I', 'Future':'F', 'Aorist':'A', 'Perfect':'X', 'Pluperfect':'Y'}
VOICE = {'Active':'A', 'Middle':'M', 'Passive':'P'}
MOOD = {'Indicative':'I', 'Subjunctive':'S', 'Optative':'O', 'Imperative':'D', 'Infinitive':'N', 'Participle':'P'}
CASE = {'Nominative':'N', 'Genitive':'G', 'Dative':'D', 'Accusative':'A', 'Vocative':'V'}
NUMBER = {'Singular':'S', 'Plural':'P'}
GENDER = {'Masculine':'M', 'Feminine':'F', 'Neuter':'N'}
def canon(text):
    return unicodedata.normalize('NFC', ''.join(c for c in unicodedata.normalize('NFD', text) if c not in '\u0304\u0306'))
def variants(form):
    """Spellings of a generator form with and without movable nu."""
    if '(ν)' in form:
        return {canon(form.replace('(ν)', '')), canon(form.replace('(ν)', 'ν'))}
    return {canon(form)}
def slot(record):
    s = TENSE[record['tense']] + VOICE[record['voice']] + MOOD[record['mood']]
    if record['mood'] == 'Participle':
        return s + '.' + CASE[record['case']] + NUMBER[record['number']] + GENDER[record['gender']]
    if record['mood'] != 'Infinitive':
        p, n = record['person'].split()
        return s + '.' + p[0] + ('S' if n == 'singular' else 'P')
    return s

out = []
cache = {}
for record in records:
    word, lemma, code = record['word'], record['lemma'], slot(record)
    candidates = []
    for name, generator in generators:
        key = (name, lemma, code)
        if key not in cache:
            try:
                cache[key] = dict(generator.generate(lemma, code, tags=GENERATOR_TAGS.get(code)))
                # Attic alternatives the generator gives only on request (λυθείημεν, λυθήσει, ἐδύνω).
                for form, details in generator.generate(lemma, code, tags=ALTERNATIVES).items():
                    cache[key].setdefault(form, details)
            except (KeyError, ValueError, TypeError):
                cache[key] = {}
        for form, details in cache[key].items():
            if canon(word) not in variants(form):
                continue
            for detail in details:
                if 'stemming' not in detail:
                    continue
                d = detail['stemming']
                candidates.append({'source':name, 'stem':detail['stem'], 'base':d['base'],
                                   'ending':d['ending'], 'rule':str(d['rule']),
                                   'unaccentedForm':detail.get('original_form'),
                                   'accentNotes':detail.get('accent_notes')})
    if candidates:
        out.append({'word':word, 'lemma':lemma, 'slot':code,
                    'recordSource':record.get('source', 'fixture'),
                    'derivations':candidates, 'reviewStatus':'unreviewed'})
(ROOT/'data/generated-constructions.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
for source in ('generated', 'fixture'):
    total = sum(r.get('source', 'fixture') == source for r in records)
    kept = sum(o['recordSource'] == source for o in out)
    print(f'Retained unreviewed generator derivations for {kept} of {total} {source} analyses.')
