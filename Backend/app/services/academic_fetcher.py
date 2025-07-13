import requests
import pandas as pd
import time
from typing import List, Dict, Optional, Tuple
from xml.etree import ElementTree as ET
from datetime import datetime
import json
from difflib import SequenceMatcher
import re

class EnhancedAcademicFetcher:
    def __init__(self):
        self.sources = {
            "semantic_scholar": self._fetch_semantic_scholar,
            "pubmed": self._fetch_pubmed,
            "arxiv": self._fetch_arxiv,
            "crossref": self._fetch_crossref,
        }
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Academic-Fetcher/1.0[](https://example.com/contact)'
        })

    def fetch_papers(self, query: str, max_results: int = 20, date_from: str = None, 
                    min_citations: int = 0, selected_sources: List[str] = None) -> pd.DataFrame:
        """
        Fetch papers from multiple sources and return as a pandas DataFrame.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            date_from: Filter papers from this year onwards (YYYY format)
            min_citations: Minimum citation count
            selected_sources: List of sources to use (default: all)
            
        Returns:
            DataFrame with paper information
        """
        results = []
        sources_to_use = selected_sources or list(self.sources.keys())
        per_source_limit = max(1, max_results // len(sources_to_use)) + 5  # Fetch extra for deduplication
        
        print(f"🔍 Searching for '{query}' across {len(sources_to_use)} sources...")
        
        for source in sources_to_use:
            fetch_func = self.sources.get(source)
            if fetch_func:
                print(f"  📚 Fetching from {source}...", end='', flush=True)
                try:
                    source_results = fetch_func(query, per_source_limit, date_from, min_citations)
                    results.extend(source_results)
                    print(f" ✓ ({len(source_results)} papers)")
                except Exception as e:
                    print(f" ✗ (Error: {str(e)})")
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(results)
        
        if df.empty:
            print("❌ No results found.")
            return df
        
        # Enhanced deduplication
        df = self._deduplicate_papers(df)
        
        # Filter by citations
        if min_citations > 0:
            df = df[df['citation_count'] >= min_citations]
        
        # Sort by citation count
        df = df.sort_values('citation_count', ascending=False).head(max_results)
        
        # Add additional computed fields
        df['year'] = pd.to_numeric(df['year'], errors='coerce')
        df['has_pdf'] = df['pdf_url'].notna()
        df['source_count'] = df.groupby('normalized_title')['source'].transform('count')
        
        print(f"\n✅ Found {len(df)} unique papers after deduplication and filtering.")
        
        return df.reset_index(drop=True)
    
    def _deduplicate_papers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Enhanced deduplication using DOI and fuzzy title matching."""
        # Normalize titles for comparison
        df['normalized_title'] = df['title'].str.lower().str.replace(r'[^\w\s]', '', regex=True)
        
        # First, deduplicate by DOI
        doi_mask = df['doi'].notna()
        unique_dois = df[doi_mask].drop_duplicates(subset=['doi'])
        no_doi = df[~doi_mask]
        
        # Then, deduplicate remaining papers by fuzzy title matching
        deduped = [unique_dois]
        seen_titles = set(unique_dois['normalized_title'].values)
        
        for _, paper in no_doi.iterrows():
            is_duplicate = False
            for seen_title in seen_titles:
                if self._similar_titles(paper['normalized_title'], seen_title):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                deduped.append(pd.DataFrame([paper]))
                seen_titles.add(paper['normalized_title'])
        
        return pd.concat(deduped, ignore_index=True) if deduped else pd.DataFrame()
    
    def _similar_titles(self, title1: str, title2: str, threshold: float = 0.85) -> bool:
        """Check if two titles are similar using sequence matching."""
        return SequenceMatcher(None, title1, title2).ratio() > threshold
    
    def _fetch_with_retry(self, url: str, params: dict, max_retries: int = 3) -> requests.Response:
        """Fetch URL with exponential backoff retry."""
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=10)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
    
    def filter_papers(self, df: pd.DataFrame, year_range: Tuple[int, int] = None,
                     venues: List[str] = None, min_citations: int = None,
                     has_pdf: bool = None) -> pd.DataFrame:
        """
        Filter papers DataFrame by various criteria.
        
        Args:
            df: Papers DataFrame
            year_range: Tuple of (start_year, end_year)
            venues: List of venue names to include
            min_citations: Minimum citation count
            has_pdf: Whether to filter only papers with PDFs
            
        Returns:
            Filtered DataFrame
        """
        filtered = df.copy()
        
        if year_range:
            filtered = filtered[(filtered['year'] >= year_range[0]) & 
                              (filtered['year'] <= year_range[1])]
        
        if venues:
            filtered = filtered[filtered['venue'].isin(venues)]
        
        if min_citations is not None:
            filtered = filtered[filtered['citation_count'] >= min_citations]
        
        if has_pdf is not None:
            filtered = filtered[filtered['has_pdf'] == has_pdf]
        
        return filtered
    
    def export_results(self, df: pd.DataFrame, filename: str, format: str = 'csv'):
        """
        Export results to file.
        
        Args:
            df: Papers DataFrame
            filename: Output filename
            format: Export format ('csv', 'json', 'excel', 'bibtex')
        """
        if format == 'csv':
            df.to_csv(filename, index=False)
        elif format == 'json':
            df.to_json(filename, orient='records', indent=2)
        elif format == 'excel':
            df.to_excel(filename, index=False, sheet_name='Papers')
        elif format == 'bibtex':
            self._export_bibtex(df, filename)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        print(f"📁 Exported {len(df)} papers to {filename}")
    
    def _export_bibtex(self, df: pd.DataFrame, filename: str):
        """Export papers to BibTeX format."""
        entries = []
        for _, paper in df.iterrows():
            entry_type = "article" if paper.get('venue') else "misc"
            key = re.sub(r'[^\w]', '', paper['title'][:20].lower()) + str(paper.get('year', ''))
            
            entry = f"@{entry_type}{{{key},\n"
            entry += f"  title={{{paper['title']}}},\n"
            
            if paper.get('authors'):
                authors = " and ".join(paper['authors'])
                entry += f"  author={{{authors}}},\n"
            
            if paper.get('year'):
                entry += f"  year={{{paper['year']}}},\n"
            
            if paper.get('venue'):
                entry += f"  journal={{{paper['venue']}}},\n"
            
            if paper.get('doi'):
                entry += f"  doi={{{paper['doi']}}},\n"
            
            if paper.get('pdf_url'):
                entry += f"  url={{{paper['pdf_url']}}},\n"
            
            entry = entry.rstrip(',\n') + "\n}"
            entries.append(entry)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(entries))
    
    def create_summary_report(self, df: pd.DataFrame) -> Dict:
        """Generate a summary report of the fetched papers."""
        report = {
            'total_papers': len(df),
            'date_range': f"{df['year'].min()}-{df['year'].max()}",
            'sources': df['source'].value_counts().to_dict(),
            'top_venues': df['venue'].value_counts().head(10).to_dict(),
            'avg_citations': df['citation_count'].mean(),
            'papers_with_pdf': df['has_pdf'].sum(),
            'top_cited': df.nlargest(5, 'citation_count')[['title', 'citation_count', 'year']].to_dict('records')
        }
        return report
    
    def display_papers(self, df: pd.DataFrame, max_display: int = 10):
        """Display papers in a formatted way."""
        print("\n📊 Paper Results:")
        print("=" * 100)
        
        for idx, paper in df.head(max_display).iterrows():
            print(f"\n{idx + 1}. {paper['title']}")
            print(f"   Authors: {', '.join(paper['authors'][:3])}{'...' if len(paper['authors']) > 3 else ''}")
            print(f"   Year: {paper['year']} | Venue: {paper['venue'] or 'N/A'}")
            print(f"   Citations: {paper['citation_count']} | Source: {paper['source']}")
            
            if paper.get('abstract'):
                abstract = paper['abstract'][:150] + "..." if len(paper['abstract']) > 150 else paper['abstract']
                print(f"   Abstract: {abstract}")
            
            if paper.get('pdf_url'):
                print(f"   📄 PDF: {paper['pdf_url']}")
            
            if paper.get('doi'):
                print(f"   DOI: {paper['doi']}")
            
            print("-" * 100)
        
        if len(df) > max_display:
            print(f"\n... and {len(df) - max_display} more papers")
    
    # [Previous fetch methods remain the same, just add proper error handling]
    def _fetch_semantic_scholar(self, query: str, limit: int, date_from: str = None, min_citations: int = 0) -> List[Dict]:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,venue,abstract,openAccessPdf,citationCount,externalIds",
        }
        if date_from:
            params["year"] = f"{date_from}-"
        try:
            response = self._fetch_with_retry(url, params).json()
            papers = response.get("data", [])
            return [
                {
                    "title": p["title"],
                    "authors": [a["name"] for a in p.get("authors", [])],
                    "year": p.get("year"),
                    "venue": p.get("venue"),
                    "abstract": p.get("abstract"),
                    "pdf_url": p.get("openAccessPdf", {}).get("url") if p.get("openAccessPdf") else None,
                    "citation_count": p.get("citationCount", 0),
                    "source": "semantic_scholar",
                    "doi": p.get("externalIds", {}).get("DOI"),
                }
                for p in papers if p.get("citationCount", 0) >= min_citations
            ]
        except Exception as e:
            raise Exception(f"Semantic Scholar API error: {e}")
    
    def _fetch_pubmed(self, query: str, limit: int, date_from: str = None, min_citations: int = 0) -> List[Dict]:
        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "pubmed", "term": query, "retmax": limit, "retmode": "json"}
        if date_from:
            params["datetype"] = "pdat"
            params["mindate"] = date_from
            params["maxdate"] = "3000"
        try:
            response = self._fetch_with_retry(esearch_url, params).json()
            ids = response.get("esearchresult", {}).get("idlist", [])

            if ids:
                esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
                params = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
                summaries = self._fetch_with_retry(esummary_url, params).json().get("result", {})
                return [
                    {
                        "title": summaries[id].get("title"),
                        "authors": [a["name"] for a in summaries[id].get("authors", [])],
                        "year": summaries[id].get("pubdate", "")[:4],
                        "venue": summaries[id].get("source"),
                        "abstract": "",
                        "pdf_url": None,
                        "citation_count": 0,
                        "source": "pubmed",
                        "doi": summaries[id].get("elocationid", "").replace("doi: ", "") if "doi" in summaries[id].get("elocationid", "") else None,
                    }
                    for id in ids if id in summaries
                ]
            return []
        except Exception as e:
            raise Exception(f"PubMed API error: {e}")

    def _fetch_arxiv(self, query: str, limit: int, date_from: str = None, min_citations: int = 0) -> List[Dict]:
        url = "http://export.arxiv.org/api/query"
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": limit,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }
        if date_from:
            params["search_query"] += f" AND submittedDate:[{date_from}000000 TO *]"
        try:
            response = self._fetch_with_retry(url, params).text
            root = ET.fromstring(response)
            entries = root.findall("{http://www.w3.org/2005/Atom}entry")
            return [
                {
                    "title": e.find("{http://www.w3.org/2005/Atom}title").text.strip(),
                    "authors": [a.text for a in e.findall("{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name")],
                    "year": e.find("{http://www.w3.org/2005/Atom}published").text[:4],
                    "venue": "arXiv",
                    "abstract": e.find("{http://www.w3.org/2005/Atom}summary").text.strip(),
                    "pdf_url": next((l.get("href") for l in e.findall("{http://www.w3.org/2005/Atom}link") 
                                   if l.get("title") == "pdf"), None),
                    "citation_count": 0,
                    "source": "arxiv",
                    "doi": e.find("{http://arxiv.org/schemas/atom}doi").text if e.find("{http://arxiv.org/schemas/atom}doi") is not None else None,
                }
                for e in entries
            ]
        except Exception as e:
            raise Exception(f"arXiv API error: {e}")

    def _fetch_crossref(self, query: str, limit: int, date_from: str = None, min_citations: int = 0) -> List[Dict]:
        url = "https://api.crossref.org/works"
        params = {"query": query, "rows": limit}
        if date_from:
            params["from-pub-date"] = date_from
        try:
            response = self._fetch_with_retry(url, params).json()
            items = response.get("message", {}).get("items", [])
            return [
                {
                    "title": i.get("title", [""])[0],
                    "authors": [f"{a.get('family', '')} {a.get('given', '')}".strip() 
                              for a in i.get("author", [])],
                    "year": i.get("published-print", i.get("published-online", {})).get("date-parts", [[None]])[0][0],
                    "venue": i.get("container-title", [""])[0] if i.get("container-title") else None,
                    "abstract": i.get("abstract", ""),
                    "pdf_url": next((link.get("URL") for link in i.get("link", []) 
                                   if link.get("content-type") == "application/pdf"), None),
                    "citation_count": i.get("is-referenced-by-count", 0),
                    "source": "crossref",
                    "doi": i.get("DOI"),
                }
                for i in items if i.get("is-referenced-by-count", 0) >= min_citations
            ]
        except Exception as e:
            raise Exception(f"CrossRef API error: {e}")


# Example usage with enhanced features
if __name__ == "__main__":
    # Initialize fetcher
    fetcher = EnhancedAcademicFetcher()
    
    # Fetch papers
    papers_df = fetcher.fetch_papers(
        query="transformer neural networks",
        max_results=30,
        date_from="2020",
        min_citations=10
    )
    
    # Display results
    fetcher.display_papers(papers_df)
    
    # Generate and print summary report
    report = fetcher.create_summary_report(papers_df)
    print("\n📈 Summary Report:")
    print(json.dumps(report, indent=2))
    
    # Filter papers from specific venues
    top_venues = ['Nature', 'Science', 'NeurIPS', 'ICML', 'arXiv']
    filtered_df = fetcher.filter_papers(papers_df, venues=top_venues, has_pdf=True)
    
    # Export results
    fetcher.export_results(papers_df, "papers.csv", format="csv")
    fetcher.export_results(filtered_df, "top_papers.json", format="json")
    fetcher.export_results(papers_df.head(10), "references.bib", format="bibtex")