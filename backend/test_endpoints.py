#!/usr/bin/env python3
"""
Test script for BloomWatch API endpoints with real NASA data
"""

import requests
import json
from datetime import datetime, timedelta

# API base URL
BASE_URL = "http://localhost:5000/api"

def test_bloom_detection():
    """Test bloom detection endpoint with real coordinates"""
    print("🌸 Testing Bloom Detection Endpoint")
    print("-" * 40)
    
    # Test different locations
    test_locations = [
        {"name": "California Central Valley (Agriculture)", "lat": 36.7783, "lng": -119.4179},
        {"name": "Amazon Rainforest", "lat": -3.4653, "lng": -62.2159},
        {"name": "Midwest Farmland", "lat": 41.8781, "lng": -87.6298},
        {"name": "Mediterranean Coast", "lat": 43.2965, "lng": 5.3698}
    ]
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    for location in test_locations:
        print(f"\n📍 Testing: {location['name']}")
        
        payload = {
            "latitude": location["lat"],
            "longitude": location["lng"],
            "start_date": start_date.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "radius": 1000
        }
        
        try:
            response = requests.post(
                f"{BASE_URL}/bloom/detect",
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Bloom events: {len(data.get('bloom_events', []))}")
                
                # Show vegetation data summary
                if 'vegetation_data' in data:
                    veg_data = data['vegetation_data']
                    if 'time_series' in veg_data:
                        ts = veg_data['time_series']
                        if ts:
                            latest = ts[-1]
                            print(f"   📊 Latest NDVI: {latest.get('ndvi', 'N/A')}")
                            print(f"   📊 Latest EVI: {latest.get('evi', 'N/A')}")
                            print(f"   📅 Data points: {len(ts)}")
                
                # Show bloom events
                bloom_events = data.get('bloom_events', [])
                if bloom_events:
                    for i, event in enumerate(bloom_events[:2]):  # Show first 2
                        print(f"   🌸 Bloom {i+1}: {event.get('start_date')} to {event.get('end_date')}")
                        print(f"      Intensity: {event.get('bloom_intensity', 'N/A')}")
                        print(f"      Confidence: {event.get('confidence_score', 'N/A')}")
                else:
                    print("   📝 No bloom events detected in this period")
                    
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print("❌ Connection failed - make sure Flask server is running")
            print("   Run: python app.py")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def test_vegetation_indices():
    """Test vegetation indices endpoint"""
    print("\n\n🌱 Testing Vegetation Indices Endpoint")
    print("-" * 40)
    
    # Agricultural region - should have good vegetation data
    payload = {
        "latitude": 40.4173, # Iowa farmland
        "longitude": -93.6533,
        "start_date": "2024-06-01",
        "end_date": "2024-09-30",
        "indices": ["NDVI", "EVI"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/vegetation/indices",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            
            time_series = data.get('time_series', [])
            print(f"📊 Retrieved {len(time_series)} data points")
            
            if time_series:
                # Show seasonal progression
                print("\n📈 Seasonal Vegetation Progression:")
                for i in range(0, len(time_series), len(time_series)//4):  # Show 4 points
                    point = time_series[i]
                    print(f"   {point.get('date')}: NDVI={point.get('ndvi', 'N/A'):.3f}, EVI={point.get('evi', 'N/A'):.3f}")
                    
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_regional_bloom():
    """Test regional bloom mapping"""
    print("\n\n🗺️ Testing Regional Bloom Mapping")
    print("-" * 40)
    
    # California Central Valley region
    payload = {
        "bounds": {
            "north": 37.0,
            "south": 36.0,
            "east": -119.0,
            "west": -120.0
        },
        "date": "2024-07-15",
        "resolution": 1000
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/bloom/regional",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=45  # Regional queries take longer
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            print(f"📅 Date: {data.get('date')}")
            print(f"📏 Resolution: {data.get('resolution')}m")
            print(f"🛰️ Data source: {data.get('data_source', 'N/A')}")
            
            bloom_points = data.get('bloom_points', [])
            if bloom_points:
                print(f"🌸 Bloom points detected: {len(bloom_points)}")
                print(f"📊 Coverage: {data.get('bloom_coverage_percent', 0):.1f}%")
                
                # Show top bloom locations
                sorted_points = sorted(bloom_points, key=lambda x: x.get('bloom_probability', 0), reverse=True)
                print("\n🏆 Top bloom locations:")
                for i, point in enumerate(sorted_points[:3]):
                    print(f"   {i+1}. Lat: {point.get('latitude'):.4f}, Lng: {point.get('longitude'):.4f}")
                    print(f"      Bloom probability: {point.get('bloom_probability', 0):.3f}")
                    print(f"      NDVI: {point.get('ndvi', 0):.3f}")
            else:
                print("📝 No significant bloom activity detected")
                
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def test_bloom_forecast():
    """Test bloom forecasting"""
    print("\n\n🔮 Testing Bloom Forecasting")
    print("-" * 40)
    
    payload = {
        "latitude": 38.5816, # California almond region
        "longitude": -121.4944,
        "forecast_days": 30
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/bloom/forecast",
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Success!")
            
            forecast = data.get('forecast', {})
            print(f"📅 Forecast period: {forecast.get('forecast_days', 0)} days")
            print(f"🎯 Confidence: {forecast.get('confidence', 0):.2f}")
            
            predictions = forecast.get('predictions', [])
            if predictions:
                print(f"📊 Predictions: {len(predictions)} data points")
                print("\n🔮 Next 7 days forecast:")
                for pred in predictions[:7]:
                    print(f"   {pred.get('date')}: Bloom probability {pred.get('bloom_probability', 0):.3f}")
            
        else:
            print(f"❌ Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Run all endpoint tests"""
    print("🧪 BloomWatch API Endpoint Testing")
    print("=" * 50)
    print("🚀 Make sure Flask server is running: python app.py")
    print("=" * 50)
    
    # Test all endpoints
    test_bloom_detection()
    test_vegetation_indices()
    test_regional_bloom()
    test_bloom_forecast()
    
    print("\n" + "=" * 50)
    print("🎉 Testing complete!")
    print("💡 Check the results above to see your real NASA data in action")

if __name__ == "__main__":
    main()
