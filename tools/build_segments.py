#!/usr/bin/env python3
"""Cut each analysed form into labelled word pieces.

Reads dist/paradigms.js and the generator derivations kept in
data/generated-constructions.json, and writes dist/segments.js. Standard
library only.

A derivation supplies the boundary between the tense stem and what follows,
and marks contraction. Everything else is decided here, by the conventions
below, and is UNREVIEWED: the output says how this script cuts a form, not
that a scholar has checked the cut.

  Prefix          a preverb (COMPOUNDS lists the compound verbs)
  Augment         syllabic ἐ-, or fused with the stem's first vowel (ἦ-γον)
  Reduplication   perfect reduplication (πε-ποίηκα)
  Present reduplication
                  δί-δωμι, τί-θημι, ἵ-στημι, ἵ-ημι
  Present stem / Aorist stem / Future stem / Perfect stem
                  a tense stem with no separable marker
  Verb stem       what is left of a tense stem once its marker is cut off
  Future marker / Aorist marker / Perfect marker
                  σ or κ; ψ and ξ are fused "Verb stem + marker" pieces
  Passive marker  θ and the vowel after it, as two pieces (ἐ-λύ-θ-η-ν), so
                  that a checker can accept λυθ- as the stem or θη as the marker
  Thematic vowel / Tense vowel / Subjunctive vowel / Optative marker
  Participle marker
  Personal ending / Infinitive ending / Nominal ending
  Movable ν       a final piece of its own, never part of an ending

Where vowel and ending are both visible they are cut apart (-ο-μεν, -ο-ν,
-ε-ς), so a checker can accept either the bare ending or vowel and ending
together, as textbooks print them. Where they are not (-ω, -ει, -εις, -ουσι)
the ending is one fused piece. Subjunctive -ῃ-ς and -ω-σι and perfect -α-σι
keep their plainly visible vowel apart.

A piece that does two jobs carries both roles joined by " + ". A form with no
separate ending fuses "Personal ending" into its last piece (λύ-ω).

-μι verbs: the stem vowel stays in the stem in whichever grade it shows
(δί-δω-μι, δί-δο-μεν, ἐ-δί-δου-ν, δι-δό-ναι); it is fused with what follows
only where the two have contracted (δι-δ-ῶ-μεν, ἐ-δί-δ-ου-ν, ἔ-θ-ου).

Participles: -ντ- is the marker. Where it has vanished before -ς, the vowel
lengthened in its place carries the marker and -ς is the ending (δι-δ-ού-ς,
λύ-σ-α-ς, λυ-θ-εί-ς); in the neuter, -ν is what is left of it (δι-δό-ν). A form with
no ending at all (ἔ-στη) simply ends with its stem. δείκ-νυ-μι is cut before
-νυ-, both pieces being present stem.

Forms outside the supported families and anything that fails a consistency
check are left out and counted in the report.
"""
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TENSE = {'Present': 'P', 'Imperfect': 'I', 'Future': 'F', 'Aorist': 'A', 'Perfect': 'X', 'Pluperfect': 'Y'}
MOOD = {'Indicative': 'I', 'Subjunctive': 'S', 'Optative': 'O', 'Imperative': 'D', 'Infinitive': 'N', 'Participle': 'P'}
CASE = {'Nominative': 'N', 'Genitive': 'G', 'Dative': 'D', 'Accusative': 'A', 'Vocative': 'V'}

SUPPORTED = {
    'PAI', 'IAI', 'FAI', 'AAI', 'XAI', 'PAS', 'AAS', 'PAO', 'AAO', 'FAO',
    'PMI', 'IMI', 'FMI', 'PMS', 'PMO', 'FMO', 'PMD',
    'PAN', 'FAN', 'AAN', 'XAN', 'PMN', 'FMN',
    'PAP', 'FAP', 'AAP', 'XAP', 'PMP', 'FMP',
    # imperatives, perfect subjunctive and optative, pluperfect
    'PAD', 'AAD', 'XAD', 'XAS', 'XAO', 'YAI', 'YMI',
    # aorist middle; perfect middle
    'AMI', 'AMS', 'AMO', 'AMD', 'AMN', 'AMP', 'XMI', 'XMD', 'XMN', 'XMP',
    # aorist and future passive
    'API', 'APS', 'APO', 'APD', 'APN', 'APP', 'FPI', 'FPO', 'FPN', 'FPP',
}

# Compound verbs: letters of the prefix before an unaugmented stem, and before
# an augment (elided, or restored from assimilation). Keys are bare letters.
COMPOUNDS = {
    'αποθνησκω': ('απο', 'απ'), 'αποκτεινω': ('απο', 'απ'), 'αποκρινω': ('απο', 'απ'),
    'αποδεχομαι': ('απο', 'απ'), 'αφικνεομαι': ('αφ', 'αφ'),
    'καταλυω': ('κατα', 'κατ'), 'παραγιγνομαι': ('παρα', 'παρ'), 'παραμενω': ('παρα', 'παρ'),
    'υπακουω': ('υπ', 'υπ'), 'υπομενω': ('υπο', 'υπ'),
    'διαφερω': ('δια', 'δι'), 'συμφερω': ('συμ', 'συν'), 'συμβουλευω': ('συμ', 'συν'),
    'αναβαινω': ('ανα', 'αν'), 'εκπιπτω': ('εκ', 'εξ'), 'επιβουλευω': ('επι', 'επ'),
    'επιδεικνυμι': ('επι', 'επ'), 'απολλυμι': ('απ', 'απ'),
}

# -μι verbs: reduplication that the general pattern (consonant, ε, same
# consonant) does not find, verbs with a κ-aorist, and presents in -νυ-.
PRESENT_REDUPLICATION = {'διδωμι': 'δι', 'τιθημι': 'τι', 'ιστημι': 'ι', 'ιημι': 'ι'}
PERFECT_REDUPLICATION = {'ιστημι': 'ε'}
KAPPA_AORIST = {'διδωμι', 'τιθημι', 'ιημι'}
NU_PRESENT = {'δεικνυμι', 'επιδεικνυμι'}
STEM_CLASSES = {'athematic', 'root'}

VOWELS = 'αεηιουω'
# Temporal augment: unaugmented and augmented spellings of a stem's first vowel.
LENGTHENED = {('ει', 'η'), ('α', 'η'), ('ε', 'η'), ('ο', 'ω'), ('αι', 'η'), ('ε', 'ει'), ('αυ', 'ηυ'), ('ευ', 'ηυ'), ('οι', 'ω')}
ASPIRATE_PAIRS = {('π', 'φ'), ('κ', 'χ'), ('τ', 'θ')}

# Endings are compared as bare letters, in which final ς is written σ.
ACTIVE_ENDINGS = {'', 'σ', 'μεν', 'τε', 'σι', 'ν', 'τω', 'ντων', 'τωσαν', 'σθα', 'μι', 'εν', 'ε', 'ασ', 'αν', 'σαν'}
# -θε, -θω, -θων, -θαι: -σθ- after a consonant stem loses its σ (πέπεμφθε)
MIDDLE_ENDINGS = {'', 'μαι', 'σαι', 'ται', 'μεθα', 'σθε', 'νται', 'μην', 'σο', 'το', 'ντο', 'ο', 'σθω', 'σθων',
                  'θε', 'θω', 'θων'}
THIRD_DECLENSION = {'οσ', 'ι', 'α', 'εσ', 'ων', 'ασ'}
FIRST_DECLENSION = {'α', 'αν', 'ησ', 'η', 'αι', 'ων', 'αισ', 'ασ'}
MIDDLE_DECLENSION = {'οσ', 'ου', 'ω', 'ον', 'ε', 'οι', 'ων', 'οισ', 'ουσ', 'α', 'η', 'ησ', 'ην', 'αι', 'αισ', 'ασ'}


class Skip(Exception):
    """A form this script will not cut; the message is the reported reason."""


def letters(text):
    """Bare lower-case letters: no diacritics, tags, breathing 'h' or boundary marks."""
    text = re.sub(r'\{[^}]*\}', '', text).replace('h', '').replace('|', '')
    out = []
    for c in unicodedata.normalize('NFD', text):
        if not unicodedata.combining(c):
            out.append('σ' if c == 'ς' else c.lower())
    return ''.join(out)


def graphemes(word):
    units = []
    for c in unicodedata.normalize('NFD', word):
        if unicodedata.combining(c) and units:
            units[-1] += c
        else:
            units.append(c)
    return [unicodedata.normalize('NFC', u) for u in units]


def slot_of(record, voice=None):
    s = TENSE[record['tense']] + (voice or record['voice'])[0] + MOOD[record['mood']]
    if record['mood'] == 'Participle':
        return s + '.' + CASE[record['case']] + record['number'][0] + record['gender'][0]
    if record['mood'] != 'Infinitive':
        person, number = record['person'].split()
        return s + '.' + person[0] + ('S' if number == 'singular' else 'P')
    return s


def leading_vowels(text):
    n = 0
    while n < len(text) and text[n] in VOWELS:
        n += 1
    return text[:n]


def cut_augment(unaugmented, augmented):
    """Return ('syllabic'|'temporal'|'none', letters of the augment piece) or None."""
    if augmented == 'ε' + unaugmented and unaugmented[:1] not in VOWELS:
        return 'syllabic', 1
    before, after = leading_vowels(unaugmented), leading_vowels(augmented)
    if not before or unaugmented[len(before):] != augmented[len(after):]:
        return None
    if before == after:
        return 'none', 0  # already long: no visible augment
    if (before, after) in LENGTHENED:
        return 'temporal', len(after)
    return None


def cut_augment_loosely(unaugmented, augmented):
    """As cut_augment, for stems whose vowel grade differs between the two (διδο-, ἐδιδου-)."""
    if augmented[:1] == 'ε' and unaugmented[:1] not in VOWELS and augmented[1:2] == unaugmented[:1]:
        return 'syllabic', 1
    if augmented[:1] == unaugmented[:1] and augmented[:1] in 'ιυηω':
        return 'none', 0  # ἵην: ι lengthens without changing its spelling
    before, after = leading_vowels(unaugmented), leading_vowels(augmented)
    if not before or unaugmented[len(before):len(before) + 1] != augmented[len(after):len(after) + 1]:
        return None
    if before == after:
        return 'none', 0
    if (before, after) in LENGTHENED:
        return 'temporal', len(after)
    return None


def cut_stem(lemma, stem, tense, augmented, second, counterparts, passive=False, others=(), empty_ok=False, active=True):
    """Pieces of a full tense stem as [letters, [roles]]."""
    pieces = []
    rest = stem
    unaug_prefix, aug_prefix = COMPOUNDS.get(letters(lemma), ('', ''))
    prefix = aug_prefix if augmented else unaug_prefix
    if prefix:
        if not rest.startswith(prefix):
            raise Skip('compound prefix not found in stem')
        pieces.append([prefix, ['Prefix']])
        rest = rest[len(prefix):]

    system = {'P': 'Present', 'I': 'Present', 'F': 'Future', 'A': 'Aorist', 'X': 'Perfect', 'Y': 'Perfect'}[tense]
    fused_augment = 0
    if augmented:
        found = None
        for compare in (cut_augment, cut_augment_loosely):
            for other in sorted(counterparts, key=len, reverse=True):
                if unaug_prefix and not other.startswith(unaug_prefix):
                    continue
                found = compare(other[len(unaug_prefix):], rest)
                if found:
                    break
            if found:
                break
        if not found:  # no stem of the same system to compare: any stem of the verb will show a syllabic augment
            for other in others:
                found = cut_augment_loosely(other[len(unaug_prefix):], rest) if other.startswith(unaug_prefix) else None
                if found and found[0] == 'syllabic':
                    break
                found = None
        if not found:
            raise Skip('augment not identified')
        kind, size = found
        if kind == 'syllabic':
            pieces.append(['ε', ['Augment']])
            rest = rest[1:]
        elif kind == 'temporal':
            fused_augment = size

    key = letters(lemma)
    odd = PERFECT_REDUPLICATION.get(key) if tense in 'XY' else None
    present = PRESENT_REDUPLICATION.get(key) if tense in 'PI' else None
    if odd and fused_augment:  # εἱ-στήκη: the augment has lengthened the reduplication
        pieces.append([rest[:fused_augment], ['Augment', 'Reduplication']])
        rest, fused_augment = rest[fused_augment:], 0
    elif odd and rest.startswith(odd) and len(rest) > len(odd):
        pieces.append([odd, ['Reduplication']])
        rest = rest[len(odd):]
    elif present and not fused_augment and rest.startswith(present):
        pieces.append([present, ['Present reduplication']])
        rest = rest[len(present):]
    elif tense in 'XY' and len(rest) >= 3 and rest[1] == 'ε' and rest[0] not in VOWELS \
            and (rest[0] == rest[2] or (rest[0], rest[2]) in ASPIRATE_PAIRS):
        pieces.append([rest[:2], ['Reduplication']])
        rest = rest[2:]

    marker_name = {'F': 'Future marker', 'A': 'Aorist marker', 'X': 'Perfect marker', 'Y': 'Perfect marker'}.get(tense)
    markers = []
    if not rest and (present or empty_ok):  # ἱ-ῶ, ὦ: the stem vowel is wholly inside the contraction that follows
        return pieces, system + ' stem'
    if not rest:
        raise Skip('nothing left of the stem')
    if tense == 'A' and not passive and not second and key in KAPPA_AORIST and len(rest) > 1 and rest[-1] == 'κ':
        markers = [['κ', ['Aorist marker']]]
    elif passive and tense == 'A':
        if len(rest) > 1 and rest[-1] == 'θ':
            markers = [['θ', ['Passive marker']]]
    elif passive and tense == 'F' and len(rest) > 3 and rest.endswith('θησ'):
        markers = [['θ', ['Passive marker']], ['η', ['Passive marker']], ['σ', ['Future marker']]]
    elif passive and tense == 'F' and len(rest) > 2 and rest.endswith('ησ'):
        markers = [['η', ['Passive marker']], ['σ', ['Future marker']]]
    elif tense in 'FA' and not second and len(rest) > 1 and rest[-1] == 'σ':
        markers = [['σ', [marker_name]]]
    elif tense in 'FA' and not second and rest[-1] in 'ψξ':
        markers = [[rest[-1], ['Verb stem', marker_name]]]
    elif tense in 'XY' and active and len(rest) > 1 and rest[-1] == 'κ':  # in the middle, κ is the stem's own (ἦρκται)
        markers = [['κ', [marker_name]]]
    if markers:
        rest = rest[:-len(markers)]
    core_role = 'Verb stem' if markers else system + ' stem'

    if fused_augment:
        if fused_augment > len(rest):
            raise Skip('augment longer than stem')
        pieces.append([rest[:fused_augment], ['Augment', core_role]])
        rest = rest[fused_augment:]
    if rest and key in NU_PRESENT and tense in 'PI' and rest.endswith('νυ') and len(rest) > 2:
        pieces += [[rest[:-2], [core_role]], ['νυ', [core_role]]]
    elif rest:
        pieces.append([rest, [core_role]])
    pieces += markers
    return pieces, core_role


def cut_aorist_passive(mood, complex_):
    """Pieces after θ in the aorist passive: the marker's vowel, then the ending."""
    marker = 'Passive marker'
    wrong = Skip('unrecognised aorist passive ending')
    if mood in 'ID':
        vowel, rest = complex_[:1], complex_[1:]
        if vowel not in ('η', 'ε') or rest not in {'', 'ν', 'σ', 'μεν', 'τε', 'σαν', 'τι', 'τω', 'ντων'}:
            raise wrong
        return [[vowel, [marker]], [rest, ['Personal ending']]] if rest else [[vowel, [marker, 'Personal ending']]]
    if mood == 'N':
        if complex_ != 'ηναι':
            raise wrong
        return [['η', [marker]], ['ναι', ['Infinitive ending']]]
    if mood == 'S':  # θε- contracted with the subjunctive vowel
        vowel, rest = complex_[:1], complex_[1:]
        if vowel not in ('ω', 'η') or rest not in ACTIVE_ENDINGS:
            raise wrong
        roles = [marker, 'Subjunctive vowel']
        return [[vowel, roles], [rest, ['Personal ending']]] if rest else [[vowel, roles + ['Personal ending']]]
    if mood == 'O':
        m = re.match('ε(ιη|ι)', complex_)
        rest = complex_[m.end():] if m else None
        if rest not in {'', 'ν', 'σ', 'μεν', 'τε', 'εν', 'σαν'}:
            raise wrong
        tail = [[rest, ['Personal ending']]] if rest else []
        return [['ε', [marker]], [m.group(1), ['Optative marker'] + ([] if rest else ['Personal ending'])]] + tail
    if complex_ == 'εισ':  # λυθείς from λυθε-ντ-ς
        return [['ει', [marker, 'Participle marker']], ['σ', ['Nominal ending']]]
    if complex_ == 'εν':
        return [['ε', [marker]], ['ν', ['Participle marker', 'Nominal ending']]]
    if complex_.startswith('εντ') and complex_[3:] in THIRD_DECLENSION:
        return [['ε', [marker]], ['ντ', ['Participle marker']], [complex_[3:], ['Nominal ending']]]
    if complex_ == 'εισι':
        return [['ει', [marker, 'Participle marker']], ['σι', ['Nominal ending']]]
    if complex_.startswith('εισ') and complex_[3:] in FIRST_DECLENSION:
        return [['εισ', [marker, 'Participle marker']], [complex_[3:], ['Nominal ending']]]
    raise wrong


def cut_finite(family, person, complex_, zone):
    """Pieces after the stem for a finite form. zone is the contracted vowel, if any."""
    tense, voice, mood = family
    endings = ACTIVE_ENDINGS if voice == 'A' else MIDDLE_ENDINGS
    # First aorist, perfect and pluperfect; second aorists arrive as tense 'a'.
    # The perfect imperative uses the thematic vowel.
    alpha = tense in 'AXY' and not (tense == 'X' and mood == 'D')
    if mood == 'D' and tense == 'A' and person == '2S' and complex_ in ('ον', 'αι'):
        return [[complex_, ['Personal ending']]]  # λῦσ-ον, λῦσ-αι
    if mood == 'S':
        role, pattern = 'Subjunctive vowel', '(ω|η)'
    elif mood == 'O':
        role, pattern = 'Optative marker', '(οι|αι|ει)'
    elif alpha:
        role, pattern = 'Tense vowel', '(ει|η|ε)' if tense == 'Y' else '(α|ε|ω)'
    else:
        role, pattern = 'Thematic vowel', '(ου|ει|ο|ε|ω|η)'
    if zone:
        vowel, rest = zone, complex_
        if mood == 'O' and rest.startswith('η'):
            vowel, rest = vowel + 'η', rest[1:]
        elif mood == 'O' and not rest and len(vowel) > 1 and vowel.endswith('ο'):
            vowel, rest = vowel[:-1], 'ο'  # -οιο, -ῷο: the rule writes the ending inside the contraction
    else:
        m = re.match(pattern, complex_)
        vowel = m.group(1) if m else ''
        rest = complex_[len(vowel):]
        if mood == 'O' and vowel and rest.startswith('η'):  # ἰοίην
            vowel, rest = vowel + 'η', rest[1:]
    if rest not in endings:
        raise Skip('unrecognised finite ending')
    if not vowel:
        if not rest:
            raise Skip('nothing after the stem')
        return [[rest, ['Personal ending']]]
    # Primary -σι and -ς have merged with the vowel before them (λύουσι from
    # -ο-ντι): a learner meets -ουσι and -εις whole.
    if voice == 'A' and mood == 'I' and tense in 'PF' and (rest == 'σι' or (rest == 'σ' and person == '2S')):
        vowel, rest = vowel + rest, ''
    if not rest:
        return [[vowel, [role, 'Personal ending']]]
    return [[vowel, [role]], [rest, ['Personal ending']]]


def cut_infinitive(family, complex_, zone):
    tense, voice, _ = family
    if voice == 'A':
        if zone:
            if complex_ != 'ν':
                raise Skip('unrecognised infinitive ending')
            return [[zone + 'ν', ['Thematic vowel', 'Infinitive ending']]]
        if tense == 'A' and complex_ == 'αι':
            return [['αι', ['Infinitive ending']]]
        if tense == 'X' and complex_ == 'εναι':
            return [['εναι', ['Infinitive ending']]]
        if tense in 'PFa' and complex_ == 'ειν':
            return [['ειν', ['Thematic vowel', 'Infinitive ending']]]
        raise Skip('unrecognised infinitive ending')
    if zone:
        if complex_ != 'σθαι':
            raise Skip('unrecognised infinitive ending')
        return [[zone, ['Thematic vowel']], ['σθαι', ['Infinitive ending']]]
    if tense == 'X' and complex_ in ('σθαι', 'θαι'):
        return [[complex_, ['Infinitive ending']]]
    if False:
        return [['σθαι', ['Infinitive ending']]]
    if tense == 'A' and complex_ == 'ασθαι':
        return [['α', ['Tense vowel']], ['σθαι', ['Infinitive ending']]]
    if complex_ == 'εσθαι':
        return [['ε', ['Thematic vowel']], ['σθαι', ['Infinitive ending']]]
    raise Skip('unrecognised infinitive ending')


def cut_participle(family, complex_, zone):
    tense, voice, _ = family
    if voice == 'M':
        role = 'Thematic vowel'
        if zone:
            vowel, rest = zone, complex_
        elif tense == 'X':
            vowel, rest = '', complex_  # the perfect adds -μεν- straight to the stem
        elif tense == 'A' and complex_.startswith('α'):
            vowel, rest, role = 'α', complex_[1:], 'Tense vowel'
        else:
            vowel = 'ο' if complex_.startswith('ο') else ''
            rest = complex_[len(vowel):]
        if (not vowel and tense != 'X') or not rest.startswith('μεν') or rest[3:] not in MIDDLE_DECLENSION:
            raise Skip('unrecognised participle ending')
        head = [[vowel, [role]]] if vowel else []
        return head + [['μεν', ['Participle marker']], [rest[3:], ['Nominal ending']]]
    if tense == 'X':
        if complex_ == 'ωσ':
            return [['ω', ['Participle marker']], ['σ', ['Nominal ending']]]
        if complex_ == 'οσ':
            return [[complex_, ['Participle marker', 'Nominal ending']]]
        if complex_ == 'οσι':
            return [['ο', ['Participle marker']], [complex_[1:], ['Nominal ending']]]
        if complex_.startswith('οτ') and complex_[2:] in THIRD_DECLENSION:
            return [['οτ', ['Participle marker']], [complex_[2:], ['Nominal ending']]]
        if complex_.startswith('υι') and complex_[2:] in FIRST_DECLENSION:
            return [['υι', ['Participle marker']], [complex_[2:], ['Nominal ending']]]
        raise Skip('unrecognised participle ending')
    role = 'Tense vowel' if tense == 'A' else 'Thematic vowel'
    if zone:
        vowel, rest = zone, complex_
    else:
        m = re.match('(α)' if tense == 'A' else '(ου|ω|ο)', complex_)
        if not m:
            raise Skip('unrecognised participle ending')
        vowel, rest = m.group(1), complex_[len(m.group(1)):]
    if rest == 'ν' and vowel == 'ω':  # λύων: lengthened vowel and ν together, no separate ending
        return [[vowel + rest, [role, 'Participle marker', 'Nominal ending']]]
    if rest == 'ν':  # λῦον, λῦσαν from -ντ: ν is what is left of the marker
        return [[vowel, [role]], ['ν', ['Participle marker', 'Nominal ending']]]
    if rest == 'σ' and tense == 'A':  # λύσας from λυσα-ντ-ς
        return [[vowel, [role, 'Participle marker']], ['σ', ['Nominal ending']]]
    if rest.startswith('ντ') and rest[2:] in THIRD_DECLENSION:
        return [[vowel, [role]], ['ντ', ['Participle marker']], [rest[2:], ['Nominal ending']]]
    if rest == 'σι':
        return [[vowel, [role, 'Participle marker']], [rest, ['Nominal ending']]]
    if rest.startswith('σ') and rest[1:] in FIRST_DECLENSION:
        return [[vowel + 'σ', [role, 'Participle marker']], [rest[1:], ['Nominal ending']]]
    raise Skip('unrecognised participle ending')


def spell(word, pieces):
    """Turn letter-count pieces into the word's own accented letters."""
    target = letters(word)
    if ''.join(p[0] for p in pieces) != target:
        raise Skip('pieces do not spell the word')
    units = graphemes(word)
    if len(units) != len(target):
        raise Skip('unexpected characters in word')
    out, at = [], 0
    for text, roles in pieces:
        if not text:
            raise Skip('empty piece')
        out.append([''.join(units[at:at + len(text)]), ' + '.join(roles)])
        at += len(text)
    return out


def segment_athematic(word, lemma, slot, stem, root, b, c_raw, d, e_raw, counterparts, others):
    """-μι presents and root aorists: endings join the stem with no vowel between."""
    tense, voice, mood = slot[:3]
    target = letters(word)
    if b and (any(ch not in VOWELS for ch in b) or not stem.endswith(b)):
        raise Skip('unsupported stem change')
    base = stem[:-len(b)] if b else stem
    movable = '(ν)' in c_raw + e_raw
    c = e = None
    for nu in (('', 'ν') if movable else ('',)):
        c, e = letters(c_raw.replace('(ν)', nu)), letters(e_raw.replace('(ν)', nu))
        if base + c + e == target:
            break
    else:
        raise Skip('derivation does not spell the word')
    movable_nu = movable and target.endswith('ν') and e.endswith('ν')
    if movable_nu:
        e = e[:-1]
    middle = voice != 'A'
    endings = MIDDLE_ENDINGS if middle else ACTIVE_ENDINGS
    personal, wrong = ['Personal ending'], Skip('unrecognised athematic ending')
    fuse = False  # the first piece after the stem shares a letter with it
    if mood == 'S':  # stem vowel contracted with the subjunctive vowel
        if not (b and c) or e not in endings:
            raise wrong
        shown, fuse = base, True
        tail = [[c, ['Subjunctive vowel'] + ([] if e else personal)]] + ([[e, personal]] if e else [])
    elif mood == 'O':  # stem vowel, then -ι- or -ιη-
        if not c.endswith('ι') or c[:-1] not in ('', b):
            raise wrong
        marker, rest = 'ι', e
        if rest.startswith('η'):
            marker, rest = 'ιη', rest[1:]
        if rest not in endings:
            raise wrong
        shown = base + c[:-1]
        tail = [[marker, ['Optative marker'] + ([] if rest else personal)]] + ([[rest, personal]] if rest else [])
    elif mood == 'N':
        if e not in ('ναι', 'σθαι', 'εναι'):
            raise wrong
        shown, tail = base + c, [[e, ['Infinitive ending']]]
    elif mood == 'P':
        marker, nominal = ['Participle marker'], ['Nominal ending']
        if middle:
            if not e.startswith('μεν') or e[3:] not in MIDDLE_DECLENSION:
                raise wrong
            shown, tail = base + c, [['μεν', marker], [e[3:], nominal]]
        elif e.startswith('ντ') and e[2:] in THIRD_DECLENSION:
            shown, tail = base + c, [['ντ', marker], [e[2:], nominal]]
        elif c and e == 'σ':  # διδούς from διδο-ντ-ς: the lengthened vowel is all that is left of -ντ-
            shown, fuse, tail = base, True, [[c, marker], ['σ', nominal]]
        elif c and e == 'ν':  # διδόν from διδο-ντ: ν is what is left of -ντ-, with no ending
            shown, tail = base + c, [['ν', marker + nominal]]
        elif c and e == 'σι':
            shown, fuse, tail = base, True, [[c, marker], ['σι', nominal]]
        elif c and e.startswith('σ') and e[1:] in FIRST_DECLENSION:
            shown, fuse, tail = base, True, [[c + 'σ', marker], [e[1:], nominal]]
        elif len(c) > 1 and c.endswith('σ') and e in FIRST_DECLENSION:
            shown, fuse, tail = base, True, [[c, marker], [e, nominal]]
        else:
            raise wrong
    elif middle and b and not e and c in ('ου', 'ω') and slot[4:] == '2S':  # ἔθου, ἐδύνω: stem vowel contracted with -σο
        shown, fuse, tail = base, True, [[c, personal]]
    elif middle and not c and e == 'ου':  # θοῦ, δοῦ
        shown, fuse, tail = base, True, [['ου', personal]]
    elif not middle and tense in 'PI' and (b, c) in (('ο', 'ου'), ('ε', 'ει')):
        # ἐδίδουν, ἐτίθεις, δίδου, τίθει: formed like contract verbs (διδο- + ο/ε), not from the long-vowel stem
        if e not in endings:
            raise wrong
        shown, fuse = base, True
        tail = [[c, ['Thematic vowel'] + ([] if e else personal)]] + ([[e, personal]] if e else [])
    elif not middle and b and e == 'σι' and letters(d) == 'α' and c.endswith('α'):
        if len(c) > len(b):  # διδό-ασι
            shown, tail = base + c[:-1], [['ασι', personal]]
        else:  # ἱστᾶσι: stem vowel contracted with -ασι
            shown, fuse, tail = base, True, [['ασι', personal]]
    else:
        if e not in endings | {'θι', 'σθα', 'θα', 'μι', 'τι', 'των', 'ασι'}:
            raise wrong
        shown, tail = base + c, ([[e, personal]] if e else [])

    augmented = mood == 'I' and tense in 'IAY'
    pieces, core_role = cut_stem(lemma, shown, tense, augmented, root, counterparts, others=others, empty_ok=fuse,
                                 active=voice == 'A')
    if fuse:
        tail[0][1] = [core_role] + tail[0][1]
    pieces += tail
    if movable_nu:
        pieces.append(['ν', ['Movable ν']])
    return spell(word, pieces)


def segment(word, lemma, slot, derivation, counterparts, others=()):
    family = slot[:3]
    person = slot[4:] if '.' in slot else ''
    tense, voice, mood = family
    stem_text = derivation['stem']
    m = re.match(r"SandhiRule\('([^']*)'", derivation['rule'])
    if not m:
        raise Skip('unreadable rule')
    rule = m.group(1)
    tags = set(re.findall(r'\{([^}]*)\}', stem_text))
    if tags - {'2nd', 'enclitic', 'recessive', 'contract'} - STEM_CLASSES:
        raise Skip('irregular stem class')
    second = '2nd' in tags
    a, bcd, e = rule.split('|')
    b, cd = bcd.split('>')
    c, d = cd.split('<')
    b = letters(b)
    stem = letters(stem_text)
    if not stem or stem == '0':
        raise Skip('empty stem')
    if tags & STEM_CLASSES:
        return segment_athematic(word, lemma, slot, stem, 'root' in tags, b, c, d, e, counterparts, others)

    target = letters(word)
    # Movable ν is written "(ν)" in a rule; try the form with and without it.
    movable = '(ν)' in c + e
    choices = [(letters(c.replace('(ν)', nu)), letters(e.replace('(ν)', nu))) for nu in (('', 'ν') if movable else ('',))]
    c = choices[0][0] if '(ν)' not in c else None
    zone = ''
    # A contract future (βαλῶ from βαλέ-ω) has its marker ε inside the contraction.
    liquid = 'contract' in tags and not b
    contracted = liquid or (bool(b) and (bool(d) or c != b))
    if contracted and not liquid and b not in ('α', 'ε', 'ο'):
        raise Skip('unsupported stem change')
    shown_stem = stem[:-len(b)] if contracted and b else stem
    if b and not stem.endswith(b):
        raise Skip('rule does not fit stem')
    complex_ = None
    for surface, ending in choices:
        tail = ending if (contracted or b) else surface + ending
        if shown_stem + (surface if contracted else '') + tail == target:
            complex_, c = tail, surface
            break
    if complex_ is None:
        raise Skip('derivation does not spell the word')
    # Movable ν becomes a final piece of its own; the rest is cut without it.
    movable_nu = movable and target.endswith('ν') and complex_.endswith('ν')
    if movable_nu:
        complex_ = complex_[:-1]
    if contracted:
        zone = c
    if liquid and mood == 'P' and not complex_ and zone.endswith('ν') and len(zone) > 1:
        zone, complex_ = zone[:-1], 'ν'  # the rule writes βαλῶν as one unit

    augmented = mood == 'I' and tense in 'IAY'
    passive = voice == 'P' and tense in 'AF'
    pieces, core_role = cut_stem(lemma, stem, tense, augmented, second, counterparts, passive, others, active=voice == 'A')
    if contracted and b:
        last = pieces[-1]
        if last[1] != [core_role] or not last[0].endswith(b):
            raise Skip('contraction does not meet a plain stem')
        last[0] = last[0][:-len(b)]
        if not last[0]:
            pieces.pop()

    # Second aorists inflect like the present system, not with the alpha endings.
    # Outside the aorist, the passive uses the middle's endings.
    ending_family = ('a' if tense == 'A' and second else tense) + ('M' if voice == 'P' else voice) + mood
    if voice == 'P' and tense == 'A':
        tail = cut_aorist_passive(mood, complex_)
    elif mood == 'N':
        tail = cut_infinitive(ending_family, complex_, zone)
    elif mood == 'P':
        tail = cut_participle(ending_family, complex_, zone)
    else:
        tail = cut_finite(ending_family, person, complex_, zone)
    if contracted:
        tail[0][1] = (['Future marker'] if liquid else [core_role]) + tail[0][1]
    pieces += tail
    if movable_nu:
        pieces.append(['ν', ['Movable ν']])

    return spell(word, pieces)


# ---- Forms the generator does not reproduce ----
# Each verb lists, per tense-voice-mood pattern, the stems to try. A stem with
# a class in braces is cut as an athematic stem (segment_athematic), a plain
# stem as a thematic or consonant stem (segment), '' means the form has no
# stem left at all (ὤν). A (stem, rule) pair gives the generator-style rule in
# full. The same checks apply as to generator derivations: a stem that does
# not lead to a recognised ending is passed over.
MANUAL = {
    'ἵστημι': [('AA.|AMP', ['στα{root}', 'στη{root}']), ('X..|YAI', ['εστα{athematic}']),
               ('P..|I..', ['ιστα{athematic}']), ('FPI', ['σταθησ'])],
    'τίθημι': [('P..', ['τιθε{athematic}', 'τιθ']), ('AA.|AM.', ['θε{root}']), ('XAI', ['τεθηκ']), ('FP.', ['τεθησ'])],
    'δίδωμι': [('P..', ['διδο{athematic}']), ('AA.', ['δο{root}'])],
    'ἵημι': [('P..|I..', ['ιε{athematic}']), ('AAI', ['ηκ', 'ει{root}']), ('AMI', ['ει{root}']),
             ('AA.|AM.', ['ε{root}']), ('XAI', ['εικ']), ('XM.|XP.', ['ει']), ('API', ['ειθ']), ('FPI', ['εθησ'])],
    'δείκνυμι': [('P..', ['δεικνυ{athematic}']), ('I..', ['εδεικνυ{athematic}']), ('XM.|XP.', ['δεδειγ']),
                 ('FP.', ['δειχθησ']), ('AP.', ['εδειχθ'])],
    'εἰμί': [('PAI', ['ει{athematic}', 'εσ{athematic}']), ('PAO|PAS', ['ε{athematic}']),
             ('PAP|PAD', ['εσ{athematic}', '']), ('IAI', ['η{athematic}', 'ησ{athematic}'])],
    'εἶμι': [('PAI|PAD|PAN', ['ει{athematic}', 'ι{athematic}', 'ι']), ('PAS|PAO|PAP', ['ι'])],
    'οἶδα': [('XAI|XAD', ['οισ{athematic}', 'ισ{athematic}']), ('XAO', ['ειδε{athematic}']), ('YAI', ['ηδ', 'ησ{athematic}'])],
    'φημί': [('PAP', ['φα{athematic}', 'φασκ']), ('P..', ['φα{athematic}', 'φη{athematic}']), ('IAI', ['εφη{athematic}'])],
    'δύναμαι': [('P..', ['δυνα{athematic}'])],
    'ἐπίσταμαι': [('P..', ['επιστα{athematic}']), ('I..', ['ηπιστα{athematic}'])],
    'βαίνω': [('AAI', ['εβη{root}']), ('AA.', ['βη{root}', 'βα{root}'])],
    'γιγνώσκω': [('AAI', ['εγνω{root}']), ('AA.', ['γνω{root}', 'γνο{root}'])],
    'πέμπω': [('X[MP].', ['πεπεμ', 'πεπεμπ', 'πεπεμφ']), ('Y[MP].', ['επεπεμ', 'επεπεμπ', 'επεπεμφ'])],
    'πείθω': [('X[MP].', ['πεπει', 'πεπεισ']), ('Y[MP].', ['επεπει', 'επεπεισ'])],
    'ἄρχω': [('[XY][MP].', ['ηργ', 'ηρκ', 'ηρχ'])],
    'ὁράω': [('[XY][MP].', ['ωμ', 'ωπ', 'ωφ']), ('AAD', [('ιδ{2nd}', "SandhiRule('|><|ε')")])],
    'φαίνω': [('X[MP].', ['πεφασ', 'πεφαν'])],
    'λαμβάνω': [('X[MP]P', ['ειλημ']), ('AAD', [('λαβ{2nd}', "SandhiRule('|><|ε')")])],
    'ἔχω': [('AAD', ['σχε{root}'])],
    'λύω': [('YAI', ['ελελυκ']), ('FPI', ['λυθησ']), ('PAP|PAD', ['λυ'])],
    'παύω': [('FPI', ['παυθησ'])],
    'νικάω': [('PAD', [('νικα', "SandhiRule('|α>α<T_2|')")])],
}
# Unaugmented stems for comparing augments, where the generator supplies none.
MANUAL_PLAIN = {
    ('ἵημι', 'A', False): {'ε', 'εκ'}, ('ἵημι', 'A', True): {'εθ'}, ('εἰμί', 'P', False): {'ε', 'εσ'},
    ('οἶδα', 'X', False): {'ειδ', 'εισ'}, ('βαίνω', 'A', False): {'βη'}, ('γιγνώσκω', 'A', False): {'γνω'},
    ('πέμπω', 'X', False): {'πεπεμ', 'πεπεμπ', 'πεπεμφ'}, ('πείθω', 'X', False): {'πεπει', 'πεπεισ'},
    ('ἄρχω', 'X', False): {'ηργ', 'ηρκ', 'ηρχ'}, ('ὁράω', 'X', False): {'ωμ', 'ωπ', 'ωφ'},
    ('δείκνυμι', 'P', False): {'δεικνυ'},
}
# Forms cut by hand: the imperfect of εἶμι (ᾖα) and one participle of ἵστημι.
_GO = ['Augment', 'Present stem']
DIRECT = {
    'ᾖα|εἶμι|IAI': [['η', _GO], ['α', ['Personal ending']]],
    'ᾔεις|εἶμι|IAI': [['η', _GO], ['ει', ['Tense vowel']], ['σ', ['Personal ending']]],
    'ᾔει|εἶμι|IAI': [['η', _GO], ['ει', ['Tense vowel', 'Personal ending']]],
    'ᾔειν|εἶμι|IAI|3S': [['η', _GO], ['ει', ['Tense vowel', 'Personal ending']], ['ν', ['Movable ν']]],
    'ᾔειν|εἶμι|IAI|1S': [['η', _GO], ['ει', ['Tense vowel']], ['ν', ['Personal ending']]],
    'ᾖμεν|εἶμι|IAI': [['η', _GO], ['μεν', ['Personal ending']]],
    'ᾖτε|εἶμι|IAI': [['η', _GO], ['τε', ['Personal ending']]],
    'ᾖσαν|εἶμι|IAI': [['η', _GO], ['σαν', ['Personal ending']]],
    'ᾔεσαν|εἶμι|IAI': [['η', _GO], ['ε', ['Tense vowel']], ['σαν', ['Personal ending']]],
    # Second singular of consonant-stem perfects: ψ and ξ hold the stem's last consonant and the σ of -σαι, -σο.
    **{f'{word}|{lemma}|{tense}{voice}I': [*([['ε', ['Augment']]] if word[0] == 'ἐ' else []),
                                           *([['πε', ['Reduplication']]] if 'πεμ' in head else []),
                                           [head[-3:] if 'πεμ' in head else head, ['Perfect stem']],
                                           [fused, ['Perfect stem', 'Personal ending']], [end, ['Personal ending']]]
       for word, lemma, tense, head, fused, end in [
           ('πέπεμψαι', 'πέμπω', 'X', 'πεπεμ', 'ψ', 'αι'), ('ἐπέπεμψο', 'πέμπω', 'Y', 'επεπεμ', 'ψ', 'ο'),
           ('ἦρξαι', 'ἄρχω', 'X', 'ηρ', 'ξ', 'αι'), ('ἦρξο', 'ἄρχω', 'Y', 'ηρ', 'ξ', 'ο'),
           ('ὦψαι', 'ὁράω', 'X', 'ω', 'ψ', 'αι'), ('ὦψο', 'ὁράω', 'Y', 'ω', 'ψ', 'ο')]
       for voice in 'MP'},
    'ἑστῶτος|ἵστημι|XAP': [['ε', ['Reduplication']], ['στ', ['Perfect stem']], ['ωτ', ['Perfect stem', 'Participle marker']],
                           ['οσ', ['Nominal ending']]],
}


def manual_candidates(spec, target, slot):
    """Generator-style readings of a word for one manual stem, likeliest first."""
    person = slot[4:]
    nu = lambda e: e[:-1] + '(ν)' if e.endswith('ιν') or (person == '3S' and e.endswith(('εν', 'ειν'))) else e
    if isinstance(spec, tuple):
        yield 'rule', spec[0], spec[1]
        return
    stem = letters(spec)
    if '{' not in spec:
        if target.startswith(stem):
            yield ('tail' if not stem else 'rule'), stem, "SandhiRule('|><|" + nu(target[len(stem):]) + "')"
        return
    vowels = len(stem) - len(stem.rstrip(VOWELS))
    for b in [''] + [stem[-n:] for n in (1, 2) if n <= vowels]:
        base = stem[:-len(b)] if b else stem
        if not target.startswith(base):
            continue
        rest = target[len(base):]
        if not b:
            cuts = [0] + ([1] if slot[2] == 'O' and rest[:1] == 'ι' else [])
        else:
            cuts = [k for k in dict.fromkeys((len(b), 1, 2, 3, 0)) if k <= len(rest)]
        for k in cuts:
            c, e = rest[:k], rest[k:]
            if any(ch not in VOWELS for ch in c):
                continue  # what replaces a stem vowel is a vowel
            grades = {'ο': ('ω', 'ου'), 'ε': ('η', 'ει'), 'α': ('η',)}.get(b, ())
            if b and c and slot[2] not in 'SO' and c != b and c not in grades and not (c == 'α' and e in ('σι', 'σιν')):
                continue  # outside contraction a stem vowel only changes grade (ἰ-ό-ντων is thematic, not a stem ἰο-)
            if not b and slot[2] == 'I' and stem.endswith('α') and e in ('σι', 'σιν'):
                continue  # ἑστᾶσι: -α- contracted with -ασι, not -σι on the bare stem
            d = 'ᾱ' if b and c.endswith('α') and e in ('σι', 'σιν') else ''
            yield 'class', stem, 'root' in spec, b, c, d, nu(e)


def manual_cut(record, slot, counterparts, others):
    word, lemma = record['word'], record['lemma']
    for key in (f'{word}|{lemma}|{slot[:3]}|{slot[4:]}', f'{word}|{lemma}|{slot[:3]}'):
        if key in DIRECT:
            return spell(word, [[text, list(roles)] for text, roles in DIRECT[key]])
    target = letters(word)
    for pattern, specs in MANUAL.get(lemma, []):
        if not re.fullmatch(pattern, slot[:3]):
            continue
        for spec in specs:
            for kind, stem, *rest in manual_candidates(spec, target, slot):
                try:
                    if kind == 'class':
                        return segment_athematic(word, lemma, slot, stem, *rest, counterparts, others)
                    if kind == 'tail':
                        complex_ = letters(re.match(r"SandhiRule\('\|><\|([^']*)'", rest[0]).group(1).replace('(ν)', ''))
                        cut = cut_participle if slot[2] == 'P' else cut_finite
                        args = (slot[:3], complex_, '') if slot[2] == 'P' else (slot[:3], slot[4:], complex_, '')
                        return spell(word, cut(*args) + ([['ν', ['Movable ν']]] if '(ν)' in rest[0] else []))
                    return segment(word, lemma, slot, {'stem': stem, 'rule': rest[0]}, counterparts, others)
                except Skip:
                    continue
    return None


def main():
    source = (ROOT / 'dist/paradigms.js').read_text(encoding='utf-8').split('export const paradigms = ', 1)[1].strip().removesuffix(';')
    records = json.loads(source)
    constructions = json.loads((ROOT / 'data/generated-constructions.json').read_text(encoding='utf-8'))
    by_slot = {(c['word'], c['lemma'], c['slot']): c for c in constructions}

    # Unaugmented stems of each verb's present and aorist systems, to compare
    # against the augmented stems of the imperfect and aorist indicative.
    plain, every = defaultdict(set), defaultdict(set)
    for c in constructions:
        tense, voice, mood = c['slot'][:3]
        if tense in 'PX' or (tense == 'A' and mood != 'I'):
            for d in c['derivations']:
                plain[(c['lemma'], tense, voice == 'P' and tense == 'A')].add(letters(d['stem']))
                every[c['lemma']].add(letters(d['stem']))

    # ἐθέλω has only imperfect forms in the pack, so its present stem is given here.
    plain[('ἐθέλω', 'P', False)].add('εθελ')
    for (lemma, tense, passive), stems in MANUAL_PLAIN.items():
        plain[(lemma, tense, passive)] |= stems
        every[lemma] |= stems

    segments, reasons, samples = {}, Counter(), defaultdict(list)
    cuts, covered, manual, by_hand_keys = defaultdict(dict), 0, 0, set()
    skipped_families = Counter()
    for record in records:
        slot = slot_of(record)
        family = slot[:3]
        entry = by_slot.get((record['word'], record['lemma'], slot))
        if not entry and record['voice'] == 'Passive' and record['tense'] in ('Present', 'Imperfect', 'Perfect', 'Pluperfect'):
            # Outside the aorist and future, passives are spelled and built like the middle.
            slot = slot_of(record, 'Middle')
            entry = by_slot.get((record['word'], record['lemma'], slot))
        if slot[:3] not in SUPPORTED:
            reasons['family not yet supported'] += 1
            skipped_families[family] += 1
            continue
        tense = slot[0]
        counterparts = plain[(record['lemma'], {'I': 'P', 'Y': 'X'}.get(tense, tense), slot[:2] == 'AP')]
        others = sorted(every[record['lemma']])
        results, why = [], 'no generator derivation'
        entry = entry or {'derivations': []}
        # Where a -μι form also has a thematic derivation, the athematic one is the Attic analysis.
        classed = [d for d in entry['derivations'] if re.search(r'\{(athematic|root)\}', d['stem'])]
        for derivation in classed or entry['derivations']:
            try:
                result = segment(record['word'], record['lemma'], slot, derivation, counterparts, others)
                if result not in results:
                    results.append(result)
            except Skip as skip:
                why = str(skip)
        if len(results) != 1:
            by_hand = manual_cut(record, slot, counterparts, others)
            if by_hand:
                results, manual = [by_hand], manual + 1
                by_hand_keys.add(f"{record['word']}|{record['lemma']}|{family}")
        if len(results) != 1:
            reason = 'derivations disagree' if results else why
            reasons[reason] += 1
            first = entry['derivations'][0] if entry['derivations'] else {'stem': '', 'rule': ''}
            samples[reason].append(f"{record['word']} {slot} {first['stem']} {first['rule']}")
            continue
        cuts[f"{record['word']}|{record['lemma']}|{family}"][slot[4:]] = results[0]
        covered += 1

    # One entry per spelling, verb and tense-voice-mood. Where persons differ
    # (ᾔειν: first singular -ν, third singular movable ν) the key adds the person.
    for key, by_person in cuts.items():
        distinct = [cut for i, cut in enumerate(by_person.values()) if cut not in list(by_person.values())[:i]]
        if len(distinct) == 1:
            segments[key] = distinct[0]
        else:
            for person, cut in by_person.items():
                segments[f'{key}|{person}'] = cut
    segments = dict(sorted(segments.items()))
    body = json.dumps(segments, ensure_ascii=False, separators=(',', ':'))
    (ROOT / 'dist/segments.js').write_text(
        '// Generated by tools/build_segments.py. Unreviewed: see that file for the conventions.\n'
        'export const segments = ' + body + ';\n', encoding='utf-8')
    print(f'Cut {covered} of {len(records)} analyses into pieces ({len(segments)} distinct entries; {manual} analyses from manual stems).')
    for reason, count in reasons.most_common():
        print(f'  left out, {reason}: {count}')
    if skipped_families:
        print('  unsupported families: ' + ', '.join(f'{f} {n}' for f, n in sorted(skipped_families.items())))
    if '--why' in sys.argv:
        for reason, examples in samples.items():
            print(f'== {reason}')
            for example in examples[::max(1, len(examples) // 25)]:
                print('   ' + example)
    if '--manual' in sys.argv:
        for key, pieces in segments.items():
            if '|'.join(key.split('|')[:3]) in by_hand_keys:
                print(key, ' | '.join(f'{t}:{r}' for t, r in pieces))
    if '--list' in sys.argv:
        for key, pieces in segments.items():
            print(key, ' | '.join(f'{t}:{r}' for t, r in pieces))


if __name__ == '__main__':
    main()
