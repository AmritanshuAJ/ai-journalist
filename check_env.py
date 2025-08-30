#!/usr/bin/env python3
"""
Quick script to check environment variables
"""

import os
from dotenv import load_dotenv

load_dotenv()

required_vars = {
    'GEMINI_API_KEY': 'Gemini API Key',
    'BRIGHTDATA_API_KEY': 'BrightData API Key',
    'BRIGHTDATA_WEB_UNLOCKER_ZONE': 'BrightData Web Unlocker Zone',
    'API_TOKEN': 'BrightData API Token (for Reddit)',
    'WEB_UNLOCKER_ZONE': 'Web Unlocker Zone (for Reddit)',
    'ELEVEN_API_KEY': 'ElevenLabs API Key (optional)'
}

print("🔍 Environment Variables Check")
print("=" * 50)

all_good = True
for var_name, description in required_vars.items():
    value = os.getenv(var_name)
    if value:
        # Show first 10 characters for security
        masked_value = value[:10] + "..." if len(value) > 10 else value
        print(f"✅ {var_name}: {masked_value}")
    else:
        print(f"❌ {var_name}: NOT FOUND")
        all_good = False

print("\n" + "=" * 50)
if all_good:
    print("🎉 All environment variables are set!")
else:
    print("⚠️  Some environment variables are missing.")
    print("📝 Make sure your .env file contains all required keys.")

# Check if .env file exists
env_file = ".env"
if os.path.exists(env_file):
    print(f"📄 .env file found: {env_file}")
else:
    print(f"❌ .env file not found: {env_file}")
    print("💡 Create a .env file with your API keys")