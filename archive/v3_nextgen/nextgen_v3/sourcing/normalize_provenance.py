import pandas as pd
import json
import bibtexparser
import os

def from_csl_json(path):
    """Ingest CSL-JSON and extract citations."""
    with open(path, 'r') as f:
        data = json.load(f)
    citations = []
    for item in data:
        source_id = item.get('id', f"csl_{len(citations)}")
        citation = item.get('title', 'Unknown')
        url = item.get('URL', '')
        citations.append({'source_id': source_id, 'citation': citation, 'url': url})
    return pd.DataFrame(citations)

def from_bibtex(path):
    """Ingest BibTeX and extract citations."""
    with open(path, 'r') as f:
        bib_db = bibtexparser.load(f)
    citations = []
    for entry in bib_db.entries:
        source_id = entry.get('ID', f"bib_{len(citations)}")
        citation = entry.get('title', 'Unknown')
        url = entry.get('url', '')
        citations.append({'source_id': source_id, 'citation': citation, 'url': url})
    return pd.DataFrame(citations)

def from_doi_list(path):
    """Ingest DOI list."""
    with open(path, 'r') as f:
        dois = f.read().splitlines()
    citations = []
    for doi in dois:
        source_id = doi.replace('/', '_')
        citation = f"DOI: {doi}"
        url = f"https://doi.org/{doi}"
        citations.append({'source_id': source_id, 'citation': citation, 'url': url})
    return pd.DataFrame(citations)

def write_provenance(df, output_path='../data_schemas/provenance_sources.csv'):
    # Append to existing file if it exists
    if os.path.exists(output_path):
        existing = pd.read_csv(output_path)
        df = pd.concat([existing, df], ignore_index=True)
    df.to_csv(output_path, index=False)