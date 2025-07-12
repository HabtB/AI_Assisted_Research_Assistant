import requests
from typing import List, Dict

class AcademicFetcher:
    def __init__(self):
        self.sources = {
            "semantic_scholar": self._fetch_semantic_scholar,
            "pubmed": self._fetch_pubmed,
            "arxiv": self._fetch_arxiv,
            "crossref": self._fetch_crossref,
        }

    def fetch_papers(self, query: str, max_results: int, date_from: str = None, min_citations: int = 0, selected_sources: List[str] = None) -> List[Dict]:
        results = []
        sources_to_use = selected_sources or list(self.sources.keys())
        per_source_limit = max(1, max_results // len(sources_to_use))

        for source in sources_to_use:
            fetch_func = self.sources.get(source)
            if fetch_func:
                source_results = fetch_func(query, per_source_limit, date_from, min_citations)
                results.extend(source_results)

        # Deduplicate by title (simple; could use DOI if available)
        seen_titles = set()
        deduped = []
        for paper in results:
            if paper['title'] not in seen_titles:
                seen_titles.add(paper['title'])
                deduped.append(paper)

        # Filter min_citations if available
        deduped = [p for p in deduped if p.get('citation_count', 0) >= min_citations]

        # Sort by citation_count descending
        return sorted(deduped, key=lambda p: p.get('citation_count', 0), reverse=True)[:max_results]

    def _fetch_semantic_scholar(self, query: str, limit: int, date_from: str = None, min_citations: int = 0) -> List[Dict]:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,authors,year,venue,abstract,openAccessPdf,citationCount",
        }
        if date_from:
            params["year"] = f"{date_from}-"
        response = requests.get(url, params=params).json()
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
            }
            for p in papers if p.get("citationCount", 0) >= min_citations
        ]

    def _fetch_pubmed(self, query: str, limit: int, date_from: str = None, min_citations: int = 0) -> List[Dict]:
        # ESearch for IDs
        esearch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db": "pubmed", "term": query, "retmax": limit, "retmode": "json"}
        if date_from:
            params["datetype"] = "pdat"
            params["mindate"] = date_from
            params["maxdate"] = "3000"
        ids = requests.get(esearch_url, params=params).json().get("esearchresult", {}).get("idlist", [])

        # ESummary for details (citations not directly available; approximate with 0 or fetch separately if needed)
        if ids:
            esummary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            params = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
            summaries = requests.get(esummary_url, params=params).json().get("result", {})
            return [
                {
                    "title": summaries[id].get("title"),
                    "authors": [a["name"] for a in summaries[id].get("authors", [])],
                    "year": summaries[id].get("pubdate", "")[:4],
                    "venue": summaries[id].get("source"),
                    "abstract": "",  # PubMed summaries don't include abstract; could use EFetch for full
                    "pdf_url": None,  # PubMed links to PMC if open
                    "citation_count": 0,  # Placeholder; PubMed doesn't provide directly
                    "source": "pubmed",
                }
                for id in ids if id in summaries
            ]
        return []

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
        response = requests.get(url, params=params).text
        # Parse XML (use xml.etree for simplicity; you have it in stdlib)
        from xml.etree import ElementTree as ET
        root = ET.fromstring(response)
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        return [
            {
                "title": e.find("{http://www.w3.org/2005/Atom}title").text,
                "authors": [a.text for a in e.findall("{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name")],
                "year": e.find("{http://www.w3.org/2005/Atom}published").text[:4],
                "venue": "arXiv",
                "abstract": e.find("{http://www.w3.org/2005/Atom}summary").text,
                "pdf_url": [l.get("href") for l in e.findall("{http://www.w3.org/2005/Atom}link") if l.get("title") == "pdf"][0],
                "citation_count": 0,  # arXiv doesn't provide
                "source": "arxiv",
            }
            for e in entries
        ]

    def _fetch_crossref(self, query: str, limit: int, date_from: str = None, min_citations: int = 0) -> List[Dict]:
        url = "https://api.crossref.org/works"
        params = {"query": query, "rows": limit}
        if date_from:
            params["from-pub-date"] = date_from
        response = requests.get(url, params=params).json()
        items = response.get("message", {}).get("items", [])
        return [
            {
                "title": i.get("title", [""])[0],
                "authors": [a.get("family", "") + " " + a.get("given", "") for a in i.get("author", [])],
                "year": i.get("published", {}).get("date-parts", [[0]])[0][0],
                "venue": i.get("container-title", [""])[0],
                "abstract": i.get("abstract", ""),
                "pdf_url": i.get("link", [{}])[0].get("URL") if i.get("link") else None,
                "citation_count": i.get("is-referenced-by-count", 0),
                "source": "crossref",
            }
            for i in items if i.get("is-referenced-by-count", 0) >= min_citations
        ]