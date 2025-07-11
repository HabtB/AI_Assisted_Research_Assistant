from typing import List, Dict, Optional, Protocol
from abc import ABC, abstractmethod
import os
from dotenv import load_dotenv
import logging
import json

# AI Provider imports
import openai
import google.generativeai as genai
from groq import Groq

load_dotenv()
logger = logging.getLogger(__name__)

class AIProvider(ABC):
    """Abstract base class for AI providers"""
    
    @abstractmethod
    async def analyze_content(self, query: str, contents: List[Dict]) -> Dict:
        """Analyze scraped content and return insights"""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured"""
        pass

class OpenAIProvider(AIProvider):
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if self.api_key:
            openai.api_key = self.api_key
            self.client = openai.OpenAI(api_key=self.api_key)
        self.model = "gpt-4-turbo-preview"  # or "gpt-3.5-turbo" for cheaper
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def analyze_content(self, query: str, contents: List[Dict]) -> Dict:
        try:
            # Prepare content for analysis
            source_texts = []
            for idx, content in enumerate(contents[:5]):  # Limit to 5 sources
                source_texts.append(f"""
Source {idx + 1}: {content.get('title', 'Unknown')}
URL: {content.get('url', '')}
Content: {content.get('content', '')[:2000]}  # Limit content length
---""")
            
            prompt = f"""
You are an expert research analyst. Analyze the following sources about "{query}" and provide:

1. A comprehensive summary (2-3 paragraphs)
2. Key findings (5-7 bullet points)
3. Common themes across sources
4. Any contradictions or debates
5. Actionable insights or recommendations

Sources:
{''.join(source_texts)}

Provide your analysis in JSON format with keys: summary, key_findings, themes, contradictions, recommendations.
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research analyst providing structured analysis."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"OpenAI analysis completed for query: {query}")
            return result
            
        except Exception as e:
            logger.error(f"OpenAI analysis failed: {str(e)}")
            return self._fallback_analysis(query, contents)

    def _fallback_analysis(self, query: str, contents: List[Dict]) -> Dict:
        """Fallback analysis if AI fails"""
        return {
            "summary": f"Analysis of {len(contents)} sources about {query}. Content extracted successfully but AI analysis unavailable.",
            "key_findings": ["AI analysis temporarily unavailable"],
            "themes": ["Unable to extract themes"],
            "contradictions": ["Unable to identify contradictions"],
            "recommendations": ["Manual review recommended"]
        }

class GeminiProvider(AIProvider):
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def analyze_content(self, query: str, contents: List[Dict]) -> Dict:
        try:
            # Prepare content
            source_texts = []
            for idx, content in enumerate(contents[:5]):
                source_texts.append(f"""
Source {idx + 1}: {content.get('title', 'Unknown')}
Content: {content.get('content', '')[:2000]}
---""")
            
            prompt = f"""
Analyze these sources about "{query}" and provide a research report with:

1. Summary: Comprehensive 2-3 paragraph summary
2. Key Findings: 5-7 important discoveries
3. Themes: Common themes across sources
4. Contradictions: Any conflicting information
5. Recommendations: Actionable insights

Sources:
{''.join(source_texts)}

Format your response as valid JSON with these exact keys: summary, key_findings (array), themes (array), contradictions (array), recommendations (array).
"""
            
            response = self.model.generate_content(prompt)
            
            # Parse response - Gemini might not always return valid JSON
            try:
                # Try to extract JSON from response
                text = response.text
                # Find JSON in response
                import re
                json_match = re.search(r'\{.*\}', text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                else:
                    # Fallback parsing
                    result = self._parse_gemini_response(text)
            except:
                result = self._parse_gemini_response(response.text)
            
            logger.info(f"Gemini analysis completed for query: {query}")
            return result
            
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            return self._fallback_analysis(query, contents)
    
    def _parse_gemini_response(self, text: str) -> Dict:
        """Parse non-JSON Gemini response"""
        # Basic parsing logic
        return {
            "summary": text[:500] if len(text) > 500 else text,
            "key_findings": ["Parsed from Gemini response"],
            "themes": ["Unable to parse themes"],
            "contradictions": ["Unable to parse contradictions"],
            "recommendations": ["Review full response"]
        }
    
    def _fallback_analysis(self, query: str, contents: List[Dict]) -> Dict:
        return {
            "summary": f"Analysis of {len(contents)} sources about {query}.",
            "key_findings": ["Analysis unavailable"],
            "themes": [],
            "contradictions": [],
            "recommendations": []
        }

class GroqProvider(AIProvider):
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        self.model = "llama3-8b-8192"  # Fast and good quality
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    async def analyze_content(self, query: str, contents: List[Dict]) -> Dict:
        try:
            source_texts = []
            for idx, content in enumerate(contents[:5]):
                source_texts.append(f"""
Source {idx + 1}: {content.get('title', 'Unknown')}
Content: {content.get('content', '')[:1500]}
---""")
            
            prompt = f"""
Analyze these sources about "{query}" and provide a structured research report.

Sources:
{''.join(source_texts)}

Provide your analysis as valid JSON with these keys:
- summary: string (2-3 paragraphs)
- key_findings: array of strings (5-7 findings)
- themes: array of strings (common themes)
- contradictions: array of strings (conflicting info)
- recommendations: array of strings (actionable insights)
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research analyst. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Groq analysis completed for query: {query}")
            return result
            
        except Exception as e:
            logger.error(f"Groq analysis failed: {str(e)}")
            return self._fallback_analysis(query, contents)
    
    def _fallback_analysis(self, query: str, contents: List[Dict]) -> Dict:
        return {
            "summary": f"Analysis of {len(contents)} sources about {query}.",
            "key_findings": ["Analysis unavailable"],
            "themes": [],
            "contradictions": [],
            "recommendations": []
        }

class AIAnalyzer:
    """Main AI analyzer that manages multiple providers"""
    
    def __init__(self, preferred_provider: str = "groq"):
        self.providers = {
            "openai": OpenAIProvider(),
            "gemini": GeminiProvider(), 
            "groq": GroqProvider()
        }
        self.preferred_provider = preferred_provider
        
    def get_available_providers(self) -> List[str]:
        """Get list of configured providers"""
        return [name for name, provider in self.providers.items() if provider.is_configured()]
    
    async def analyze_research(self, query: str, contents: List[Dict], provider_name: Optional[str] = None) -> Dict:
        """Analyze research using specified or preferred provider"""
        
        # Use specified provider or preferred
        provider_name = provider_name or self.preferred_provider
        
        # Get available providers
        available = self.get_available_providers()
        
        if not available:
            logger.warning("No AI providers configured. Using basic analysis.")
            return self._basic_analysis(query, contents)
        
        # Try preferred provider first
        if provider_name in available:
            provider = self.providers[provider_name]
            logger.info(f"Using {provider_name} for analysis")
            return await provider.analyze_content(query, contents)
        
        # Fallback to first available provider
        fallback_name = available[0]
        logger.info(f"Preferred provider {provider_name} not available. Using {fallback_name}")
        provider = self.providers[fallback_name]
        return await provider.analyze_content(query, contents)
    
    def _basic_analysis(self, query: str, contents: List[Dict]) -> Dict:
        """Basic analysis without AI"""
        summaries = [c.get('summary', '') for c in contents if c.get('summary')]
        
        return {
            "summary": f"Research on '{query}' analyzed {len(contents)} sources. " + 
                      " ".join(summaries[:2])[:500],
            "key_findings": [
                f"Found {len(contents)} relevant sources",
                f"Topics cover various aspects of {query}",
                "Further analysis recommended"
            ],
            "themes": ["Multiple perspectives found"],
            "contradictions": ["Unable to analyze without AI"],
            "recommendations": ["Configure AI provider for better analysis"],
            "provider_used": "basic"
        }