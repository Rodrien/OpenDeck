#!/usr/bin/env python3
"""
Test Ollama Server Connection and Functionality

This script tests the Ollama server running at http://192.168.1.2:11434
"""

import requests
import json
import sys
from typing import Dict, Any, Optional

# Ollama server configuration (from docker-compose.yml)
OLLAMA_BASE_URL = "http://192.168.1.2:11434"
OLLAMA_MODEL = "deepseek-r1:8b"


def test_connection() -> bool:
    """Test basic connectivity to Ollama server."""
    print("🔌 Testing connection to Ollama server...")
    print(f"   URL: {OLLAMA_BASE_URL}")
    
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if response.status_code == 200:
            print("   ✅ Connection successful!")
            return True
        else:
            print(f"   ❌ Connection failed with status code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("   ❌ Connection timeout - server not responding")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection error - cannot reach server")
        return False
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return False


def list_models() -> list[Dict[str, Any]]:
    """List all available models on the Ollama server."""
    print("\n📋 Listing available models...")
    
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        response.raise_for_status()
        
        data = response.json()
        models = data.get("models", [])
        
        if models:
            print(f"   Found {len(models)} model(s):")
            for model in models:
                name = model.get("name", "unknown")
                size = model.get("size", 0)
                size_gb = size / (1024**3) if size else 0
                modified = model.get("modified_at", "unknown")
                print(f"   📦 {name}")
                print(f"      Size: {size_gb:.2f} GB")
                print(f"      Modified: {modified}")
        else:
            print("   ⚠️  No models found")
        
        return models
    
    except Exception as e:
        print(f"   ❌ Error listing models: {e}")
        return []


def test_generate(model: str = OLLAMA_MODEL, prompt: str = "Hello, how are you?") -> Optional[str]:
    """Test text generation with a specific model."""
    print(f"\n🤖 Testing text generation with model: {model}")
    print(f"   Prompt: '{prompt}'")
    
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        
        print("   ⏳ Generating response...")
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        
        result = response.json()
        generated_text = result.get("response", "")
        
        if generated_text:
            print(f"   ✅ Response generated successfully!")
            print(f"\n   Response:\n   {'-'*60}")
            print(f"   {generated_text}")
            print(f"   {'-'*60}")
            
            # Print stats if available
            if "total_duration" in result:
                duration_sec = result["total_duration"] / 1e9
                print(f"\n   📊 Stats:")
                print(f"      Duration: {duration_sec:.2f}s")
                if "eval_count" in result:
                    tokens = result["eval_count"]
                    tokens_per_sec = tokens / duration_sec if duration_sec > 0 else 0
                    print(f"      Tokens: {tokens} ({tokens_per_sec:.2f} tokens/s)")
            
            return generated_text
        else:
            print("   ⚠️  No response generated")
            return None
            
    except requests.exceptions.Timeout:
        print("   ❌ Request timeout - generation took too long")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"   ❌ HTTP error: {e}")
        if hasattr(e.response, 'text'):
            print(f"      Details: {e.response.text}")
        return None
    except Exception as e:
        print(f"   ❌ Error generating text: {e}")
        return None


def test_streaming(model: str = OLLAMA_MODEL, prompt: str = "Write a haiku about AI") -> bool:
    """Test streaming text generation."""
    print(f"\n🌊 Testing streaming generation with model: {model}")
    print(f"   Prompt: '{prompt}'")
    
    try:
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }
        
        print("   ⏳ Streaming response...")
        print(f"   Response:\n   {'-'*60}\n   ", end="")
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json=payload,
            stream=True,
            timeout=60
        )
        response.raise_for_status()
        
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                if "response" in data:
                    print(data["response"], end="", flush=True)
                
                if data.get("done", False):
                    print(f"\n   {'-'*60}")
                    print("   ✅ Streaming completed successfully!")
                    return True
        
        return True
        
    except Exception as e:
        print(f"\n   ❌ Error in streaming: {e}")
        return False


def test_embeddings(model: str = OLLAMA_MODEL, text: str = "Hello world") -> Optional[list]:
    """Test embedding generation."""
    print(f"\n🔢 Testing embeddings with model: {model}")
    print(f"   Text: '{text}'")
    
    try:
        payload = {
            "model": model,
            "prompt": text
        }
        
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        embedding = result.get("embedding", [])
        
        if embedding:
            print(f"   ✅ Embedding generated successfully!")
            print(f"      Dimensions: {len(embedding)}")
            print(f"      First 5 values: {embedding[:5]}")
            return embedding
        else:
            print("   ⚠️  No embedding generated")
            return None
            
    except Exception as e:
        print(f"   ❌ Error generating embeddings: {e}")
        return None


def main():
    """Run all Ollama server tests."""
    print("="*70)
    print("🧪 OLLAMA SERVER TEST SUITE")
    print("="*70)
    
    # Test 1: Connection
    if not test_connection():
        print("\n❌ Cannot connect to Ollama server. Exiting.")
        sys.exit(1)
    
    # Test 2: List models
    models = list_models()
    
    if not models:
        print("\n⚠️  No models available. Please pull a model first:")
        print(f"   ollama pull {OLLAMA_MODEL}")
        print(f"   Or: curl http://192.168.1.2:11434/api/pull -d '{{\"name\":\"{OLLAMA_MODEL}\"}}'")
        sys.exit(1)
    
    # Use the configured model or first available model for testing
    test_model = OLLAMA_MODEL if any(m.get("name") == OLLAMA_MODEL for m in models) else models[0].get("name", OLLAMA_MODEL)
    
    # Test 3: Generate text
    test_generate(test_model, "What is the capital of France? Answer in one sentence.")
    
    # Test 4: Streaming
    test_streaming(test_model, "Write a short haiku about coding.")
    
    # Test 5: Embeddings
    test_embeddings(test_model, "Hello, this is a test.")
    
    print("\n" + "="*70)
    print("✅ ALL TESTS COMPLETED!")
    print("="*70)


if __name__ == "__main__":
    main()
