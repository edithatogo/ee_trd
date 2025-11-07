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

def main():
    # Known DOIs found through search
    known_dois = {
        "Acute and longer-term outcomes in depressed outpatients requiring one or several treatment steps: a STAR*D report": "10.1176/ajp.2006.163.11.1905",
        "Psilocybin produces substantial and sustained decreases in depression and anxiety in patients with life-threatening cancer: a randomized double-blind trial": "10.1177/0269881116675513",
        "Efficacy and safety of intranasal esketamine adjunctive to oral antidepressant therapy in treatment-resistant depression: a randomized clinical trial": "10.1001/jamapsychiatry.2017.3739",
        "Antidepressant effects of ketamine in depressed patients": "10.1016/S0006-3223(99)00230-9",
        "Diagnosis and definition of treatment-resistant depression": "10.1016/S0006-3223(03)00231-2",
        "Intravenous esketamine in adult treatment-resistant depression: a double-blind, double-randomization, placebo-controlled study": "10.1016/j.biopsych.2015.10.018",
        "Efficacy and safety of electroconvulsive therapy in depressive disorders: a systematic review and meta-analysis": "10.1016/S0140-6736(03)12705-5",
        "EuroQol—a new facility for the measurement of health-related quality of life": "10.1016/0168-8510(90)90421-9",
        "Consolidated Health Economic Evaluation Reporting Standards (CHEERS) statement": "10.1136/bmj.f1049",
        # Add more DOIs as they are found
    }

    # Read validated file
    with open('references_validated.ris', 'r', encoding='utf-8') as f:
        ris_content = f.read()

    # Parse entries
    ris_entries_text = re.split(r'\n\s*\n', ris_content.strip())

    print(f"Processing {len(ris_entries_text)} references...")

    updated_entries = []
    updated_count = 0

    for ris_text in ris_entries_text:
        if not ris_text.strip():
            continue

        entry = parse_ris_entry(ris_text)
        title = entry.get('T1') or entry.get('TI', '')

        # Check if we have a DOI for this title
        if title in known_dois and 'DO' not in entry:
            entry['DO'] = known_dois[title]
            # Add URL if DOI exists
            entry['UR'] = f"https://doi.org/{known_dois[title]}"
            updated_count += 1
            print(f"Added DOI to: {title[:50]}...")

        updated_entries.append(format_ris_entry(entry))

    # Save updated file
    with open('references_validated.ris', 'w', encoding='utf-8') as f:
        f.write('\n\n'.join(updated_entries))

    print(f"Updated {updated_count} references with DOIs")

if __name__ == "__main__":
    main()