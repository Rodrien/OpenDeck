#!/usr/bin/env python3
"""
Debug Ollama Response - See what the model actually returns

This script sends a flashcard generation request to Ollama and 
prints the raw response to help debug parsing issues.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
import json
from app.services.ai.prompts import build_system_prompt, build_user_prompt

# Configuration
OLLAMA_BASE_URL = "http://192.168.1.2:11434"
OLLAMA_MODEL = "deepseek-r1:8b"

# Sample document text (short for testing)
SAMPLE_TEXT = """
Python is a high-level programming language. It was created by Guido van Rossum 
and first released in 1991. Python emphasizes code readability with significant 
indentation. It supports multiple programming paradigms including procedural, 
object-oriented, and functional programming.
"""

DOCUMENT_NAME = "sample.txt"
PAGE_DATA = [(1, SAMPLE_TEXT)]
MAX_CARDS = 3


def test_ollama_flashcard_generation():
    """Test Ollama with actual flashcard generation prompt."""
    
    print("="*70)
    print("🧪 DEBUGGING OLLAMA FLASHCARD GENERATION")
    print("="*70)
    
    # Build prompts
    system_prompt = build_system_prompt(DOCUMENT_NAME, MAX_CARDS)
    user_prompt = build_user_prompt(SAMPLE_TEXT, PAGE_DATA)
    
    # Combine prompts for Ollama
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    
    print("\n📝 SYSTEM PROMPT:")
    print("-" * 70)
    print(system_prompt[:500] + "..." if len(system_prompt) > 500 else system_prompt)
    
    print("\n📝 USER PROMPT:")
    print("-" * 70)
    print(user_prompt[:500] + "..." if len(user_prompt) > 500 else user_prompt)
    
    # Prepare request
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": full_prompt,
        "stream": False,
        "format": "json",  # Request JSON format
        "options": {
            "temperature": 0.7,
            "num_predict": 4000
        }
    }
    
    print(f"\n🚀 SENDING REQUEST TO: {OLLAMA_BASE_URL}/api/generate")
    print(f"   Model: {OLLAMA_MODEL}")
    print(f"   Format: json")
    print(f"   Temperature: 0.7")
    
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=120
        )
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get("response", "")
        
        print("\n✅ RESPONSE RECEIVED")
        print("-" * 70)
        print(f"Status: {response.status_code}")
        print(f"Response Length: {len(response_text)} characters")
        
        print("\n📄 RAW RESPONSE:")
        print("=" * 70)
        print(response_text)
        print("=" * 70)
        
        # Try to parse as JSON
        print("\n🔍 PARSING JSON...")
        try:
            data = json.loads(response_text)
            print("✅ Valid JSON!")
            print(f"\nParsed structure:")
            print(json.dumps(data, indent=2))
            
            # Check for flashcards
            if "flashcards" in data:
                flashcards = data["flashcards"]
                print(f"\n✅ Found 'flashcards' key with {len(flashcards)} cards")
                
                for i, card in enumerate(flashcards, 1):
                    print(f"\n📇 Card {i}:")
                    print(f"   Question: {card.get('question', 'MISSING')[:100]}")
                    print(f"   Answer: {card.get('answer', 'MISSING')[:100]}")
                    print(f"   Source: {card.get('source', 'MISSING')}")
            else:
                print("\n❌ No 'flashcards' key in response!")
                print(f"   Available keys: {list(data.keys())}")
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing failed: {e}")
            print("\n🔍 Trying to find JSON in response...")
            
            # Sometimes the model includes extra text before/after JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                print("Found potential JSON block, attempting parse...")
                try:
                    data = json.loads(json_match.group(0))
                    print("✅ Extracted JSON successfully!")
                    print(json.dumps(data, indent=2))
                except:
                    print("❌ Still couldn't parse extracted JSON")
            
        # Print stats
        if "total_duration" in result:
            duration_sec = result["total_duration"] / 1e9
            print(f"\n⏱️  Generation time: {duration_sec:.2f}s")
            
            if "eval_count" in result:
                tokens = result["eval_count"]
                tokens_per_sec = tokens / duration_sec if duration_sec > 0 else 0
                print(f"   Tokens: {tokens} ({tokens_per_sec:.2f} tokens/s)")
        
    except requests.exceptions.Timeout:
        print("\n❌ Request timeout")
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP error: {e}")
        if hasattr(e.response, 'text'):
            print(f"Details: {e.response.text}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_ollama_flashcard_generation()
