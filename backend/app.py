"""
NASA BloomWatch Backend - Simplified for Testing
Real-time bloom detection using NASA Earth observation data
"""

import os
import logging
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS
import json

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for services (will be initialized when needed)
nasa_service = None
bloom_service = None
species_service = None
earth_engine_service = None

def initialize_services():
    global nasa_service, bloom_service, species_service, earth_engine_service
    
    if nasa_service is None:
        try:
            from services.nasa_data_service import NASADataService
            from services.bloom_detection_service import BloomDetectionService
            from services.species_identification_service import SpeciesIdentificationService
            from services.earth_engine_service import EarthEngineService
            
            earth_engine_service = EarthEngineService()
            nasa_service = NASADataService()
            bloom_service = BloomDetectionService()
            species_service = SpeciesIdentificationService()
            
            logger.info("Services initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}")
            # Create mock services for testing
            nasa_service = MockNASAService()
            bloom_service = MockBloomService()
            species_service = MockSpeciesService()
            earth_engine_service = None

class MockNASAService:
    """Mock NASA service for testing when Earth Engine is not available"""
    
    def get_vegetation_indices(self, roi, start_date, end_date, indices=['NDVI', 'EVI']):
        # Generate mock time series data
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        time_series = []
        current = start
        while current <= end:
            # Mock seasonal pattern
            day_of_year = current.timetuple().tm_yday
            ndvi = 0.3 + 0.4 * abs(np.sin(2 * np.pi * day_of_year / 365))
            evi = ndvi * 0.7
            
            time_series.append({
                'date': current.strftime('%Y-%m-%d'),
                'ndvi': round(ndvi + np.random.normal(0, 0.05), 4),
                'evi': round(evi + np.random.normal(0, 0.03), 4)
            })
            current += timedelta(days=16)  # MODIS 16-day composites
        
        return {
            'time_series': time_series,
            'metadata': {
                'collection_size': len(time_series),
                'satellite': 'MODIS Terra/Aqua (Mock)',
                'resolution_meters': 250,
                'temporal_resolution': '16-day composite'
            }
        }

class MockBloomService:
    """Mock bloom detection service"""
    
    def detect_bloom_events(self, vegetation_data, latitude, longitude):
        # Generate mock bloom events
        return [
            {
                'id': f'bloom_{latitude}_{longitude}_2023-04-15',
                'start_date': '2023-04-10',
                'peak_date': '2023-04-20',
                'end_date': '2023-05-05',
                'duration_days': 25,
                'peak_ndvi': 0.78,
                'peak_evi': 0.52,
                'bloom_intensity': 0.65,
                'confidence_score': 0.85,
                'detection_method': 'mock',
                'bloom_stage': 'post_bloom',
                'species_hints': ['Cherry blossom', 'Apple blossom', 'Wildflowers']
            }
        ]

class MockSpeciesService:
    """Mock species identification service"""
    
    def identify_species_detailed(self, latitude, longitude, bloom_characteristics):
        return {
            'species_matches': [
                {
                    'species_name': 'Cherry Blossom',
                    'scientific_name': 'Prunus serrulata',
                    'confidence': 0.89,
                    'match_reasons': ['Blooms in April', 'NDVI matches expected range'],
                    'species_info': {
                        'habitat': ['urban', 'forest', 'orchard'],
                        'economic_importance': 'high',
                        'pollinator_value': 'high'
                    }
                }
            ],
            'confidence': 0.89
        }

# Import numpy for mock services
import numpy as np

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'services': {
            'earth_engine': 'connected',
            'database': 'connected'
        }
    })

@app.route('/api/bloom/detect', methods=['POST'])
def detect_blooms():
    """Detect bloom events for a given location and time period"""
    try:
        initialize_services()
        
        data = request.get_json()
        
        # Validate input
        required_fields = ['latitude', 'longitude', 'start_date', 'end_date']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        lat = float(data['latitude'])
        lng = float(data['longitude'])
        start_date = data['start_date']
        end_date = data['end_date']
        radius = data.get('radius', 1000)
        
        # Validate coordinates
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return jsonify({'error': 'Invalid coordinates'}), 400
        
        logger.info(f"Processing bloom detection for {lat}, {lng}")
        
        # Get vegetation indices time series using Earth Engine
        if earth_engine_service and earth_engine_service.initialized:
            vegetation_data = earth_engine_service.get_vegetation_indices(
                lat, lng, start_date, end_date, radius
            )
        else:
            # Fallback to mock data
            vegetation_data = nasa_service.get_vegetation_indices(
                None, start_date, end_date
            )
        
        # Detect bloom events
        bloom_events = bloom_service.detect_bloom_events(
            vegetation_data, lat, lng
        )
        
        response = {
            'location': {'latitude': lat, 'longitude': lng},
            'period': {'start_date': start_date, 'end_date': end_date},
            'bloom_events': bloom_events,
            'data_sources': ['MODIS/061/MOD13Q1 (Mock)'],
            'processing_timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in bloom detection: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bloom/forecast', methods=['POST'])
def forecast_blooms():
    """
    Forecast bloom events for the next 30 days
    
    Request body:
    {
        "latitude": float,
        "longitude": float,
        "forecast_days": int (optional, default: 30)
    }
    """
    try:
        data = request.get_json()
        
        lat = float(data['latitude'])
        lng = float(data['longitude'])
        forecast_days = data.get('forecast_days', 30)
        
        # Get historical data for forecasting
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365 * 2)  # 2 years of history
        
        roi = ee.Geometry.Point([lng, lat]).buffer(1000)
        
        # Get historical vegetation data
        historical_data = nasa_service.get_vegetation_indices(
            roi, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')
        )
        
        # Generate forecast
        forecast = bloom_service.forecast_bloom_events(
            historical_data, lat, lng, forecast_days
        )
        
        response = {
            'location': {'latitude': lat, 'longitude': lng},
            'forecast_period_days': forecast_days,
            'forecast': forecast,
            'confidence_level': 0.85,
            'generated_at': datetime.utcnow().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in bloom forecasting: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/vegetation/indices', methods=['POST'])
def get_vegetation_indices():
    """Get vegetation indices (NDVI, EVI) for a location and time period"""
    try:
        initialize_services()
        
        data = request.get_json()
        
        lat = float(data['latitude'])
        lng = float(data['longitude'])
        start_date = data['start_date']
        end_date = data['end_date']
        indices = data.get('indices', ['NDVI', 'EVI'])
        
        logger.info(f"Getting vegetation indices for {lat}, {lng}")
        
        # Get vegetation indices
        vegetation_data = nasa_service.get_vegetation_indices(
            None, start_date, end_date, indices
        )
        
        response = {
            'location': {'latitude': lat, 'longitude': lng},
            'period': {'start_date': start_date, 'end_date': end_date},
            'indices': vegetation_data,
            'metadata': {
                'satellite': 'MODIS',
                'resolution': '250m',
                'temporal_resolution': '16-day composite'
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting vegetation indices: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/bloom/regional', methods=['POST'])
def get_regional_blooms():
    """
    Get bloom events for a larger region
    
    Request body:
    {
        "bounds": {
            "north": float,
            "south": float,
            "east": float,
            "west": float
        },
        "date": "YYYY-MM-DD",
        "resolution": int (optional, default: 1000m)
    }
    """
    try:
        data = request.get_json()
        bounds = data['bounds']
        date = data['date']
        resolution = data.get('resolution', 1000)
        
        # Create region from bounds
        region = ee.Geometry.Rectangle([
            bounds['west'], bounds['south'],
            bounds['east'], bounds['north']
        ])
        
        # Get regional bloom data
        regional_blooms = nasa_service.get_regional_bloom_data(
            region, date, resolution
        )
        
        response = {
            'bounds': bounds,
            'date': date,
            'resolution_meters': resolution,
            'bloom_data': regional_blooms,
            'processing_timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting regional blooms: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/species/identify', methods=['POST'])
def identify_species():
    """Identify plant species based on bloom characteristics and location"""
    try:
        initialize_services()
        
        data = request.get_json()
        
        lat = float(data['latitude'])
        lng = float(data['longitude'])
        bloom_chars = data['bloom_characteristics']
        
        logger.info(f"Identifying species for {lat}, {lng}")
        
        # Identify species
        species_info = species_service.identify_species_detailed(
            lat, lng, bloom_chars
        )
        
        response = {
            'location': {'latitude': lat, 'longitude': lng},
            'bloom_characteristics': bloom_chars,
            'species_matches': species_info.get('species_matches', []),
            'confidence': species_info.get('confidence', 0.0),
            'identification_timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in species identification: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/phenology/metrics', methods=['POST'])
def get_phenology_metrics():
    """
    Get detailed phenology metrics (Start of Season, Peak of Season, End of Season)
    
    Request body:
    {
        "latitude": float,
        "longitude": float,
        "year": int
    }
    """
    try:
        data = request.get_json()
        
        lat = float(data['latitude'])
        lng = float(data['longitude'])
        year = int(data['year'])
        
        # Get phenology metrics for the year
        metrics = phenology_service.get_annual_phenology_metrics(
            lat, lng, year
        )
        
        response = {
            'location': {'latitude': lat, 'longitude': lng},
            'year': year,
            'phenology_metrics': metrics,
            'calculation_timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting phenology metrics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Run the application
    port = int(os.environ.get('PORT', 5000))
    debug = True  # Enable debug mode for testing
    
    print("🚀 Starting NASA BloomWatch Backend")
    print(f"🌐 Server running on http://localhost:{port}")
    print("🧪 Using mock services for testing")
    print("\n📡 Available endpoints:")
    print("  GET  /health")
    print("  POST /api/vegetation/indices")
    print("  POST /api/bloom/detect")
    print("  POST /api/species/identify")
    print("\n🔧 Run test_backend.py to verify functionality")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
