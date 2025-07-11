import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import time
from urllib.parse import urlparse, quote
import logging
from trafilatura import fetch_url, extract
import json

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.timeout = 10.0
        self.rate_limit_delay = 1.0  # Respectful delay between requests
        
    async def search_web(self, query: str, num_results: int = 5) -> List[Dict]:
        """Search the web using DuckDuckGo (no API key needed)"""
        results = []
        
        try:
            # Use DuckDuckGo HTML version for scraping
            search_url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    search_url,
                    headers=self.headers,
                    timeout=self.timeout,
                    follow_redirects=True
                )
                response.raise_for_status()
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find search results
            for i, result in enumerate(soup.find_all('div', class_='web-result')[:num_results]):
                title_elem = result.find('h2')
                link_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem and link_elem:
                    results.append({
                        'title': title_elem.get_text(strip=True),
                        'url': link_elem.get('href', ''),
                        'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                    })
                    
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            # Fallback to predefined educational sources
            results = self._get_fallback_sources(query)
            
        return results
    
    async def scrape_content(self, url: str) -> Optional[Dict]:
        """Scrape content from a URL using multiple methods"""
        try:
            # Add delay for respectful scraping
            time.sleep(self.rate_limit_delay)
            
            # Method 1: Try trafilatura first (best for article extraction)
            html = fetch_url(url)
            if html:
                content = extract(html, include_comments=False, include_tables=False)
                if content:
                    return {
                        'url': url,
                        'content': content,
                        'title': self._extract_title_from_html(html),
                        'success': True
                    }
            
            # Method 2: Fallback to BeautifulSoup
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    follow_redirects=True
                )
                response.raise_for_status()
                
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
                
            # Extract text content
            content = self._extract_content_from_soup(soup)
            title = soup.find('title').get_text() if soup.find('title') else urlparse(url).netloc
            
            return {
                'url': url,
                'content': content,
                'title': title,
                'success': True
            }
            
        except Exception as e:
            logger.error(f"Scraping error for {url}: {str(e)}")
            return {
                'url': url,
                'content': f"Failed to scrape: {str(e)}",
                'title': urlparse(url).netloc,
                'success': False
            }
    
    def _extract_content_from_soup(self, soup: BeautifulSoup) -> str:
        """Extract main content from BeautifulSoup object"""
        # Try to find main content areas
        content_areas = [
            soup.find('main'),
            soup.find('article'),
            soup.find('div', class_='content'),
            soup.find('div', class_='main'),
            soup.find('div', id='content'),
        ]
        
        for area in content_areas:
            if area:
                return area.get_text(separator='\n', strip=True)
        
        # Fallback to body
        body = soup.find('body')
        if body:
            return body.get_text(separator='\n', strip=True)
        
        return ""
    
    def _extract_title_from_html(self, html: str) -> str:
        """Extract title from HTML string"""
        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('title')
        return title_tag.get_text(strip=True) if title_tag else "Untitled"
    
    def _get_fallback_sources(self, query: str) -> List[Dict]:
        """Provide fallback sources when search fails"""
        # Educational and reliable sources for common topics
        sources = {
            'python': [
                {'title': 'Python.org', 'url': 'https://www.python.org/', 'snippet': 'Official Python documentation'},
                {'title': 'Real Python', 'url': 'https://realpython.com/', 'snippet': 'Python tutorials and articles'},
            ],
            'javascript': [
                {'title': 'MDN Web Docs', 'url': 'https://developer.mozilla.org/', 'snippet': 'Mozilla Developer Network'},
                {'title': 'JavaScript.info', 'url': 'https://javascript.info/', 'snippet': 'Modern JavaScript Tutorial'},
            ],
            'default': [
                {'title': 'Wikipedia', 'url': f'https://en.wikipedia.org/wiki/{quote(query)}', 'snippet': 'Wikipedia article'},
                {'title': 'Google Scholar', 'url': f'https://scholar.google.com/scholar?q={quote(query)}', 'snippet': 'Academic papers'},
            ]
        }
        
        # Check if query matches any predefined topic
        for topic, urls in sources.items():
            if topic.lower() in query.lower():
                return urls[:3]
        
        return sources['default']