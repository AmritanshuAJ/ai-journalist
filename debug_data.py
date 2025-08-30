#!/usr/bin/env python3
"""
Debug script to test news scraping, Reddit data collection, and Gemini API
with robust fallback (BrightData -> NewsAPI).
"""

import asyncio
import os
from dotenv import load_dotenv
from news_scraper import NewsScraper
from reddit_scraper import scrape_reddit_topics
from utils import (
    generate_news_urls_to_scrape,
    scrape_with_brightdata,
    clean_html_to_text,
    extract_headlines,
)
import requests

load_dotenv()

async def test_news_scraping():
    """Test news scraping functionality with fallback"""
    print("🗞️ Testing News Scraping...")
    print("=" * 50)

    test_topics = ["AI", "Climate Change"]

    # Test URL generation
    print("1. Testing URL generation...")
    urls = generate_news_urls_to_scrape(test_topics)
    for topic, url in urls.items():
        print(f"   {topic}: {url}")

    # -------------------------------
    # Try BrightData First
    # -------------------------------
    print("\n2. Testing BrightData scraping...")
    brightdata_key = os.getenv("BRIGHTDATA_API_KEY")
    if not brightdata_key:
        print("❌ BRIGHTDATA_API_KEY not found in .env file")
    else:
        try:
            first_topic = test_topics[0]
            first_url = urls[first_topic]
            print(f"   Scraping: {first_url}")

            html_content = scrape_with_brightdata(first_url)
            if html_content:
                print(f"✅ HTML content received: {len(html_content)} characters")

                clean_text = clean_html_to_text(html_content)
                print(f"✅ Clean text extracted: {len(clean_text)} characters")

                headlines = extract_headlines(clean_text)
                if headlines:
                    headline_count = len(headlines.split("\n"))
                    print(f"✅ Headlines extracted: {headline_count} headlines")
                    print("📄 Sample headlines:")
                    for i, headline in enumerate(headlines.split("\n")[:3]):
                        print(f"   {i+1}. {headline[:100]}...")
                    return True
                else:
                    print("❌ No headlines extracted")
            else:
                print("❌ No HTML content received")

        except Exception as e:
            print(f"❌ BrightData scraping failed: {e}")

    # -------------------------------
    # Fallback: Try NewsAPI
    # -------------------------------
    print("\n⚡ BrightData failed. Trying NewsAPI fallback...")
    newsapi_key = os.getenv("NEWSAPI_KEY")
    if not newsapi_key:
        print("❌ NEWSAPI_KEY not found in .env file")
        return False

    try:
        url = f"https://newsapi.org/v2/everything?q={test_topics[0]}&apiKey={newsapi_key}&language=en&sortBy=publishedAt&pageSize=5"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            articles = data.get("articles", [])
            if articles:
                print(f"✅ NewsAPI returned {len(articles)} articles")
                for i, article in enumerate(articles[:3]):
                    print(f"   {i+1}. {article['title']}")
                return True
            else:
                print("❌ NewsAPI returned no articles")
                return False
        else:
            print(f"❌ NewsAPI error: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ NewsAPI fallback failed: {e}")
        return False

async def test_reddit_scraping():
    """Test Reddit scraping functionality"""
    print("\n💬 Testing Reddit Scraping...")
    print("=" * 50)

    api_token = os.getenv("API_TOKEN")
    web_unlocker_zone = os.getenv("WEB_UNLOCKER_ZONE")

    if not api_token:
        print("❌ API_TOKEN not found in .env file")
        return False
    if not web_unlocker_zone:
        print("❌ WEB_UNLOCKER_ZONE not found in .env file")
        return False

    print("✅ Environment variables found")

    try:
        test_topics = ["AI"]
        print(f"Testing with topics: {test_topics}")

        results = await scrape_reddit_topics(test_topics)

        if results and "reddit_analysis" in results:
            analysis = results["reddit_analysis"].get("AI", "")
            if analysis:
                print(f"✅ Reddit analysis successful: {len(analysis)} characters")
                print(f"📄 Sample analysis: {analysis[:200]}...")
                return True
            else:
                print("❌ Reddit analysis empty")
                return False
        else:
            print("❌ No results from Reddit scraper")
            return False

    except Exception as e:
        print(f"❌ Reddit scraping failed: {e}")
        return False

async def test_gemini_api():
    """Test Gemini API functionality"""
    print("\n🤖 Testing Gemini API...")
    print("=" * 50)

    gemini_key = os.getenv("GEMINI_API_KEY")
    if not gemini_key:
        print("❌ GEMINI_API_KEY not found in .env file")
        return False

    try:
        import google.generativeai as genai
        genai.configure(api_key=gemini_key)

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content("Say 'Hello World' in a news anchor style.")

        if response and response.text:
            print(f"✅ Gemini API working: {response.text[:100]}...")
            return True
        else:
            print("❌ No response from Gemini API")
            return False

    except Exception as e:
        print(f"❌ Gemini API failed: {e}")
        return False

async def main():
    print("🔍 NewsNinja Diagnostic Tool")
    print("=" * 70)

    news_ok = await test_news_scraping()
    reddit_ok = await test_reddit_scraping()
    gemini_ok = await test_gemini_api()

    print("\n" + "=" * 70)
    print("📊 DIAGNOSTIC SUMMARY:")
    print(f"News Scraping:  {'✅ Working' if news_ok else '❌ Failed'}")
    print(f"Reddit Data:    {'✅ Working' if reddit_ok else '❌ Failed'}")
    print(f"Gemini API:     {'✅ Working' if gemini_ok else '❌ Failed'}")

    if all([news_ok, reddit_ok, gemini_ok]):
        print("\n🎉 All systems working! Your app should work properly.")
    else:
        print("\n⚠️  Some issues detected. Check the errors above.")

if __name__ == "__main__":
    asyncio.run(main())