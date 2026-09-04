from typing import List, Dict, Any
from ..blend_engine.request_handler import SearchRequestHandler
from ..blend_engine.result_processor import ResultProcessor
from ..blend_engine.ranking import RankingEngine
from bs4 import BeautifulSoup
import urllib.parse
import asyncio

class FastMode:
    """
    Fast Search Mode for Blend Engine.
    Executes parallel requests to open-web sources (like DDG html) and parses them.
    No Tor, but uses anti-fingerprinting.
    """
    
    def __init__(self):
        self.handler = SearchRequestHandler()
        self.processor = ResultProcessor()
        self.ranker = RankingEngine()
        
    def _build_search_urls(self, query: str) -> List[str]:
        # For now, we query DDG HTML and Qwant as fast sources.
        # Keep fast mode on Blend's lightweight provider path.
        encoded_query = urllib.parse.quote(query)
        return [
            f"https://html.duckduckgo.com/html/?q={encoded_query}",
            f"https://lite.qwant.com/?q={encoded_query}"
        ]
        
    def _parse_ddg(self, html: str) -> List[Dict[str, Any]]:
        """Retrieval Node: WebSignalAgent (DDG). Extracts metadata alongside text."""
        results = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select(".result"):
                link = item.select_one(".result__a")
                if not link:
                    continue
                href = link.get("href", "")
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/l/"):
                    parsed = urllib.parse.urlparse(href)
                    query_params = urllib.parse.parse_qs(parsed.query)
                    href = urllib.parse.unquote(query_params.get("uddg", [""])[0])
                
                title = link.get_text(" ", strip=True)
                snippet_el = item.select_one(".result__snippet")
                snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
                
                if href and title:
                    # Inject Node Metadata
                    metadata = {
                        "freshness_metadata": 1.0, # Default for now
                        "source_node": "DDG_WebSignalAgent"
                    }
                    res = self.processor.format_result(title, href, snippet, source="DDG Fast", metadata=metadata)
                    res['source_confidence'] = 1.0
                    res['signal_strength'] = 1.0
                    results.append(res)
        except Exception:
            pass
        return results

    def _parse_qwant(self, html: str) -> List[Dict[str, Any]]:
        """Retrieval Node: KnowledgeDriftAgent (Qwant). Extracts metadata alongside text."""
        results = []
        try:
            soup = BeautifulSoup(html, "html.parser")
            for item in soup.select(".result"):
                title_el = item.select_one(".result__title")
                url_el = item.select_one(".result__url")
                snippet_el = item.select_one(".result__snippet")
                
                if title_el and url_el:
                    title = title_el.get_text(" ", strip=True)
                    href = url_el.get("href", "") or url_el.get_text(" ", strip=True)
                    if not href.startswith("http"):
                        href = "https://" + href
                    snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
                    
                    # Inject Node Metadata
                    metadata = {
                        "freshness_metadata": 1.0, 
                        "source_node": "Qwant_KnowledgeDriftAgent"
                    }
                    res = self.processor.format_result(title, href, snippet, source="Qwant Fast", metadata=metadata)
                    res['source_confidence'] = 0.8
                    res['signal_strength'] = 0.9
                    results.append(res)
        except Exception:
            pass
        return results

    async def search(self, query: str) -> Dict[str, Any]:
        """
        Execute the fast search using adaptive parallel orchestration.
        """
        urls = self._build_search_urls(query)
        
        # Parallel Async Fetch
        html_responses = await self.handler.execute_parallel_requests(urls, use_tor=False)
        
        # Parallel Async Parsing / Extraction
        parse_tasks = []
        if html_responses[0]:
            parse_tasks.append(asyncio.to_thread(self._parse_ddg, html_responses[0]))
        if len(html_responses) > 1 and html_responses[1]:
            parse_tasks.append(asyncio.to_thread(self._parse_qwant, html_responses[1]))
            
        parsed_results = await asyncio.gather(*parse_tasks)
        
        all_results = []
        for results in parsed_results:
            all_results.extend(results)
            
        # Semantic Fusion and Contradiction Mapping (Deduplicate)
        unique_results = self.processor.deduplicate(all_results)
        
        # Cognitive Ranking
        ranked_results = self.ranker.rank_results(unique_results, query)
        
        return {
            "query": query,
            "number_of_results": len(ranked_results),
            "results": ranked_results,
            "answers": [],
            "suggestions": []
        }
