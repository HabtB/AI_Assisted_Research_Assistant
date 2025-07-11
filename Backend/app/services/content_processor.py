from typing import List, Dict
import re
from collections import Counter
import logging

logger = logging.getLogger(__name__)

class ContentProcessor:
    def __init__(self):
        self.min_content_length = 100
        self.max_summary_length = 500
        
    def process_content(self, scraped_data: Dict) -> Dict:
        """Process scraped content into structured data"""
        if not scraped_data.get('success') or not scraped_data.get('content'):
            return {
                'url': scraped_data.get('url', ''),
                'title': scraped_data.get('title', 'Unknown'),
                'summary': 'Content could not be retrieved',
                'key_points': [],
                'word_count': 0,
                'relevance_score': 0.0
            }
        
        content = scraped_data['content']
        
        return {
            'url': scraped_data['url'],
            'title': scraped_data['title'],
            'summary': self._generate_summary(content),
            'key_points': self._extract_key_points(content),
            'word_count': len(content.split()),
            'relevance_score': self._calculate_relevance(content)
        }
    
    def _generate_summary(self, content: str) -> str:
        """Generate a simple extractive summary"""
        sentences = self._split_into_sentences(content)
        
        if not sentences:
            return "No content available"
        
        # Take first few sentences as summary
        summary_sentences = sentences[:3]
        summary = ' '.join(summary_sentences)
        
        # Truncate if too long
        if len(summary) > self.max_summary_length:
            summary = summary[:self.max_summary_length] + '...'
        
        return summary
    
    def _extract_key_points(self, content: str) -> List[str]:
        """Extract key points from content"""
        sentences = self._split_into_sentences(content)
        key_points = []
        
        # Simple heuristic: look for sentences with keywords
        keywords = ['important', 'key', 'main', 'essential', 'critical', 'must', 'should', 'need']
        
        for sentence in sentences[:20]:  # Check first 20 sentences
            if any(keyword in sentence.lower() for keyword in keywords):
                key_points.append(sentence.strip())
                if len(key_points) >= 3:
                    break
        
        # If no keyword sentences found, take sentences with numbers/statistics
        if len(key_points) < 2:
            for sentence in sentences[:20]:
                if re.search(r'\d+', sentence):  # Contains numbers
                    key_points.append(sentence.strip())
                    if len(key_points) >= 3:
                        break
        
        return key_points[:3]  # Return top 3 key points
    
    def _calculate_relevance(self, content: str) -> float:
        """Calculate a simple relevance score (0-1)"""
        # Basic relevance based on content length and structure
        word_count = len(content.split())
        
        if word_count < self.min_content_length:
            return 0.2
        elif word_count < 500:
            return 0.5
        elif word_count < 1000:
            return 0.7
        else:
            return 0.9
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        # Filter out very short sentences
        return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def extract_keywords(self, content: str, num_keywords: int = 5) -> List[str]:
        """Extract keywords from content"""
        # Simple keyword extraction based on word frequency
        # Remove common words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
                     'of', 'with', 'by', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 
                     'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
        
        words = re.findall(r'\b[a-z]+\b', content.lower())
        words = [w for w in words if w not in stop_words and len(w) > 3]
        
        word_freq = Counter(words)
        return [word for word, _ in word_freq.most_common(num_keywords)]