"""
Google Earth Engine Service for Real-time Satellite Data
Integrates with NASA satellites: MODIS, VIIRS, Landsat
"""

import ee
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from google.auth import default
from google.oauth2 import service_account
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class EarthEngineService:
    """Service for fetching real-time satellite data from Google Earth Engine"""
    
    def __init__(self):
        self.initialized = False
        self._initialize_ee()
        
    def _initialize_ee(self):
        """Initialize Earth Engine authentication"""
        try:
            # Try service account authentication first (production)
            service_account_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH')
            print(f"🔍 Raw service account path from env: {service_account_path}")
            
            if service_account_path:
                # Handle relative paths
                if not os.path.isabs(service_account_path):
                    # Remove 'backend/' prefix if it exists since we're already in backend directory
                    if service_account_path.startswith('backend/'):
                        service_account_path = service_account_path[8:]  # Remove 'backend/'
                    service_account_path = os.path.join(os.path.dirname(__file__), '..', service_account_path)
                    service_account_path = os.path.abspath(service_account_path)
                
                print(f"🔍 Looking for service account key at: {service_account_path}")
                print(f"🔍 File exists: {os.path.exists(service_account_path)}")
                
            if service_account_path and os.path.exists(service_account_path):
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_path,
                    scopes=['https://www.googleapis.com/auth/earthengine']
                )
                ee.Initialize(credentials)
                print("✅ Earth Engine initialized with service account")
            else:
                # Fallback to user authentication (development)
                project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'bloomwatch-432198')
                print(f"🔍 Using project ID: {project_id}")
                ee.Initialize(project=project_id)
                print(f"✅ Earth Engine initialized with project: {project_id}")
                
            self.initialized = True
            
        except Exception as e:
            print(f"❌ Earth Engine initialization failed: {e}")
            print("💡 Using mock data instead")
            self.initialized = False
    
    def get_vegetation_indices(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str,
        radius: int = 1000
    ) -> Dict:
        """
        Get vegetation indices (NDVI, EVI, SAVI) for a location and time period
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate  
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            radius: Radius in meters around the point
            
        Returns:
            Dictionary with time series vegetation data
        """
        if not self.initialized:
            return self._get_mock_vegetation_data(latitude, longitude, start_date, end_date)
        
        try:
            # Create point geometry
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(radius)
            
            # Get MODIS vegetation indices
            modis_vi = ee.ImageCollection('MODIS/061/MOD13Q1') \
                .filterDate(start_date, end_date) \
                .filterBounds(region)
            
            # Calculate vegetation indices
            def calculate_indices(image):
                ndvi = image.select('NDVI').multiply(0.0001)  # Scale factor
                evi = image.select('EVI').multiply(0.0001)
                
                # Calculate SAVI (Soil Adjusted Vegetation Index)
                nir = image.select('sur_refl_b02')
                red = image.select('sur_refl_b01')
                savi = nir.subtract(red).divide(nir.add(red).add(0.5)).multiply(1.5)
                
                return image.addBands([ndvi.rename('NDVI_scaled'), 
                                     evi.rename('EVI_scaled'),
                                     savi.rename('SAVI')])
            
            # Process collection
            processed = modis_vi.map(calculate_indices)
            
            # Extract time series
            time_series = processed.getRegion(region, 250).getInfo()
            
            # Convert to structured data
            return self._process_time_series(time_series)
            
        except Exception as e:
            print(f"❌ Error fetching vegetation indices: {e}")
            return self._get_mock_vegetation_data(latitude, longitude, start_date, end_date)
    
    def get_landsat_data(
        self, 
        latitude: float, 
        longitude: float, 
        start_date: str, 
        end_date: str,
        cloud_cover_max: int = 20
    ) -> Dict:
        """
        Get high-resolution Landsat data for detailed bloom analysis
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            cloud_cover_max: Maximum cloud cover percentage
            
        Returns:
            Dictionary with Landsat imagery data
        """
        if not self.initialized:
            return self._get_mock_landsat_data(latitude, longitude, start_date, end_date)
        
        try:
            # Create point geometry
            point = ee.Geometry.Point([longitude, latitude])
            region = point.buffer(1000)
            
            # Get Landsat 8/9 collection
            landsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
                .filterDate(start_date, end_date) \
                .filterBounds(region) \
                .filter(ee.Filter.lt('CLOUD_COVER', cloud_cover_max))
            
            # Calculate spectral indices
            def add_indices(image):
                # Scale factors for Landsat Collection 2
                optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
                
                # NDVI
                nir = optical_bands.select('SR_B5')
                red = optical_bands.select('SR_B4')
                ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
                
                # EVI
                blue = optical_bands.select('SR_B2')
                evi = nir.subtract(red).divide(
                    nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
                ).multiply(2.5).rename('EVI')
                
                # NDWI (water content)
                swir = optical_bands.select('SR_B6')
                ndwi = nir.subtract(swir).divide(nir.add(swir)).rename('NDWI')
                
                return image.addBands([ndvi, evi, ndwi])
            
            # Process collection
            processed = landsat.map(add_indices)
            
            # Check if collection has images
            count = processed.size().getInfo()
            if count == 0:
                return self._get_mock_landsat_data(latitude, longitude, start_date, end_date)
            
            # Get the most recent image
            latest = processed.sort('system:time_start', False).first()
            
            # Extract data
            data = latest.reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=region,
                scale=30,
                maxPixels=1e9
            ).getInfo()
            
            return {
                'data': data,
                'date': datetime.fromtimestamp(
                    latest.get('system:time_start').getInfo() / 1000
                ).isoformat(),
                'satellite': 'Landsat 8/9',
                'resolution': '30m',
                'location': {'latitude': latitude, 'longitude': longitude}
            }
            
        except Exception as e:
            print(f"❌ Error fetching Landsat data: {e}")
            return self._get_mock_landsat_data(latitude, longitude, start_date, end_date)
    
    def get_regional_bloom_map(
        self, 
        bounds: Dict[str, float], 
        date: str,
        resolution: int = 1000
    ) -> Dict:
        """
        Generate regional bloom intensity map
        
        Args:
            bounds: Dictionary with north, south, east, west coordinates
            date: Target date (YYYY-MM-DD)
            resolution: Spatial resolution in meters
            
        Returns:
            Dictionary with regional bloom data
        """
        if not self.initialized:
            return self._get_mock_regional_data(bounds, date)
        
        try:
            # Create region geometry
            region = ee.Geometry.Rectangle([
                bounds['west'], bounds['south'],
                bounds['east'], bounds['north']
            ])
            
            # Get MODIS data for the date (±8 days for composite)
            start_date = (datetime.strptime(date, '%Y-%m-%d') - timedelta(days=8)).strftime('%Y-%m-%d')
            end_date = (datetime.strptime(date, '%Y-%m-%d') + timedelta(days=8)).strftime('%Y-%m-%d')
            
            modis_collection = ee.ImageCollection('MODIS/061/MOD13Q1') \
                .filterDate(start_date, end_date) \
                .filterBounds(region) \
                .select(['NDVI', 'EVI'])
            
            # Check if collection has images
            count = modis_collection.size().getInfo()
            if count == 0:
                return self._get_mock_regional_data(bounds, date)
            
            modis = modis_collection.median()
            ndvi = modis.select('NDVI').multiply(0.0001)
            evi = modis.select('EVI').multiply(0.0001)
            
            # Bloom intensity formula (weighted combination)
            bloom_intensity = ndvi.multiply(0.6).add(evi.multiply(0.4))
            
            grid_data = bloom_intensity.reduceRegion(
                reducer=ee.Reducer.toList(),
                geometry=region,
                scale=resolution,
                maxPixels=1e6
            ).getInfo()
            
            return {
                'bloom_intensity': grid_data,
                'bounds': bounds,
                'date': date,
                'resolution': resolution,
                'data_source': 'MODIS/061/MOD13Q1'
            }
            
        except Exception as e:
            print(f"❌ Error generating regional bloom map: {e}")
            return self._get_mock_regional_data(bounds, date)
    
    def _process_time_series(self, raw_data: List) -> Dict:
        """Process raw Earth Engine time series data"""
        if not raw_data or len(raw_data) < 2:
            return {'time_series': []}
        
        # Extract headers and data
        headers = raw_data[0]
        data_rows = raw_data[1:]
        
        # Find relevant columns
        time_idx = headers.index('time') if 'time' in headers else 0
        ndvi_idx = headers.index('NDVI_scaled') if 'NDVI_scaled' in headers else None
        evi_idx = headers.index('EVI_scaled') if 'EVI_scaled' in headers else None
        savi_idx = headers.index('SAVI') if 'SAVI' in headers else None
        
        time_series = []
        for row in data_rows:
            if len(row) > max(time_idx, ndvi_idx or 0, evi_idx or 0, savi_idx or 0):
                entry = {
                    'date': datetime.fromtimestamp(row[time_idx] / 1000).strftime('%Y-%m-%d'),
                    'ndvi': row[ndvi_idx] if ndvi_idx and row[ndvi_idx] else None,
                    'evi': row[evi_idx] if evi_idx and row[evi_idx] else None,
                    'savi': row[savi_idx] if savi_idx and row[savi_idx] else None
                }
                time_series.append(entry)
        
        return {
            'time_series': sorted(time_series, key=lambda x: x['date']),
            'data_source': 'MODIS/061/MOD13Q1',
            'processing_timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_mock_vegetation_data(self, lat: float, lon: float, start: str, end: str) -> Dict:
        """Generate mock vegetation data when Earth Engine is unavailable"""
        dates = pd.date_range(start=start, end=end, freq='16D')  # MODIS 16-day cycle
        
        time_series = []
        for date in dates:
            # Simulate seasonal vegetation patterns
            day_of_year = date.timetuple().tm_yday
            base_ndvi = 0.3 + 0.4 * np.sin(2 * np.pi * (day_of_year - 80) / 365)
            base_evi = base_ndvi * 0.7
            
            # Add some noise
            ndvi = max(0, min(1, base_ndvi + np.random.normal(0, 0.05)))
            evi = max(0, min(1, base_evi + np.random.normal(0, 0.03)))
            savi = ndvi * 0.8
            
            time_series.append({
                'date': date.strftime('%Y-%m-%d'),
                'ndvi': round(ndvi, 3),
                'evi': round(evi, 3),
                'savi': round(savi, 3)
            })
        
        return {
            'time_series': time_series,
            'data_source': 'MODIS/061/MOD13Q1 (Mock)',
            'processing_timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_mock_landsat_data(self, lat: float, lon: float, start: str, end: str) -> Dict:
        """Generate mock Landsat data"""
        return {
            'data': {
                'NDVI': 0.65 + np.random.normal(0, 0.1),
                'EVI': 0.45 + np.random.normal(0, 0.08),
                'NDWI': 0.2 + np.random.normal(0, 0.05)
            },
            'date': end,
            'satellite': 'Landsat 8/9 (Mock)',
            'resolution': '30m',
            'location': {'latitude': lat, 'longitude': lon}
        }
    
    def _get_mock_regional_data(self, bounds: Dict, date: str) -> Dict:
        """Generate mock regional data"""
        return {
            'bloom_intensity': {'bloom_intensity': [0.3, 0.5, 0.7, 0.4, 0.6]},
            'bounds': bounds,
            'date': date,
            'resolution': 1000,
            'data_source': 'MODIS/061/MOD13Q1 (Mock)'
        }
