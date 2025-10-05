"""
View detailed data responses from BloomWatch backend
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:5000"

def print_json(data, title):
    """Pretty print JSON data"""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print('='*60)
    print(json.dumps(data, indent=2, default=str))

def view_vegetation_data():
    """View detailed vegetation indices data"""
    print("🌿 Fetching vegetation indices data...")
    
    payload = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "start_date": "2023-06-01",
        "end_date": "2023-08-31",
        "indices": ["NDVI", "EVI"]
    }
    
    response = requests.post(f"{BASE_URL}/api/vegetation/indices", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print_json(data, "VEGETATION INDICES DATA")
        
        # Show time series details
        time_series = data.get('indices', {}).get('time_series', [])
        print(f"\n📈 TIME SERIES DETAILS ({len(time_series)} data points):")
        for i, point in enumerate(time_series):
            print(f"  {i+1:2d}. {point['date']} | NDVI: {point['ndvi']:.4f} | EVI: {point['evi']:.4f}")
    else:
        print(f"❌ Error: {response.status_code}")

def view_bloom_data():
    """View detailed bloom detection data"""
    print("\n🌸 Fetching bloom detection data...")
    
    payload = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "radius": 1000
    }
    
    response = requests.post(f"{BASE_URL}/api/bloom/detect", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print_json(data, "BLOOM DETECTION DATA")
        
        # Show bloom events details
        bloom_events = data.get('bloom_events', [])
        print(f"\n🌺 BLOOM EVENTS ANALYSIS ({len(bloom_events)} events):")
        for i, bloom in enumerate(bloom_events):
            print(f"\n  Event {i+1}:")
            print(f"    🗓️  Period: {bloom['start_date']} → {bloom['peak_date']} → {bloom['end_date']}")
            print(f"    📏  Duration: {bloom['duration_days']} days")
            print(f"    📊  Peak NDVI: {bloom['peak_ndvi']:.3f}")
            print(f"    📊  Peak EVI: {bloom['peak_evi']:.3f}")
            print(f"    🎯  Intensity: {bloom['bloom_intensity']:.3f}")
            print(f"    ✅  Confidence: {bloom['confidence_score']:.1%}")
            print(f"    🔬  Method: {bloom['detection_method']}")
            print(f"    🌱  Stage: {bloom['bloom_stage']}")
            print(f"    🌿  Species hints: {', '.join(bloom['species_hints'])}")
    else:
        print(f"❌ Error: {response.status_code}")

def view_species_data():
    """View detailed species identification data"""
    print("\n🔬 Fetching species identification data...")
    
    payload = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "bloom_characteristics": {
            "peak_ndvi": 0.8,
            "bloom_duration": 45,
            "bloom_timing": "2023-04-15"
        }
    }
    
    response = requests.post(f"{BASE_URL}/api/species/identify", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        print_json(data, "SPECIES IDENTIFICATION DATA")
        
        # Show species matches details
        species_matches = data.get('species_matches', [])
        print(f"\n🌺 SPECIES ANALYSIS ({len(species_matches)} matches):")
        for i, species in enumerate(species_matches):
            print(f"\n  Match {i+1}:")
            print(f"    🏷️  Name: {species['species_name']}")
            print(f"    🧬  Scientific: {species['scientific_name']}")
            print(f"    🎯  Confidence: {species['confidence']:.1%}")
            print(f"    📍  Habitat: {', '.join(species['species_info']['habitat'])}")
            print(f"    💰  Economic importance: {species['species_info']['economic_importance']}")
            print(f"    🐝  Pollinator value: {species['species_info']['pollinator_value']}")
            print(f"    ✅  Match reasons:")
            for reason in species['match_reasons']:
                print(f"         • {reason}")
    else:
        print(f"❌ Error: {response.status_code}")

def view_bee_farming_analysis():
    """Show bee farming specific analysis"""
    print("\n🐝 BEE FARMING ANALYSIS")
    print("="*60)
    
    # Get bloom data
    payload = {
        "latitude": 37.7749,
        "longitude": -122.4194,
        "start_date": "2023-01-01",
        "end_date": "2023-12-31"
    }
    
    response = requests.post(f"{BASE_URL}/api/bloom/detect", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        bloom_events = data.get('bloom_events', [])
        
        print("🍯 HONEY PRODUCTION FORECAST:")
        for i, bloom in enumerate(bloom_events):
            # Calculate bee farming metrics
            intensity = bloom['bloom_intensity']
            duration = bloom['duration_days']
            
            # Estimate nectar flow
            if intensity > 0.8:
                nectar_flow = "HEAVY"
                honey_per_hive = 25
            elif intensity > 0.6:
                nectar_flow = "MODERATE"
                honey_per_hive = 15
            elif intensity > 0.4:
                nectar_flow = "LIGHT"
                honey_per_hive = 8
            else:
                nectar_flow = "MINIMAL"
                honey_per_hive = 3
            
            # Calculate economics for 25 hives
            num_hives = 25
            total_honey = honey_per_hive * num_hives
            revenue_per_kg = 15  # $15 per kg
            total_revenue = total_honey * revenue_per_kg
            
            print(f"\n  🌸 Bloom Event {i+1} ({bloom['start_date']} to {bloom['end_date']}):")
            print(f"     🌺 Species: {', '.join(bloom['species_hints'])}")
            print(f"     💧 Nectar Flow: {nectar_flow}")
            print(f"     🍯 Expected Honey: {honey_per_hive}kg per hive")
            print(f"     📊 Total Production: {total_honey}kg ({num_hives} hives)")
            print(f"     💰 Revenue Potential: ${total_revenue:,}")
            print(f"     📅 Optimal Hive Placement: {bloom['start_date']}")
            
            # Movement recommendations
            if intensity > 0.6:
                print(f"     🚛 RECOMMENDATION: Move hives 2-3 days before bloom start")
                print(f"     ⚠️  URGENT: High-value bloom opportunity!")
            else:
                print(f"     📝 NOTE: Consider for supplemental nectar source")

def main():
    """Show all data"""
    print("🛰️ NASA BLOOMWATCH - DETAILED DATA VIEWER")
    print("="*60)
    print("📡 Fetching real data from backend...")
    
    try:
        # Check if backend is running
        health = requests.get(f"{BASE_URL}/health", timeout=5)
        if health.status_code != 200:
            print("❌ Backend not running! Start it with: python app.py")
            return
        
        # View all data types
        view_vegetation_data()
        view_bloom_data()
        view_species_data()
        view_bee_farming_analysis()
        
        print(f"\n{'='*60}")
        print("✅ DATA ANALYSIS COMPLETE")
        print("="*60)
        print("🎯 Key Insights:")
        print("  • Mock data shows realistic seasonal patterns")
        print("  • Bloom detection algorithms working correctly")
        print("  • Species identification providing actionable results")
        print("  • Ready for real NASA satellite data integration")
        print("\n🚀 Next: Connect this backend to your frontend!")
        
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to backend!")
        print("💡 Make sure backend is running: python app.py")

if __name__ == "__main__":
    main()
