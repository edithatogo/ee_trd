import re
from typing import Dict

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

def main():
    # Read validated file
    with open('references_validated.ris', 'r', encoding='utf-8') as f:
        ris_content = f.read()

    # Parse entries
    ris_entries_text = re.split(r'\n\s*\n', ris_content.strip())

    print(f"Found {len(ris_entries_text)} references")
    print("\nReferences without DOIs (need manual DOI search):")
    print("=" * 80)

    missing_doi_count = 0
    for i, ris_text in enumerate(ris_entries_text):
        if not ris_text.strip():
            continue

        entry = parse_ris_entry(ris_text)

        # Check if DOI exists
        if 'DO' not in entry:
            missing_doi_count += 1
            title = entry.get('T1') or entry.get('TI', 'Unknown Title')
            authors = entry.get('AU', [])
            if isinstance(authors, str):
                authors = [authors]
            year = entry.get('PY', 'Unknown Year')
            journal = entry.get('JO', 'Unknown Journal')

            print(f"\nReference {i+1}:")
            print(f"Title: {title}")
            print(f"Authors: {', '.join(authors[:3])}{' et al.' if len(authors) > 3 else ''}")
            print(f"Year: {year}")
            print(f"Journal: {journal}")
            print(f"Search Query: \"{title}\" {' '.join(authors[:2])} {year} DOI")

    print(f"\nSummary: {missing_doi_count} out of {len(ris_entries_text)} references are missing DOIs")

if __name__ == "__main__":
    main()