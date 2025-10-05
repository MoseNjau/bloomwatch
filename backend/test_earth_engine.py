#!/usr/bin/env python3
"""
Test script for Google Earth Engine integration
Run this to verify your Earth Engine setup is working
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.earth_engine_service import EarthEngineService
from datetime import datetime, timedelta

def test_earth_engine_connection():
    """Test basic Earth Engine connectivity"""
    print("🧪 Testing Google Earth Engine Integration...")
    print("=" * 50)
    
    # Initialize service
    ee_service = EarthEngineService()
    
    if not ee_service.initialized:
        print("❌ Earth Engine not initialized - using mock data")
        print("💡 To use real data, set up authentication:")
        print("   1. Run: earthengine authenticate")
        print("   2. Or set up service account credentials")
        return False
    
    print("✅ Earth Engine initialized successfully!")
    
    # Test coordinates (San Francisco Bay Area - known agricultural region)
    test_lat = 37.7749
    test_lon = -122.4194
    
    # Test date range (last 3 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    print(f"\n🌍 Testing location: {test_lat}, {test_lon}")
    print(f"📅 Date range: {start_str} to {end_str}")
    
    try:
        # Test vegetation indices
        print("\n📊 Fetching vegetation indices...")
        veg_data = ee_service.get_vegetation_indices(
            test_lat, test_lon, start_str, end_str
        )
        
        if veg_data and 'time_series' in veg_data:
            time_series = veg_data['time_series']
            print(f"✅ Retrieved {len(time_series)} data points")
            
            if time_series:
                latest = time_series[-1]
                print(f"📈 Latest data ({latest['date']}):")
                print(f"   NDVI: {latest.get('ndvi', 'N/A')}")
                print(f"   EVI: {latest.get('evi', 'N/A')}")
                print(f"   SAVI: {latest.get('savi', 'N/A')}")
        
        # Test Landsat data
        print("\n🛰️ Fetching Landsat data...")
        landsat_data = ee_service.get_landsat_data(
            test_lat, test_lon, start_str, end_str
        )
        
        if landsat_data and 'data' in landsat_data:
            data = landsat_data['data']
            print(f"✅ Landsat data retrieved:")
            print(f"   NDVI: {data.get('NDVI', 'N/A'):.3f}")
            print(f"   EVI: {data.get('EVI', 'N/A'):.3f}")
            print(f"   NDWI: {data.get('NDWI', 'N/A'):.3f}")
            print(f"   Date: {landsat_data.get('date', 'N/A')}")
        
        # Test regional data
        print("\n🗺️ Testing regional bloom mapping...")
        bounds = {
            'north': test_lat + 0.1,
            'south': test_lat - 0.1,
            'east': test_lon + 0.1,
            'west': test_lon - 0.1
        }
        
        regional_data = ee_service.get_regional_bloom_map(
            bounds, end_str
        )
        
        if regional_data:
            print(f"✅ Regional data generated for {regional_data.get('date', 'N/A')}")
            print(f"   Resolution: {regional_data.get('resolution', 'N/A')}m")
            print(f"   Data source: {regional_data.get('data_source', 'N/A')}")
        
        print("\n🎉 All tests passed! Earth Engine integration is working.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("💡 Check your Earth Engine authentication and permissions")
        return False

def test_api_endpoint():
    """Test the Flask API endpoint"""
    print("\n🌐 Testing API endpoint...")
    
    import requests
    import json
    
    # Test data
    test_payload = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "start_date": "2024-01-01",
        "end_date": "2024-03-31",
        "radius": 1000
    }
    
    try:
        # Make request to local API
        response = requests.post(
            'http://localhost:5000/api/bloom/detect',
            json=test_payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ API endpoint working!")
            print(f"   Location: {data.get('location', {})}")
            print(f"   Bloom events: {len(data.get('bloom_events', []))}")
            print(f"   Data sources: {data.get('data_sources', [])}")
        else:
            print(f"❌ API returned status {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to API - make sure Flask server is running")
        print("   Run: python app.py")
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")

if __name__ == "__main__":
    print("🌸 BloomWatch Earth Engine Integration Test")
    print("=" * 50)
    
    # Test Earth Engine connection
    ee_success = test_earth_engine_connection()
    
    # Test API endpoint (optional)
    print("\n" + "=" * 50)
    test_api_endpoint()
    
    print("\n" + "=" * 50)
    if ee_success:
        print("🎉 Setup complete! Your BloomWatch backend is ready for real NASA data.")
    else:
        print("⚠️  Using mock data. Set up Earth Engine authentication for real data.")
    
    print("\n📚 Next steps:")
    print("1. Start the Flask server: python app.py")
    print("2. Test the frontend integration")
    print("3. Set up production authentication for deployment")
