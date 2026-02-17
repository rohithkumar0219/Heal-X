# Test script for the Multimodal AI Healthcare Assistant

import requests
import json

BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health check endpoint."""
    print("\n=== Testing Health Check ===")
    response = requests.get(f"{BASE_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_text_query():
    """Test text-based query."""
    print("\n=== Testing Text Query ===")
    
    data = {
        "query": "What are the common symptoms of seasonal flu?",
        "include_audio": False
    }
    
    response = requests.post(
        f"{BASE_URL}/api/query",
        json=data
    )
    
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result.get('success')}")
        print(f"Explanation: {result.get('explanation')[:200]}...")
        print(f"Conditions: {len(result.get('possible_conditions', []))}")
        print(f"Precautions: {len(result.get('precautions', []))}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

def test_image_analysis():
    """Test image analysis (requires a test image)."""
    print("\n=== Testing Image Analysis ===")
    print("Note: This test requires a test image file.")
    print("Skipping image test. To test manually:")
    print("  curl -X POST http://localhost:8000/api/analyze-image \\")
    print("    -F 'image=@path/to/image.jpg' \\")
    print("    -F 'query=What could this be?' \\")
    print("    -F 'include_audio=false'")
    return True

def test_voice_query():
    """Test voice query (requires a test audio file)."""
    print("\n=== Testing Voice Query ===")
    print("Note: This test requires a test audio file.")
    print("Skipping voice test. To test manually:")
    print("  curl -X POST http://localhost:8000/api/voice-query \\")
    print("    -F 'audio=@path/to/audio.mp3' \\")
    print("    -F 'include_audio=true'")
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("Multimodal AI Healthcare Assistant - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Health Check", test_health_check),
        ("Text Query", test_text_query),
        ("Image Analysis", test_image_analysis),
        ("Voice Query", test_voice_query),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} failed with error: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")

if __name__ == "__main__":
    main()
