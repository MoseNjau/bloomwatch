"""
NASA Data Service
Integrates with Google Earth Engine to fetch real NASA satellite data
"""

import ee
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class NASADataService:
    """Service for fetching and processing NASA Earth observation data"""
    
    def __init__(self):
        self.modis_collection = 'MODIS/061/MOD13Q1'  # Terra MODIS 16-day vegetation indices
        self.modis_aqua_collection = 'MODIS/061/MYD13Q1'  # Aqua MODIS 16-day vegetation indices
        self.viirs_collection = 'NOAA/VIIRS/001/VNP13A1'  # VIIRS 16-day vegetation indices
        self.landsat_collection = 'LANDSAT/LC08/C02/T1_L2'  # Landsat 8 Collection 2
        
    def get_vegetation_indices(
        self, 
        roi: ee.Geometry, 
        start_date: str, 
        end_date: str,
        indices: List[str] = ['NDVI', 'EVI']
    ) -> Dict:
        """
        Get vegetation indices time series for a region of interest
        
        Args:
            roi: Earth Engine Geometry object
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            indices: List of indices to retrieve ['NDVI', 'EVI', 'SAVI', 'NDWI']
            
        Returns:
            Dictionary containing time series data
        """
        try:
            # Load MODIS vegetation indices
            modis_terra = ee.ImageCollection(self.modis_collection) \
                .filterDate(start_date, end_date) \
                .filterBounds(roi) \
                .select(indices)
            
            modis_aqua = ee.ImageCollection(self.modis_aqua_collection) \
                .filterDate(start_date, end_date) \
                .filterBounds(roi) \
                .select(indices)
            
            # Merge Terra and Aqua collections
            modis_combined = modis_terra.merge(modis_aqua).sort('system:time_start')
            
            # Apply scale factor (MODIS vegetation indices are scaled by 10000)
            def apply_scale_factor(image):
                scaled = image.multiply(0.0001)
                return scaled.copyProperties(image, image.propertyNames())
            
            modis_scaled = modis_combined.map(apply_scale_factor)
            
            # Extract time series
            time_series = self._extract_time_series(modis_scaled, roi, indices)
            
            # Get additional metadata
            metadata = self._get_collection_metadata(modis_scaled, roi)
            
            return {
                'time_series': time_series,
                'metadata': metadata,
                'roi_area_km2': roi.area().divide(1000000).getInfo(),
                'data_points': modis_scaled.size().getInfo()
            }
            
        except Exception as e:
            logger.error(f"Error getting vegetation indices: {str(e)}")
            raise
    
    def get_regional_bloom_data(
        self, 
        region: ee.Geometry, 
        date: str, 
        resolution: int = 1000
    ) -> Dict:
        """
        Get bloom detection data for a larger region
        
        Args:
            region: Earth Engine Geometry object for the region
            date: Date in 'YYYY-MM-DD' format
            resolution: Spatial resolution in meters
            
        Returns:
            Dictionary containing regional bloom data
        """
        try:
            # Get date range (±8 days for 16-day composite)
            target_date = datetime.strptime(date, '%Y-%m-%d')
            start_date = (target_date - timedelta(days=8)).strftime('%Y-%m-%d')
            end_date = (target_date + timedelta(days=8)).strftime('%Y-%m-%d')
            
            # Load MODIS data
            modis = ee.ImageCollection(self.modis_collection) \
                .filterDate(start_date, end_date) \
                .filterBounds(region) \
                .select(['NDVI', 'EVI']) \
                .first()
            
            if modis is None:
                return {'error': 'No data available for the specified date and region'}
            
            # Apply scale factor
            modis_scaled = modis.multiply(0.0001)
            
            # Calculate bloom probability based on NDVI and EVI thresholds
            bloom_mask = self._calculate_bloom_probability(modis_scaled)
            
            # Sample the region
            sample_points = bloom_mask.sample(
                region=region,
                scale=resolution,
                numPixels=10000,
                geometries=True
            )
            
            # Convert to list for JSON serialization
            sample_data = sample_points.getInfo()
            
            # Process sample data
            bloom_points = []
            for feature in sample_data['features']:
                coords = feature['geometry']['coordinates']
                properties = feature['properties']
                
                if properties.get('bloom_probability', 0) > 0.3:  # Threshold for bloom detection
                    bloom_points.append({
                        'longitude': coords[0],
                        'latitude': coords[1],
                        'bloom_probability': properties.get('bloom_probability', 0),
                        'ndvi': properties.get('NDVI', 0),
                        'evi': properties.get('EVI', 0)
                    })
            
            return {
                'date': date,
                'bloom_points': bloom_points,
                'total_points_analyzed': len(sample_data['features']),
                'bloom_points_detected': len(bloom_points),
                'bloom_coverage_percent': (len(bloom_points) / len(sample_data['features'])) * 100
            }
            
        except Exception as e:
            logger.error(f"Error getting regional bloom data: {str(e)}")
            raise
    
    def get_landsat_data(
        self, 
        roi: ee.Geometry, 
        start_date: str, 
        end_date: str
    ) -> Dict:
        """
        Get Landsat 8 data for higher resolution analysis
        
        Args:
            roi: Earth Engine Geometry object
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format
            
        Returns:
            Dictionary containing Landsat data
        """
        try:
            # Load Landsat 8 Collection 2
            landsat = ee.ImageCollection(self.landsat_collection) \
                .filterDate(start_date, end_date) \
                .filterBounds(roi) \
                .filter(ee.Filter.lt('CLOUD_COVER', 20))
            
            # Function to calculate vegetation indices
            def calculate_indices(image):
                # Scale factors for Landsat Collection 2
                optical_bands = image.select('SR_B.').multiply(0.0000275).add(-0.2)
                
                # Calculate NDVI
                nir = optical_bands.select('SR_B5')
                red = optical_bands.select('SR_B4')
                ndvi = nir.subtract(red).divide(nir.add(red)).rename('NDVI')
                
                # Calculate EVI
                blue = optical_bands.select('SR_B2')
                evi = nir.subtract(red).multiply(2.5).divide(
                    nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
                ).rename('EVI')
                
                return image.addBands([ndvi, evi])
            
            # Apply vegetation index calculation
            landsat_with_indices = landsat.map(calculate_indices)
            
            # Get median composite
            composite = landsat_with_indices.median()
            
            # Extract values for ROI
            roi_stats = composite.select(['NDVI', 'EVI']).reduceRegion(
                reducer=ee.Reducer.mean(),
                geometry=roi,
                scale=30,
                maxPixels=1e9
            )
            
            return {
                'ndvi_mean': roi_stats.getInfo().get('NDVI'),
                'evi_mean': roi_stats.getInfo().get('EVI'),
                'image_count': landsat.size().getInfo(),
                'resolution_meters': 30,
                'satellite': 'Landsat 8'
            }
            
        except Exception as e:
            logger.error(f"Error getting Landsat data: {str(e)}")
            raise
    
    def _extract_time_series(
        self, 
        collection: ee.ImageCollection, 
        roi: ee.Geometry, 
        bands: List[str]
    ) -> List[Dict]:
        """Extract time series data from image collection"""
        try:
            # Create a function to extract values for each image
            def extract_values(image):
                # Get image date
                date = ee.Date(image.get('system:time_start')).format('YYYY-MM-dd')
                
                # Reduce region to get mean values
                stats = image.select(bands).reduceRegion(
                    reducer=ee.Reducer.mean(),
                    geometry=roi,
                    scale=250,
                    maxPixels=1e9
                )
                
                # Return feature with date and values
                return ee.Feature(None, stats.set('date', date))
            
            # Map over collection and extract values
            time_series_collection = collection.map(extract_values)
            
            # Convert to list
            time_series_list = time_series_collection.getInfo()
            
            # Process the results
            time_series_data = []
            for feature in time_series_list['features']:
                properties = feature['properties']
                data_point = {'date': properties['date']}
                
                for band in bands:
                    data_point[band.lower()] = properties.get(band, None)
                
                time_series_data.append(data_point)
            
            # Sort by date
            time_series_data.sort(key=lambda x: x['date'])
            
            return time_series_data
            
        except Exception as e:
            logger.error(f"Error extracting time series: {str(e)}")
            raise
    
    def _calculate_bloom_probability(self, image: ee.Image) -> ee.Image:
        """Calculate bloom probability based on vegetation indices"""
        try:
            ndvi = image.select('NDVI')
            evi = image.select('EVI')
            
            # Define thresholds for bloom detection
            # These are empirically derived thresholds
            ndvi_threshold = 0.4
            evi_threshold = 0.3
            
            # Calculate bloom probability
            ndvi_score = ndvi.subtract(ndvi_threshold).divide(1 - ndvi_threshold).max(0).min(1)
            evi_score = evi.subtract(evi_threshold).divide(1 - evi_threshold).max(0).min(1)
            
            # Combined bloom probability (geometric mean)
            bloom_probability = ndvi_score.multiply(evi_score).sqrt().rename('bloom_probability')
            
            return image.addBands(bloom_probability)
            
        except Exception as e:
            logger.error(f"Error calculating bloom probability: {str(e)}")
            raise
    
    def _get_collection_metadata(
        self, 
        collection: ee.ImageCollection, 
        roi: ee.Geometry
    ) -> Dict:
        """Get metadata about the image collection"""
        try:
            # Get collection size
            size = collection.size().getInfo()
            
            # Get date range
            dates = collection.aggregate_array('system:time_start')
            date_list = dates.getInfo()
            
            if date_list:
                start_timestamp = min(date_list)
                end_timestamp = max(date_list)
                
                start_date = datetime.fromtimestamp(start_timestamp / 1000).strftime('%Y-%m-%d')
                end_date = datetime.fromtimestamp(end_timestamp / 1000).strftime('%Y-%m-%d')
            else:
                start_date = end_date = None
            
            return {
                'collection_size': size,
                'date_range': {
                    'start': start_date,
                    'end': end_date
                },
                'satellite': 'MODIS Terra/Aqua',
                'resolution_meters': 250,
                'temporal_resolution': '16-day composite'
            }
            
        except Exception as e:
            logger.error(f"Error getting collection metadata: {str(e)}")
            return {}
