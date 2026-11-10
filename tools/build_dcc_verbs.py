#!/usr/bin/env python3
"""Extract DCC's verb entries without guessing aliases or principal parts."""
import csv
import json
import re
import unicodedata
from pathlib import Path

root = Path(__file__).resolve().parent.parent
with (root / 'data/dcc-greek-core.csv').open(encoding='utf-8-sig', newline='') as source:
    rows = list(csv.DictReader(source))
verbs = []
for row in rows:
    if not row['Part of Speech'].startswith('verb'):
        continue
    headword = unicodedata.normalize('NFC', row['Headword'].strip())
    # The first Greek word is a provisional DCC headword, not a guaranteed
    # dictionary lemma: εἶπον, for example, needs a human-reviewed alias.
    token = re.match(r'^[\u0370-\u03ff\u1f00-\u1fff]+', headword)
    if not token:
        raise ValueError(f'Unexpected headword: {headword!r}')
    verbs.append({'headword': headword, 'candidate': token.group(0),
                  'partOfSpeech': row['Part of Speech'],
                  'frequencyRank': int(row['FREQUENCY RANK'])})
(root / 'data/dcc-verbs.json').write_text(json.dumps(verbs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Extracted {len(verbs)} DCC verb entries from {len(rows)} Greek core entries.')
