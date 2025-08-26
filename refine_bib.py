#!/usr/bin/env python3
"""
BibTeX Reference Optimizer using DBLP API

This script reads a BibTeX file, searches for each entry using DBLP API,
and generates an optimized BibTeX file with updated publication information.
"""

import re
import json
import requests
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus
import argparse


class BibtexEntry:
    """Represents a single BibTeX entry"""
    
    def __init__(self, entry_type: str, cite_key: str, fields: Dict[str, str]):
        self.entry_type = entry_type.lower()
        self.cite_key = cite_key
        self.fields = fields
    
    def get_title(self) -> str:
        """Extract and clean the title"""
        title = self.fields.get('title', '').strip()
        # Remove braces and clean up
        title = re.sub(r'[{}]', '', title)
        title = re.sub(r'\s+', ' ', title).strip()
        return title
    
    def to_bibtex(self) -> str:
        """Convert back to BibTeX format, keeping only essential fields"""
        # Define the fields to keep
        essential_fields = ['author', 'title', 'booktitle', 'journal', 'year', 'pages', 'volume', 'number']
        
        lines = [f"@{self.entry_type}{{{self.cite_key},"]
        
        # Only include essential fields that exist
        for key in essential_fields:
            if key in self.fields and self.fields[key]:
                value = self.fields[key]
                
                # Clean booktitle - remove first comma and everything after it, then balance braces
                if key.lower() == 'booktitle':
                    comma_pos = value.find(',')
                    if comma_pos != -1:
                        value = value[:comma_pos].strip()
                    # Balance braces by adding missing closing braces
                    value = self._balance_braces(value)
                    value = re.sub(r'\s+', ' ', value).strip()
                
                # Ensure proper formatting
                if key.lower() in ['title', 'booktitle', 'journal', 'author']:
                    value = f"{{{value}}}"
                else:
                    # For other fields, add quotes if they contain spaces or special characters
                    if ' ' in str(value) or any(char in str(value) for char in ['-', ':', '/', '.']):
                        value = f"{{{value}}}"
                lines.append(f"  {key} = {value},")
        
        lines.append("}")
        return "\n".join(lines)
    
    def _balance_braces(self, text: str) -> str:
        """Balance braces by removing extra closing braces and adding missing ones"""
        text = text.strip()
        
        # First pass: remove extra closing braces and track unmatched opening braces
        result = []
        brace_count = 0
        
        for char in text:
            if char == '{':
                brace_count += 1
                result.append(char)
            elif char == '}':
                if brace_count > 0:
                    brace_count -= 1
                    result.append(char)
                # Skip extra closing braces (when brace_count is 0)
            else:
                result.append(char)
        
        # Second pass: add missing closing braces at the end
        balanced_text = ''.join(result)
        if brace_count > 0:
            balanced_text += '}' * brace_count
        
        return balanced_text


class BibtexParser:
    """Parser for BibTeX files"""
    
    def parse_file(self, filename: str) -> List[BibtexEntry]:
        """Parse a BibTeX file and return list of entries"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            print(f"Error: File {filename} not found")
            return []
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(filename, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                print(f"Error reading file {filename}: {e}")
                return []
        
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> List[BibtexEntry]:
        """Parse BibTeX content and return list of entries"""
        entries = []
        
        # Pattern to match BibTeX entries
        entry_pattern = r'@(\w+)\s*\{\s*([^,\s]+)\s*,\s*(.*?)\n\s*\}'
        
        for match in re.finditer(entry_pattern, content, re.DOTALL | re.IGNORECASE):
            entry_type = match.group(1)
            cite_key = match.group(2)
            fields_str = match.group(3)
            
            fields = self._parse_fields(fields_str)
            entries.append(BibtexEntry(entry_type, cite_key, fields))
        
        return entries
    
    def _parse_fields(self, fields_str: str) -> Dict[str, str]:
        """Parse the fields section of a BibTeX entry"""
        fields = {}
        
        # Pattern to match field = value pairs
        field_pattern = r'(\w+)\s*=\s*(.+?)(?=,\s*\w+\s*=|$)'
        
        for match in re.finditer(field_pattern, fields_str, re.DOTALL):
            key = match.group(1).strip()
            value = match.group(2).strip()
            
            # Remove trailing comma and whitespace
            value = re.sub(r',\s*$', '', value)
            
            # Remove quotes or braces if they wrap the entire value
            value = re.sub(r'^["\'](.*)["\']$', r'\1', value)
            value = re.sub(r'^\{(.*)\}$', r'\1', value)
            
            fields[key] = value
        
        return fields


class DBLPSearcher:
    """DBLP API searcher"""
    
    BASE_URL = "https://dblp.org/search/publ/api"
    
    def __init__(self, delay: float = 10.0, max_retries: int = 3):
        """Initialize with optional delay between requests and max retries"""
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'BibTeX-Refiner/1.0 (Academic Research Tool)'
        })
        self.max_retries = max_retries
        
    def search_by_title(self, title: str) -> Optional[Dict]:
        """Search DBLP by publication title with retry mechanism"""
        if not title.strip():
            return None
        
        for attempt in range(self.max_retries):
            try:
                # Prepare query - add quotes for exact phrase matching
                query = f'"{title}"'
                params = {
                    'q': query,
                    'format': 'json',
                    'h': 10  # Get more results to find better matches
                }
                
                response = self.session.get(self.BASE_URL, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                # Extract hits
                hits = data.get('result', {}).get('hits', {})
                if isinstance(hits, dict):
                    hit_list = hits.get('hit', [])
                else:
                    hit_list = hits
                
                if not hit_list:
                    # Try without quotes if exact match fails
                    params['q'] = quote_plus(title)
                    response = self.session.get(self.BASE_URL, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    hits = data.get('result', {}).get('hits', {})
                    if isinstance(hits, dict):
                        hit_list = hits.get('hit', [])
                    else:
                        hit_list = hits
                
                if not hit_list:
                    return None
                
                # Filter out arXiv preprints first
                result = None
                if isinstance(hit_list, list):
                    filtered_hits = self._filter_arxiv_hits(hit_list)
                    print(f"  Found {len(hit_list)} total results, {len(filtered_hits)} non-arXiv results")
                    
                    if len(filtered_hits) == 0:
                        print("  All results are arXiv preprints, skipping")
                        result = None
                    elif len(filtered_hits) == 1:
                        print("  Found exactly one non-arXiv result, using it")
                        result = filtered_hits[0]
                    else:
                        print(f"  Found {len(filtered_hits)} non-arXiv results, skipping")
                        result = None
                elif isinstance(hit_list, dict):
                    # Single result - check if it's arXiv
                    if self._is_arxiv_hit(hit_list):
                        print("  Single result is arXiv preprint, skipping")
                        result = None
                    else:
                        result = hit_list
                
                # Rate limiting after successful request
                time.sleep(self.delay)
                return result
            
            except (requests.RequestException, json.JSONDecodeError) as e:
                attempt_num = attempt + 1
                if attempt_num < self.max_retries:
                    print(f"  Attempt {attempt_num} failed: {e}")
                    print(f"  Retrying in {self.delay} seconds... ({attempt_num}/{self.max_retries})")
                    time.sleep(self.delay)
                else:
                    print(f"  All {self.max_retries} attempts failed for '{title}': {e}")
                    return None
        
        return None
    
    def _find_best_title_match(self, original_title: str, hits: List[Dict]) -> Optional[Dict]:
        """Find the hit with the most similar title"""
        original_title_lower = original_title.lower().strip()
        best_match = None
        best_score = 0
        
        for hit in hits:
            info = hit.get('info', {})
            hit_title = info.get('title', '').lower().strip()
            
            if not hit_title:
                continue
            
            # Simple similarity scoring based on word overlap
            original_words = set(original_title_lower.split())
            hit_words = set(hit_title.split())
            
            if len(original_words) == 0:
                continue
            
            # Calculate Jaccard similarity
            intersection = len(original_words.intersection(hit_words))
            union = len(original_words.union(hit_words))
            similarity = intersection / union if union > 0 else 0
            
            # Boost score for exact substring matches
            if original_title_lower in hit_title or hit_title in original_title_lower:
                similarity += 0.5
            
            if similarity > best_score:
                best_score = similarity
                best_match = hit
        
        # Only return match if similarity is reasonably high
        return best_match if best_score > 0.3 else None
    
    def _is_arxiv_hit(self, hit: Dict) -> bool:
        """Check if a hit is an arXiv preprint"""
        info = hit.get('info', {})
        venue = info.get('venue', '')
        
        # Check if venue indicates arXiv
        if isinstance(venue, str):
            return 'arxiv' in venue.lower() or 'corr' in venue.lower()
        elif isinstance(venue, dict):
            venue_text = venue.get('text', '')
            return 'arxiv' in venue_text.lower() or 'corr' in venue_text.lower()
        
        return False
    
    def _filter_arxiv_hits(self, hits: List[Dict]) -> List[Dict]:
        """Filter out arXiv preprints from hits list"""
        return [hit for hit in hits if not self._is_arxiv_hit(hit)]
    
    def download_bibtex_from_dblp(self, hit: Dict, original_cite_key: str) -> Optional['BibtexEntry']:
        """Download BibTeX from DBLP URL and replace cite key"""
        info = hit.get('info', {})
        
        # Get DBLP URL
        dblp_url = info.get('url', '')
        if not dblp_url:
            print("  No DBLP URL found in hit")
            return None
        
        # Construct BibTeX download URL
        bib_url = f"{dblp_url}.bib?param=1"
        print(f"  Downloading BibTeX from: {bib_url}")
        
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(bib_url, timeout=10)
                response.raise_for_status()
                bib_content = response.text
                
                if not bib_content.strip():
                    print("  Empty BibTeX content received")
                    return None
                
                # Parse the downloaded BibTeX
                parser = BibtexParser()
                entries = parser.parse_content(bib_content)
                
                if not entries:
                    print("  Failed to parse downloaded BibTeX")
                    return None
                
                # Take the first entry and replace cite key
                entry = entries[0]
                entry.cite_key = original_cite_key
                
                print(f"  ✓ Successfully downloaded and parsed BibTeX for {original_cite_key}")
                return entry
                
            except requests.RequestException as e:
                attempt_num = attempt + 1
                if attempt_num < self.max_retries:
                    print(f"  Download attempt {attempt_num} failed: {e}")
                    print(f"  Retrying in {self.delay} seconds... ({attempt_num}/{self.max_retries})")
                else:
                    print(f"  All {self.max_retries} download attempts failed for {original_cite_key}: {e}")
                    return None
            except Exception as e:
                print(f"  Error processing BibTeX: {e}")
                return None
        
        return None


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Optimize BibTeX references using DBLP API')
    parser.add_argument('input_file', nargs='?', default='ref_input.bib', 
                       help='Input BibTeX file (default: ref_input.bib)')
    parser.add_argument('output_file', nargs='?', default='ref_output.bib',
                       help='Output BibTeX file (default: ref_output.bib)')
    parser.add_argument('--delay', type=float, default=10.0,
                       help='Delay between API requests in seconds (default: 10.0)')
    
    args = parser.parse_args()
    
    # Initialize components
    parser_obj = BibtexParser()
    searcher = DBLPSearcher(delay=args.delay)
    
    print(f"Reading BibTeX file: {args.input_file}")
    entries = parser_obj.parse_file(args.input_file)
    
    if not entries:
        print("No entries found or failed to parse file")
        return
    
    print(f"Found {len(entries)} entries")
    
    updated_entries = []
    failed_entries = []
    
    for i, entry in enumerate(entries, 1):
        print(f"Processing entry {i}/{len(entries)}: {entry.cite_key}")
        
        title = entry.get_title()
        if not title:
            print(f"  Warning: No title found for {entry.cite_key}")
            failed_entries.append(entry.cite_key)
            updated_entries.append(entry)
            continue
        
        print(f"  Searching for: {title}")
        
        # Search DBLP
        hit = searcher.search_by_title(title)
        
        if hit is None:
            print(f"  No results found for {entry.cite_key}")
            failed_entries.append(entry.cite_key)
            updated_entries.append(entry)
            continue
        
        # Download BibTeX from DBLP
        updated_entry = searcher.download_bibtex_from_dblp(hit, entry.cite_key)
        
        if updated_entry is None:
            print(f"  Failed to download BibTeX for {entry.cite_key}")
            failed_entries.append(entry.cite_key)
            updated_entries.append(entry)
            continue
        
        updated_entries.append(updated_entry)
    
    # Write updated BibTeX file
    print(f"\nWriting updated file: {args.output_file}")
    
    try:
        with open(args.output_file, 'w', encoding='utf-8') as f:
            for entry in updated_entries:
                f.write(entry.to_bibtex())
                f.write("\n\n")
        
        print(f"✓ Successfully wrote {len(updated_entries)} entries to {args.output_file}")
        
    except Exception as e:
        print(f"Error writing output file: {e}")
        return
    
    # Report results
    successful_count = len(updated_entries) - len(failed_entries)
    print(f"\nResults:")
    print(f"  Total entries: {len(entries)}")
    print(f"  Successfully updated: {successful_count}")
    print(f"  Failed: {len(failed_entries)}")
    
    if failed_entries:
        print(f"\nFailed entries:")
        for cite_key in failed_entries:
            print(f"  - {cite_key}")


if __name__ == "__main__":
    main()
