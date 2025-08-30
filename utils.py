from urllib.parse import quote_plus
from dotenv import load_dotenv
import requests
import os
from fastapi import FastAPI, HTTPException
from bs4 import BeautifulSoup
import ollama
import google.generativeai as genai
from datetime import datetime
from elevenlabs import ElevenLabs

load_dotenv()

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))


class MCPOverloadedError(Exception):
    """Custom exception for MCP service overloads"""
    pass


def generate_valid_news_url(keyword: str) -> str:
    """
    Generate a Google News search URL for a keyword with optional sorting by latest
    
    Args:
        keyword: Search term to use in the news search
        
    Returns:
        str: Constructed Google News search URL
    """
    q = quote_plus(keyword)
    return f"https://news.google.com/search?q={q}&tbs=sbd:1"


def generate_news_urls_to_scrape(list_of_keywords):
    valid_urls_dict = {}
    for keyword in list_of_keywords:
        valid_urls_dict[keyword] = generate_valid_news_url(keyword)
    
    return valid_urls_dict


def scrape_with_brightdata(url: str) -> str:
    """Scrape a URL using BrightData"""
    headers = {
        "Authorization": f"Bearer {os.getenv('BRIGHTDATA_API_KEY')}",
        "Content-Type": "application/json"
    }

    payload = {
        "zone": os.getenv('BRIGHTDATA_WEB_UNLOCKER_ZONE'),
        "url": url,
        "format": "raw"
    }
    
    try:
        response = requests.post("https://api.brightdata.com/request", json=payload, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"BrightData error: {str(e)}")


def clean_html_to_text(html_content: str) -> str:
    """Clean HTML content to plain text"""
    soup = BeautifulSoup(html_content, "html.parser")
    text = soup.get_text(separator="\n")
    return text.strip()


def extract_headlines(cleaned_text: str) -> str:
    """
    Extract and concatenate headlines from cleaned news text content.
    
    Args:
        cleaned_text: Raw text from news page after HTML cleaning
        
    Returns:
        str: Combined headlines separated by newlines
    """
    headlines = []
    current_block = []
    
    # Split text into lines and remove empty lines
    lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
    
    # Process lines to find headline blocks
    for line in lines:
        if line == "More":
            if current_block:
                # First line of block is headline
                headlines.append(current_block[0])
                current_block = []
        else:
            current_block.append(line)
    
    # Add any remaining block at end of text
    if current_block:
        headlines.append(current_block[0])
    
    return "\n".join(headlines)


def summarize_with_ollama(headlines) -> str:
    """Summarize content using Ollama (fallback option)"""
    prompt = f"""You are my personal news editor. Summarize these headlines into a TV news script for me, focus on important headlines and remember that this text will be converted to audio:
    So no extra stuff other than text which the podcast/news host should read, no special symbols or extra information in between and of course no preamble please.
    {headlines}
    News Script:"""

    try:
        client = ollama.Client(host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
        
        # Generate response using the Ollama client
        response = client.generate(
            model="llama3.2",
            prompt=prompt,
            options={
                "temperature": 0.4,
                "max_tokens": 800
            },
            stream=False
        )
        
        return response['response']
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama error: {str(e)}")


def generate_broadcast_news(api_key, news_data, reddit_data, topics):
    """Generate broadcast news using Gemini API"""
    system_prompt = """
    You are broadcast_news_writer, a professional virtual news reporter. Generate natural, TTS-ready news reports using available sources:

    For each topic, STRUCTURE BASED ON AVAILABLE DATA:
    1. If news exists: "According to official reports..." + summary
    2. If Reddit exists: "Online discussions on Reddit reveal..." + summary
    3. If both exist: Present news first, then Reddit reactions
    4. If neither exists: Create a general introduction about the topic and mention that current data is limited

    Formatting rules:
    - ALWAYS start directly with the content, NO INTRODUCTIONS
    - Keep audio length 60-120 seconds per topic
    - Use natural speech transitions like "Meanwhile, online discussions..." 
    - Incorporate 1-2 short quotes from Reddit when available
    - Maintain neutral tone but highlight key sentiments
    - If no data is available, provide brief context about the topic and why it's newsworthy
    - End with "To wrap up this segment..." summary

    Write in full paragraphs optimized for speech synthesis. Avoid markdown.
    """

    try:
        topic_blocks = []
        for topic in topics:
            news_content = ""
            reddit_content = ""
            
            # Safely extract news content
            if news_data and "news_analysis" in news_data:
                news_content = news_data["news_analysis"].get(topic, "")
                # Skip if it's an error message
                if news_content.startswith("Error:"):
                    news_content = ""
            
            # Safely extract Reddit content
            if reddit_data and "reddit_analysis" in reddit_data:
                reddit_content = reddit_data["reddit_analysis"].get(topic, "")
            
            # Build context for this topic
            context = []
            if news_content:
                context.append(f"OFFICIAL NEWS CONTENT:\n{news_content}")
            if reddit_content:
                context.append(f"REDDIT DISCUSSION CONTENT:\n{reddit_content}")
            
            # Always include the topic, even if no data
            if context:
                topic_blocks.append(
                    f"TOPIC: {topic}\n\n" +
                    "\n\n".join(context)
                )
            else:
                # No data available, but still include the topic
                topic_blocks.append(
                    f"TOPIC: {topic}\n\n" +
                    f"LIMITED DATA: No current news or Reddit data available for this topic."
                )

        if not topic_blocks:
            # Fallback if no topics at all
            user_prompt = f"Create a brief news segment explaining that current data for topics {', '.join(topics)} is temporarily unavailable, but provide general context about why these topics are newsworthy."
        else:
            user_prompt = (
                "Create broadcast segments for these topics using available sources:\n\n" +
                "\n\n--- NEW TOPIC ---\n\n".join(topic_blocks)
            )

        # Use Gemini API
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.3,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 4000,
            }
        )

        full_prompt = f"{system_prompt}\n\n{user_prompt}"
        response = model.generate_content(full_prompt)
        
        return response.text

    except Exception as e:
        # Return a fallback script if Gemini fails
        fallback_script = f"Welcome to your news update. Today we're covering {', '.join(topics)}. Unfortunately, we're experiencing technical difficulties accessing current news data. Please check back later for updated information on these important topics."
        print(f"⚠️ Gemini API failed, using fallback script: {e}")
        return fallback_script


def summarize_with_gemini_news_script(api_key: str, headlines: str) -> str:
    """
    Summarize multiple news headlines into a TTS-friendly broadcast news script using Gemini API.
    """
    system_prompt = """
You are my personal news editor and scriptwriter for a news podcast. Your job is to turn raw headlines into a clean, professional, and TTS-friendly news script.

The final output will be read aloud by a news anchor or text-to-speech engine. So:
- Do not include any special characters, emojis, formatting symbols, or markdown.
- Do not add any preamble or framing like "Here's your summary" or "Let me explain".
- Write in full, clear, spoken-language paragraphs.
- Keep the tone formal, professional, and broadcast-style — just like a real TV news script.
- Focus on the most important headlines and turn them into short, informative news segments that sound natural when spoken.
- Start right away with the actual script, using transitions between topics if needed.

Remember: Your only output should be a clean script that is ready to be read out loud.
"""

    try:
        model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.4,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 1000,
            }
        )

        full_prompt = f"{system_prompt}\n\nHeadlines to summarize:\n{headlines}"
        response = model.generate_content(full_prompt)
        
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")


def text_to_audio_elevenlabs_sdk(
    text: str,
    voice_id: str = "JBFqnCBsd6RMkjVDRZzb",
    model_id: str = "eleven_multilingual_v2",
    output_format: str = "mp3_44100_128",
    output_dir: str = "audio",
    api_key: str = None
) -> str:
    """
    Converts text to speech using ElevenLabs SDK and saves it to audio/ directory.

    Returns:
        str: Path to the saved audio file.
    """
    try:
        api_key = api_key or os.getenv("ELEVEN_API_KEY")
        if not api_key:
            raise ValueError("ElevenLabs API key is required.")

        # Initialize client
        client = ElevenLabs(api_key=api_key)

        # Get the audio generator
        audio_stream = client.text_to_speech.convert(
            text=text,
            voice_id=voice_id,
            model_id=model_id,
            output_format=output_format
        )

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Generate unique filename
        filename = f"tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
        filepath = os.path.join(output_dir, filename)

        # Write audio chunks to file
        with open(filepath, "wb") as f:
            for chunk in audio_stream:
                f.write(chunk)

        return filepath

    except Exception as e:
        # Re-raise with more specific error information
        if "detected_unusual_activity" in str(e):
            raise Exception("ElevenLabs free tier disabled due to unusual activity. Consider upgrading to a paid plan.")
        elif "401" in str(e):
            raise Exception("ElevenLabs API authentication failed. Check your API key.")
        else:
            raise Exception(f"ElevenLabs TTS failed: {str(e)}")


from pathlib import Path
from gtts import gTTS
AUDIO_DIR = Path("audio")
AUDIO_DIR.mkdir(exist_ok=True)  # Create directory if it doesn't exist


def tts_to_audio(text: str, language: str = 'en') -> str:
    """
    Convert text to speech using gTTS (Google Text-to-Speech) and save to file.
    
    Args:
        text: Input text to convert
        language: Language code (default: 'en')
    
    Returns:
        str: Path to saved audio file
    
    Example:
        tts_to_audio("Hello world", "en")
    """
    try:
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = AUDIO_DIR / f"tts_{timestamp}.mp3"
        
        # Create TTS object and save
        tts = gTTS(text=text, lang=language, slow=False)
        tts.save(str(filename))
        
        return str(filename)
    except Exception as e:
        print(f"gTTS Error: {str(e)}")
        raise Exception(f"gTTS failed: {str(e)}")


def get_chat_model():
    """
    Try Gemini first, but if credits are exhausted, fallback to Ollama.
    """
    try:
        # Configure and test Gemini
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        # Test Gemini with a dummy request
        response = model.generate_content("Hello")
        print("✅ Using Gemini")
        return model
    except Exception as e:
        print(f"⚠️ Gemini unavailable: {e}")
        print("👉 Falling back to Ollama...")
        from langchain_ollama import ChatOllama
        return ChatOllama(model="llama3")