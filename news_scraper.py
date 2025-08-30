import asyncio
import os
from typing import Dict, List

from aiolimiter import AsyncLimiter
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from utils import (
    generate_news_urls_to_scrape,
    scrape_with_brightdata,
    clean_html_to_text,
    extract_headlines,
    summarize_with_gemini_news_script,
    summarize_with_ollama
)

load_dotenv()


class NewsScraper:
    _rate_limiter = AsyncLimiter(5, 1)  # 5 requests/second

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def scrape_news(self, topics: List[str]) -> Dict[str, str]:
        """Scrape and analyze news articles"""
        results = {}
        
        for topic in topics:
            async with self._rate_limiter:
                try:
                    urls = generate_news_urls_to_scrape([topic])
                    search_html = scrape_with_brightdata(urls[topic])
                    clean_text = clean_html_to_text(search_html)
                    headlines = extract_headlines(clean_text)

                    # ✅ Try Gemini first, then fallback to Ollama
                    try:
                        summary = summarize_with_gemini_news_script(
                            api_key=os.getenv("GEMINI_API_KEY"),
                            headlines=headlines
                        )
                    except Exception as e:
                        print(f"⚠️ Gemini failed for topic '{topic}': {e}")
                        summary = summarize_with_ollama(headlines=headlines)

                    results[topic] = summary
                except Exception as e:
                    results[topic] = f"Error: {str(e)}"
                await asyncio.sleep(1)  # Avoid overwhelming news sites

        return {"news_analysis": results}