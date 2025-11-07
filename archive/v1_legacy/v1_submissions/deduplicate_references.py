import re

def normalize_text(text):
    """Normalize text for comparison"""
    if not text:
        return ''
    return re.sub(r'[^a-zA-Z0-9]', '', text.lower())

def parse_ris_entries(content):
    """Parse RIS content into individual entries"""
    entries = []
    current_entry = []

    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('TY'):
            if current_entry:
                entries.append('\n'.join(current_entry))
                current_entry = []
        current_entry.append(line)

    if current_entry:
        entries.append('\n'.join(current_entry))

    return entries

def parse_bib_entries(content):
    """Parse BIB content into individual entries"""
    entries = []
    current_entry = []
    in_entry = False

    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('@'):
            if current_entry:
                entries.append('\n'.join(current_entry))
                current_entry = []
            in_entry = True
        elif line == '}' and in_entry:
            current_entry.append(line)
            entries.append('\n'.join(current_entry))
            current_entry = []
            in_entry = False
        elif in_entry:
            current_entry.append(line)

    if current_entry:
        entries.append('\n'.join(current_entry))

    return entries

def extract_ris_key(entry):
    """Extract key information from RIS entry for deduplication"""
    title = ''
    authors = []
    year = ''

    for line in entry.split('\n'):
        if line.startswith('T1') or line.startswith('TI'):
            title = line[6:].strip()
        elif line.startswith('AU'):
            authors.append(line[6:].strip())
        elif line.startswith('PY'):
            year = line[6:].strip()

    return {
        'title': normalize_text(title),
        'authors': sorted([normalize_text(a) for a in authors]),
        'year': year
    }

def extract_bib_key(entry):
    """Extract key information from BIB entry for deduplication"""
    title = ''
    authors = []
    year = ''

    for line in entry.split('\n'):
        if 'title=' in line:
            title_match = re.search(r'title\s*=\s*[\{"]((?:[^"]*?(?:et al\.)?[^"]*?))[\}"]', line, re.IGNORECASE)
            if title_match:
                title = title_match.group(1)
        elif 'author=' in line:
            author_match = re.search(r'author\s*=\s*[\{"]((?:[^"]*?(?:et al\.)?[^"]*?))[\}"]', line, re.IGNORECASE)
            if author_match:
                authors.extend([a.strip() for a in author_match.group(1).split(' and ')])
        elif 'year=' in line:
            year_match = re.search(r'year\s*=\s*[\{"]?(\d{4})[\}"]?', line, re.IGNORECASE)
            if year_match:
                year = year_match.group(1)

    return {
        'title': normalize_text(title),
        'authors': sorted([normalize_text(a) for a in authors]),
        'year': year
    }

# Read combined files
with open('all_references_combined.ris', 'r', encoding='utf-8') as f:
    ris_content = f.read()

with open('all_references_combined.bib', 'r', encoding='utf-8') as f:
    bib_content = f.read()

# Parse entries
ris_entries = parse_ris_entries(ris_content)
bib_entries = parse_bib_entries(bib_content)

print(f'Found {len(ris_entries)} RIS entries and {len(bib_entries)} BIB entries')

# Deduplicate RIS entries
ris_seen = set()
deduplicated_ris = []

for entry in ris_entries:
    key = extract_ris_key(entry)
    key_tuple = (key['title'], tuple(key['authors']), key['year'])

    if key_tuple not in ris_seen:
        ris_seen.add(key_tuple)
        deduplicated_ris.append(entry)

# Deduplicate BIB entries
bib_seen = set()
deduplicated_bib = []

for entry in bib_entries:
    key = extract_bib_key(entry)
    key_tuple = (key['title'], tuple(key['authors']), key['year'])

    if key_tuple not in bib_seen:
        bib_seen.add(key_tuple)
        deduplicated_bib.append(entry)

print(f'After deduplication: {len(deduplicated_ris)} RIS entries and {len(deduplicated_bib)} BIB entries')

# Save deduplicated files
with open('references_deduplicated.ris', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(deduplicated_ris))

with open('references_deduplicated.bib', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(deduplicated_bib))

print('Created references_deduplicated.ris and references_deduplicated.bib')