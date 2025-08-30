from fastapi import FastAPI, HTTPException, Response
from pathlib import Path
from dotenv import load_dotenv
import traceback   
import os
from models import NewsRequest
from utils import tts_to_audio, generate_broadcast_news
from reddit_scraper import scrape_reddit_topics

app = FastAPI()
load_dotenv()


async def get_news_data(topics):
    """Get news data from available sources - no mock data fallback"""
    
    # Priority 1: BrightData (most comprehensive)
    if os.getenv('BRIGHTDATA_API_KEY') and os.getenv('BRIGHTDATA_WEB_UNLOCKER_ZONE'):
        print("🌐 Using BrightData for news scraping...")
        try:
            from news_scraper import NewsScraper
            news_scraper = NewsScraper()
            return await news_scraper.scrape_news(topics)
        except Exception as e:
            print(f"❌ BrightData failed: {e}")
            # Fall through to next option
    
    # Priority 2: NewsAPI (free but limited)  
    if os.getenv('NEWSAPI_KEY'):
        print("📡 Using NewsAPI for news scraping...")
        try:
            from free_news_scraper import FreeNewsScraper
            news_scraper = FreeNewsScraper()
            return await news_scraper.scrape_news(topics)
        except Exception as e:
            print(f"❌ NewsAPI failed: {e}")
            # No more fallbacks - raise error
    
    # No valid news sources configured
    raise HTTPException(
        status_code=503, 
        detail="No valid news sources configured. Please set up BRIGHTDATA_API_KEY + BRIGHTDATA_WEB_UNLOCKER_ZONE or NEWSAPI_KEY"
    )


@app.post("/generate-news-audio")
async def generate_news_audio(request: NewsRequest):
    try:
        print(f"🚀 Starting audio generation for topics: {request.topics}")
        print(f"📊 Source type: {request.source_type}")
        
        results = {}
        
        # Handle news data
        if request.source_type in ["news", "both"]:
            print("📰 Collecting news data...")
            results["news"] = await get_news_data(request.topics)
            
            news_analysis = results["news"].get("news_analysis", {})
            print(f"✅ News data collected for {len(news_analysis)} topics")
        
        # Handle Reddit data  
        if request.source_type in ["reddit", "both"]:
            print("💬 Collecting Reddit data...")
            try:
                results["reddit"] = await scrape_reddit_topics(request.topics)
                reddit_analysis = results["reddit"].get("reddit_analysis", {})
                print(f"✅ Reddit data collected for {len(reddit_analysis)} topics")
            except Exception as e:
                print(f"❌ Reddit collection failed: {e}")
                results["reddit"] = {}
        
        # Check if we have any data at all
        news_data = results.get("news", {})
        reddit_data = results.get("reddit", {})
        
        if not news_data and not reddit_data:
            raise HTTPException(
                status_code=503, 
                detail="Unable to collect any data from configured sources"
            )
        
        print("🤖 Generating broadcast script with Gemini...")
        
        news_summary = generate_broadcast_news(
            api_key=os.getenv("GEMINI_API_KEY"),
            news_data=news_data,
            reddit_data=reddit_data,
            topics=request.topics
        )
        
        if news_summary:
            print(f"✅ Script generated: {len(news_summary)} characters")
        else:
            raise HTTPException(status_code=500, detail="Failed to generate news script")

        print("🎵 Generating audio...")
        audio_path = tts_to_audio(text=news_summary)
        print("✅ Audio generated successfully")

        if audio_path and Path(audio_path).exists():
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()

            return Response(
                content=audio_bytes,
                media_type="audio/mpeg",
                headers={"Content-Disposition": "attachment; filename=news-summary.mp3"}
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to generate audio file")
    
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check with news source detection"""
    features = []
    news_source = None
    
    # Detect news sources
    if os.getenv('BRIGHTDATA_API_KEY') and os.getenv('BRIGHTDATA_WEB_UNLOCKER_ZONE'):
        news_source = "brightdata"
        features.append("real_news_brightdata")
    elif os.getenv('NEWSAPI_KEY'):
        news_source = "newsapi"
        features.append("real_news_newsapi")
    else:
        news_source = "none_configured"
        features.append("no_news_source")
    
    # Other features
    if os.getenv('API_TOKEN') and os.getenv('WEB_UNLOCKER_ZONE'):
        features.append("reddit_scraping")
    
    if os.getenv('GEMINI_API_KEY'):
        features.append("gemini_ai")
    
    status = "healthy" if news_source != "none_configured" else "degraded"
    
    return {
        "status": status,
        "message": "NewsNinja Backend is running" if status == "healthy" else "NewsNinja Backend - No news sources configured",
        "news_source": news_source,
        "features": features,
        "setup_instructions": {
            "brightdata": "Add BRIGHTDATA_API_KEY + BRIGHTDATA_WEB_UNLOCKER_ZONE for premium news",
            "newsapi": "Add NEWSAPI_KEY for free news (100 requests/day)",
            "reddit": "Add API_TOKEN + WEB_UNLOCKER_ZONE for Reddit data"
        }
    }


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting NewsNinja Backend (No Mock Data)...")
    print("📰 News Sources: BrightData > NewsAPI > ERROR")
    print("💬 Reddit: Available if configured")
    print("🤖 AI: Gemini")
    print("🎵 TTS: gTTS")
    uvicorn.run(
        "flexible_backend:app",
        host="0.0.0.0",
        port=1234,
        reload=True
    )