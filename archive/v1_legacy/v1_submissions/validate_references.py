import re
import time
from typing import Dict, List, Optional

def parse_ris_entry(entry_text: str) -> Dict[str, str]:
    """Parse a single RIS entry into a dictionary"""
    entry = {}
    for line in entry_text.strip().split('\n'):
        line = line.strip()
        if len(line) >= 6 and line[2:6] == '  - ':
            tag = line[:2]
            value = line[6:]
            if tag in entry:
                if not isinstance(entry[tag], list):
                    entry[tag] = [entry[tag]]
                entry[tag].append(value)
            else:
                entry[tag] = value
    return entry

def parse_bib_entry(entry_text: str) -> Dict[str, str]:
    """Parse a single BIB entry into a dictionary"""
    entry = {}
    # Extract entry type and key
    first_line = entry_text.strip().split('\n')[0]
    match = re.match(r'@(\w+)\{([^,]+)', first_line)
    if match:
        entry['ENTRYTYPE'] = match.group(1)
        entry['ID'] = match.group(2)

    # Extract fields
    for line in entry_text.split('\n'):
        line = line.strip()
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if value.startswith('{') and value.endswith('}'):
                value = value[1:-1]
            elif value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            entry[key] = value

    return entry

def search_for_doi(title: str, authors: List[str], year: str) -> Optional[str]:
    """Search for DOI using title, authors, and year"""
    # Create search query
    author_str = ' '.join(authors[:2]) if authors else ''  # Use first 2 authors
    _query = f'"{title}" {author_str} {year} DOI'

    # This would use a web search tool - for now return None
    # In a real implementation, we'd use tools like fetch_webpage or semantic_search
    return None

def validate_and_enhance_reference(ris_entry: Dict, bib_entry: Dict) -> tuple[Dict, Dict]:
    """Validate and enhance a single reference with DOI/URL if possible"""
    enhanced_ris = ris_entry.copy()
    enhanced_bib = bib_entry.copy()

    title = ris_entry.get('T1') or ris_entry.get('TI', '')
    authors = ris_entry.get('AU', [])
    if isinstance(authors, str):
        authors = [authors]
    year = ris_entry.get('PY', '')

    # Try to find DOI
    doi = search_for_doi(title, authors, year)
    if doi:
        enhanced_ris['DO'] = doi
        enhanced_bib['doi'] = doi

    # Add URL if we can construct one (for common journals)
    _journal = ris_entry.get('JO', '').lower()
    if 'doi' in enhanced_ris:
        url = f"https://doi.org/{enhanced_ris['DO']}"
        enhanced_ris['UR'] = url
        enhanced_bib['url'] = url

    return enhanced_ris, enhanced_bib

def format_ris_entry(entry: Dict) -> str:
    """Format a RIS entry dictionary back to RIS format"""
    lines = []
    for tag, value in entry.items():
        if isinstance(value, list):
            for v in value:
                lines.append(f"{tag}  - {v}")
        else:
            lines.append(f"{tag}  - {value}")
    return '\n'.join(lines) + '\nER'

def format_bib_entry(entry: Dict) -> str:
    """Format a BIB entry dictionary back to BIB format"""
    lines = []
    entry_type = entry.get('ENTRYTYPE', 'article')
    entry_id = entry.get('ID', 'unknown')

    lines.append(f"@{entry_type}{{{entry_id},")

    for key, value in entry.items():
        if key not in ['ENTRYTYPE', 'ID']:
            lines.append(f"  {key} = {{{value}}}")

    lines.append("}")
    return '\n'.join(lines)

def main():
    # Read deduplicated files
    with open('references_deduplicated.ris', 'r', encoding='utf-8') as f:
        ris_content = f.read()

    with open('references_deduplicated.bib', 'r', encoding='utf-8') as f:
        bib_content = f.read()

    # Parse entries
    ris_entries_text = re.split(r'\n\s*\n', ris_content.strip())
    bib_entries_text = re.split(r'\n\s*\n', bib_content.strip())

    print(f"Processing {len(ris_entries_text)} RIS entries and {len(bib_entries_text)} BIB entries")

    enhanced_ris_entries = []
    enhanced_bib_entries = []

    for i, (ris_text, bib_text) in enumerate(zip(ris_entries_text, bib_entries_text)):
        if not ris_text.strip() or not bib_text.strip():
            continue

        print(f"Processing entry {i+1}...")

        # Parse entries
        ris_entry = parse_ris_entry(ris_text)
        bib_entry = parse_bib_entry(bib_text)

        # Validate and enhance
        enhanced_ris, enhanced_bib = validate_and_enhance_reference(ris_entry, bib_entry)

        # Format back
        enhanced_ris_entries.append(format_ris_entry(enhanced_ris))
        enhanced_bib_entries.append(format_bib_entry(enhanced_bib))

        # Small delay to be respectful
        time.sleep(0.1)

    # Save enhanced files
    with open('references_validated.ris', 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(enhanced_ris_entries))

    with open('references_validated.bib', 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(enhanced_bib_entries))

    print("Created references_validated.ris and references_validated.bib")

if __name__ == "__main__":
    main()