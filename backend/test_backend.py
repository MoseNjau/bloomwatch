"""
Simple test script to verify backend is working and fetching NASA data
"""

import requests
import json
from datetime import datetime

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_LOCATION = {
    "latitude": 37.7749,  # San Francisco
    "longitude": -122.4194,
    "start_date": "2023-01-01",
    "end_date": "2023-12-31"
}

def test_health_check():
    """Test if the backend is running"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Backend is running!")
            print(f"Response: {response.json()}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend: {e}")
        return False

def test_vegetation_indices():
    """Test vegetation indices endpoint"""
    print("\n🌿 Testing vegetation indices...")
    try:
        payload = {
            "latitude": TEST_LOCATION["latitude"],
            "longitude": TEST_LOCATION["longitude"],
            "start_date": "2023-06-01",
            "end_date": "2023-08-31",
            "indices": ["NDVI", "EVI"]
        }
        
        response = requests.post(
            f"{BASE_URL}/api/vegetation/indices", 
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Vegetation indices retrieved!")
            print(f"Data points: {len(data.get('indices', {}).get('time_series', []))}")
            print(f"Satellite: {data.get('metadata', {}).get('satellite', 'Unknown')}")
            return True
        else:
            print(f"❌ Vegetation indices failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_bloom_detection():
    """Test bloom detection endpoint"""
    print("\n🌸 Testing bloom detection...")
    try:
        payload = {
            "latitude": TEST_LOCATION["latitude"],
            "longitude": TEST_LOCATION["longitude"],
            "start_date": TEST_LOCATION["start_date"],
            "end_date": TEST_LOCATION["end_date"],
            "radius": 1000
        }
        
        response = requests.post(
            f"{BASE_URL}/api/bloom/detect", 
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            bloom_events = data.get('bloom_events', [])
            print("✅ Bloom detection completed!")
            print(f"Bloom events found: {len(bloom_events)}")
            
            if bloom_events:
                first_bloom = bloom_events[0]
                print(f"First bloom: {first_bloom.get('start_date')} to {first_bloom.get('end_date')}")
                print(f"Peak NDVI: {first_bloom.get('peak_ndvi', 'N/A')}")
                print(f"Confidence: {first_bloom.get('confidence_score', 'N/A')}")
            
            return True
        else:
            print(f"❌ Bloom detection failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def test_species_identification():
    """Test species identification endpoint"""
    print("\n🔬 Testing species identification...")
    try:
        payload = {
            "latitude": TEST_LOCATION["latitude"],
            "longitude": TEST_LOCATION["longitude"],
            "bloom_characteristics": {
                "peak_ndvi": 0.8,
                "bloom_duration": 45,
                "bloom_timing": "2023-04-15"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/species/identify", 
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            species_matches = data.get('species_matches', [])
            print("✅ Species identification completed!")
            print(f"Species matches: {len(species_matches)}")
            
            if species_matches:
                top_match = species_matches[0]
                print(f"Top match: {top_match.get('species_name')} ({top_match.get('confidence', 0):.2f} confidence)")
            
            return True
        else:
            print(f"❌ Species identification failed: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting BloomWatch Backend Tests")
    print("=" * 50)
    
    # Test results
    results = {}
    
    # Run tests
    results['health'] = test_health_check()
    
    if results['health']:
        results['vegetation'] = test_vegetation_indices()
        results['bloom'] = test_bloom_detection()
        results['species'] = test_species_identification()
    else:
        print("\n❌ Backend not running. Please start the backend first:")
        print("cd backend")
        print("python app.py")
        return
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{test_name.upper():<15} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Backend is working correctly.")
        print("\nNext steps:")
        print("1. Connect frontend to backend")
        print("2. Test with real NASA data")
        print("3. Deploy to production")
    else:
        print("⚠️  Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
