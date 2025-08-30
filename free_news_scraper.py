"""
Free alternative to BrightData news scraping using NewsAPI
"""

import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from utils import summarize_with_gemini_news_script

load_dotenv()

class FreeNewsScraper:
    """Free news scraper using NewsAPI.org"""
    
    def __init__(self):
        self.api_key = os.getenv('NEWSAPI_KEY')
        self.base_url = "https://newsapi.org/v2/everything"
    
    async def scrape_news(self, topics):
        """Scrape news using NewsAPI (free tier: 100 requests/day)"""
        results = {}
        
        if not self.api_key:
            print("⚠️ NEWSAPI_KEY not found - using mock data")
            return self._create_mock_news(topics)
        
        for topic in topics:
            try:
                # Get articles from last 7 days
                from_date = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
                
                params = {
                    'q': topic,
                    'from': from_date,
                    'sortBy': 'popularity',
                    'pageSize': 10,
                    'language': 'en',
                    'apiKey': self.api_key
                }
                
                response = requests.get(self.base_url, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    articles = data.get('articles', [])
                    
                    if articles:
                        # Combine headlines and descriptions
                        headlines = []
                        for article in articles:
                            title = article.get('title', '')
                            description = article.get('description', '')
                            if title:
                                headlines.append(f"{title}. {description}" if description else title)
                        
                        headlines_text = '\n'.join(headlines)
                        
                        # Summarize with Gemini
                        summary = summarize_with_gemini_news_script(
                            api_key=os.getenv("GEMINI_API_KEY"),
                            headlines=headlines_text
                        )
                        
                        results[topic] = summary
                        print(f"✅ NewsAPI: Found {len(articles)} articles for '{topic}'")
                    else:
                        results[topic] = f"No recent news found for {topic}"
                        print(f"⚠️ NewsAPI: No articles found for '{topic}'")
                
                elif response.status_code == 429:
                    print(f"⚠️ NewsAPI rate limit exceeded")
                    results[topic] = f"Rate limit exceeded for {topic} news"
                    
                else:
                    print(f"❌ NewsAPI error {response.status_code} for '{topic}'")
                    results[topic] = f"Error fetching {topic} news"
                    
            except Exception as e:
                print(f"❌ Error scraping {topic}: {e}")
                results[topic] = f"Error: {str(e)}"
        
        return {"news_analysis": results}
    
    def _create_mock_news(self, topics):
        """Fallback mock news data"""
        mock_news = {}
        for topic in topics:
            mock_news[topic] = f"Recent developments in {topic} continue to evolve. Industry experts are monitoring the situation closely as new information becomes available."
        return {"news_analysis": mock_news}

# Test function
async def test_newsapi():
    """Test NewsAPI functionality"""
    print("🧪 Testing NewsAPI...")
    
    scraper = FreeNewsScraper()
    results = await scraper.scrape_news(["AI", "Climate Change"])
    
    for topic, content in results["news_analysis"].items():
        print(f"\n📰 {topic}:")
        print(f"   {content[:200]}...")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_newsapi())