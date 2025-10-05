"""
Database models for storing bloom detection and phenology data
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
import json

db = SQLAlchemy()

class BloomEvent(db.Model):
    """Model for storing detected bloom events"""
    __tablename__ = 'bloom_events'
    
    id = Column(Integer, primary_key=True)
    
    # Location information
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    location_name = Column(String(255))
    
    # Bloom timing
    start_date = Column(DateTime, nullable=False, index=True)
    peak_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False, index=True)
    duration_days = Column(Integer)
    
    # Bloom characteristics
    peak_ndvi = Column(Float)
    peak_evi = Column(Float)
    bloom_intensity = Column(Float)
    confidence_score = Column(Float)
    
    # Detection metadata
    detection_method = Column(String(50))
    bloom_stage = Column(String(20))
    data_source = Column(String(100))
    
    # Species information
    species_hints = Column(JSON)
    identified_species = Column(String(255))
    species_confidence = Column(Float)
    
    # Economic data for bee farmers
    nectar_flow_rating = Column(String(20))  # heavy, moderate, light, minimal
    pollen_quality = Column(String(20))      # excellent, good, fair, poor
    pollinator_value = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert model to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude,
                'name': self.location_name
            },
            'timing': {
                'start_date': self.start_date.isoformat() if self.start_date else None,
                'peak_date': self.peak_date.isoformat() if self.peak_date else None,
                'end_date': self.end_date.isoformat() if self.end_date else None,
                'duration_days': self.duration_days
            },
            'characteristics': {
                'peak_ndvi': self.peak_ndvi,
                'peak_evi': self.peak_evi,
                'bloom_intensity': self.bloom_intensity,
                'confidence_score': self.confidence_score
            },
            'detection': {
                'method': self.detection_method,
                'stage': self.bloom_stage,
                'data_source': self.data_source
            },
            'species': {
                'hints': self.species_hints,
                'identified': self.identified_species,
                'confidence': self.species_confidence
            },
            'bee_farming': {
                'nectar_flow': self.nectar_flow_rating,
                'pollen_quality': self.pollen_quality,
                'pollinator_value': self.pollinator_value
            },
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class VegetationIndex(db.Model):
    """Model for storing vegetation index time series data"""
    __tablename__ = 'vegetation_indices'
    
    id = Column(Integer, primary_key=True)
    
    # Location
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    
    # Date and satellite info
    observation_date = Column(DateTime, nullable=False, index=True)
    satellite = Column(String(50))  # MODIS, VIIRS, Landsat
    resolution_meters = Column(Integer)
    
    # Vegetation indices
    ndvi = Column(Float)
    evi = Column(Float)
    savi = Column(Float)
    ndwi = Column(Float)
    
    # Quality flags
    cloud_cover = Column(Float)
    quality_flag = Column(String(20))
    
    # Processing metadata
    processing_level = Column(String(20))
    algorithm_version = Column(String(20))
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            'observation_date': self.observation_date.isoformat() if self.observation_date else None,
            'satellite_info': {
                'satellite': self.satellite,
                'resolution_meters': self.resolution_meters
            },
            'indices': {
                'ndvi': self.ndvi,
                'evi': self.evi,
                'savi': self.savi,
                'ndwi': self.ndwi
            },
            'quality': {
                'cloud_cover': self.cloud_cover,
                'quality_flag': self.quality_flag
            },
            'processing': {
                'level': self.processing_level,
                'algorithm_version': self.algorithm_version
            }
        }

class PhenologyMetrics(db.Model):
    """Model for storing phenology analysis results"""
    __tablename__ = 'phenology_metrics'
    
    id = Column(Integer, primary_key=True)
    
    # Location and year
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    year = Column(Integer, nullable=False, index=True)
    
    # Phenology dates
    start_of_season = Column(DateTime)  # SoS
    peak_of_season = Column(DateTime)   # PoS
    end_of_season = Column(DateTime)    # EoS
    
    # Phenology metrics
    growing_season_length = Column(Integer)  # days
    seasonal_amplitude = Column(Float)       # max - min NDVI
    peak_ndvi_value = Column(Float)
    baseline_ndvi_value = Column(Float)
    
    # Rate of change metrics
    green_up_rate = Column(Float)    # NDVI increase rate
    senescence_rate = Column(Float)  # NDVI decrease rate
    
    # Confidence and quality
    confidence_score = Column(Float)
    data_completeness = Column(Float)  # percentage of valid observations
    
    # Climate context
    temperature_sum = Column(Float)      # growing degree days
    precipitation_sum = Column(Float)    # total precipitation
    drought_stress_days = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            'year': self.year,
            'phenology_dates': {
                'start_of_season': self.start_of_season.isoformat() if self.start_of_season else None,
                'peak_of_season': self.peak_of_season.isoformat() if self.peak_of_season else None,
                'end_of_season': self.end_of_season.isoformat() if self.end_of_season else None
            },
            'metrics': {
                'growing_season_length': self.growing_season_length,
                'seasonal_amplitude': self.seasonal_amplitude,
                'peak_ndvi': self.peak_ndvi_value,
                'baseline_ndvi': self.baseline_ndvi_value
            },
            'rates': {
                'green_up_rate': self.green_up_rate,
                'senescence_rate': self.senescence_rate
            },
            'quality': {
                'confidence_score': self.confidence_score,
                'data_completeness': self.data_completeness
            },
            'climate': {
                'temperature_sum': self.temperature_sum,
                'precipitation_sum': self.precipitation_sum,
                'drought_stress_days': self.drought_stress_days
            }
        }

class SpeciesIdentification(db.Model):
    """Model for storing species identification results"""
    __tablename__ = 'species_identifications'
    
    id = Column(Integer, primary_key=True)
    
    # Location
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    
    # Species information
    species_name = Column(String(255), nullable=False)
    scientific_name = Column(String(255))
    confidence_score = Column(Float)
    
    # Identification basis
    bloom_characteristics = Column(JSON)
    climate_zone = Column(String(50))
    habitat_type = Column(String(100))
    
    # Ecological information
    economic_importance = Column(String(20))  # very_high, high, medium, low
    pollinator_value = Column(String(20))     # very_high, high, medium, low
    conservation_status = Column(String(50))
    
    # Bloom timing for this species
    typical_bloom_months = Column(JSON)
    bloom_duration_range = Column(JSON)
    
    # Verification status
    verified_by_expert = Column(Boolean, default=False)
    verification_date = Column(DateTime)
    verification_notes = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            'species': {
                'name': self.species_name,
                'scientific_name': self.scientific_name,
                'confidence': self.confidence_score
            },
            'identification': {
                'bloom_characteristics': self.bloom_characteristics,
                'climate_zone': self.climate_zone,
                'habitat_type': self.habitat_type
            },
            'ecological_info': {
                'economic_importance': self.economic_importance,
                'pollinator_value': self.pollinator_value,
                'conservation_status': self.conservation_status
            },
            'bloom_timing': {
                'typical_months': self.typical_bloom_months,
                'duration_range': self.bloom_duration_range
            },
            'verification': {
                'verified': self.verified_by_expert,
                'verification_date': self.verification_date.isoformat() if self.verification_date else None,
                'notes': self.verification_notes
            }
        }

class BloomForecast(db.Model):
    """Model for storing bloom forecasts"""
    __tablename__ = 'bloom_forecasts'
    
    id = Column(Integer, primary_key=True)
    
    # Location
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    
    # Forecast details
    forecast_date = Column(DateTime, nullable=False, index=True)  # When forecast was made
    forecast_for_date = Column(DateTime, nullable=False, index=True)  # Date being forecasted
    forecast_horizon_days = Column(Integer)
    
    # Predicted bloom characteristics
    bloom_probability = Column(Float)
    predicted_peak_ndvi = Column(Float)
    predicted_peak_evi = Column(Float)
    predicted_intensity = Column(Float)
    
    # Uncertainty bounds
    ndvi_uncertainty_range = Column(JSON)  # [min, max]
    date_uncertainty_days = Column(Integer)
    
    # Forecast model information
    model_version = Column(String(50))
    input_data_quality = Column(Float)
    historical_data_years = Column(Integer)
    
    # Climate factors
    temperature_forecast = Column(Float)
    precipitation_forecast = Column(Float)
    climate_anomaly_score = Column(Float)
    
    # Validation (after the fact)
    actual_bloom_occurred = Column(Boolean)
    actual_peak_ndvi = Column(Float)
    forecast_accuracy_score = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    validated_at = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'location': {
                'latitude': self.latitude,
                'longitude': self.longitude
            },
            'forecast_info': {
                'forecast_date': self.forecast_date.isoformat() if self.forecast_date else None,
                'forecast_for_date': self.forecast_for_date.isoformat() if self.forecast_for_date else None,
                'horizon_days': self.forecast_horizon_days
            },
            'predictions': {
                'bloom_probability': self.bloom_probability,
                'predicted_peak_ndvi': self.predicted_peak_ndvi,
                'predicted_peak_evi': self.predicted_peak_evi,
                'predicted_intensity': self.predicted_intensity
            },
            'uncertainty': {
                'ndvi_range': self.ndvi_uncertainty_range,
                'date_uncertainty_days': self.date_uncertainty_days
            },
            'model_info': {
                'version': self.model_version,
                'data_quality': self.input_data_quality,
                'historical_years': self.historical_data_years
            },
            'climate_factors': {
                'temperature_forecast': self.temperature_forecast,
                'precipitation_forecast': self.precipitation_forecast,
                'climate_anomaly': self.climate_anomaly_score
            },
            'validation': {
                'actual_bloom': self.actual_bloom_occurred,
                'actual_peak_ndvi': self.actual_peak_ndvi,
                'accuracy_score': self.forecast_accuracy_score,
                'validated_at': self.validated_at.isoformat() if self.validated_at else None
            }
        }

class BeeFarmingAlert(db.Model):
    """Model for storing bee farming specific alerts"""
    __tablename__ = 'bee_farming_alerts'
    
    id = Column(Integer, primary_key=True)
    
    # Apiary location
    apiary_latitude = Column(Float, nullable=False, index=True)
    apiary_longitude = Column(Float, nullable=False, index=True)
    apiary_name = Column(String(255))
    
    # Bloom location
    bloom_latitude = Column(Float, nullable=False)
    bloom_longitude = Column(Float, nullable=False)
    distance_km = Column(Float)
    
    # Alert details
    alert_type = Column(String(50))  # bloom_start, peak_bloom, move_hives, harvest_honey
    priority = Column(String(20))    # urgent, high, medium, low
    alert_date = Column(DateTime, nullable=False, index=True)
    
    # Bloom information
    species_name = Column(String(255))
    bloom_start_date = Column(DateTime)
    bloom_peak_date = Column(DateTime)
    bloom_end_date = Column(DateTime)
    
    # Bee farming metrics
    nectar_flow_rating = Column(String(20))
    pollen_quality = Column(String(20))
    expected_honey_yield_kg = Column(Float)
    
    # Economic analysis
    estimated_revenue = Column(Float)
    movement_cost = Column(Float)
    net_benefit = Column(Float)
    roi_percentage = Column(Float)
    
    # Weather considerations
    weather_risk = Column(String(20))  # low, medium, high
    optimal_move_date = Column(DateTime)
    
    # Alert status
    alert_sent = Column(Boolean, default=False)
    alert_acknowledged = Column(Boolean, default=False)
    action_taken = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    acknowledged_at = Column(DateTime)
    action_taken_at = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'apiary': {
                'latitude': self.apiary_latitude,
                'longitude': self.apiary_longitude,
                'name': self.apiary_name
            },
            'bloom_location': {
                'latitude': self.bloom_latitude,
                'longitude': self.bloom_longitude,
                'distance_km': self.distance_km
            },
            'alert': {
                'type': self.alert_type,
                'priority': self.priority,
                'date': self.alert_date.isoformat() if self.alert_date else None
            },
            'bloom_info': {
                'species': self.species_name,
                'start_date': self.bloom_start_date.isoformat() if self.bloom_start_date else None,
                'peak_date': self.bloom_peak_date.isoformat() if self.bloom_peak_date else None,
                'end_date': self.bloom_end_date.isoformat() if self.bloom_end_date else None
            },
            'bee_metrics': {
                'nectar_flow': self.nectar_flow_rating,
                'pollen_quality': self.pollen_quality,
                'expected_yield_kg': self.expected_honey_yield_kg
            },
            'economics': {
                'estimated_revenue': self.estimated_revenue,
                'movement_cost': self.movement_cost,
                'net_benefit': self.net_benefit,
                'roi_percentage': self.roi_percentage
            },
            'weather': {
                'risk': self.weather_risk,
                'optimal_move_date': self.optimal_move_date.isoformat() if self.optimal_move_date else None
            },
            'status': {
                'sent': self.alert_sent,
                'acknowledged': self.alert_acknowledged,
                'action_taken': self.action_taken,
                'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
                'action_taken_at': self.action_taken_at.isoformat() if self.action_taken_at else None
            }
        }

# Database initialization function
def init_db(app):
    """Initialize database with Flask app"""
    db.init_app(app)
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        print("Database tables created successfully!")
        print("Tables:", db.metadata.tables.keys())

# Helper functions for database operations
class DatabaseHelper:
    """Helper class for common database operations"""
    
    @staticmethod
    def save_bloom_event(bloom_data, location):
        """Save a detected bloom event to database"""
        try:
            bloom_event = BloomEvent(
                latitude=location['latitude'],
                longitude=location['longitude'],
                location_name=location.get('name'),
                start_date=datetime.fromisoformat(bloom_data['start_date']),
                peak_date=datetime.fromisoformat(bloom_data['peak_date']),
                end_date=datetime.fromisoformat(bloom_data['end_date']),
                duration_days=bloom_data['duration_days'],
                peak_ndvi=bloom_data['peak_ndvi'],
                peak_evi=bloom_data['peak_evi'],
                bloom_intensity=bloom_data['bloom_intensity'],
                confidence_score=bloom_data['confidence_score'],
                detection_method=bloom_data['detection_method'],
                bloom_stage=bloom_data['bloom_stage'],
                species_hints=bloom_data.get('species_hints'),
                data_source='MODIS'
            )
            
            db.session.add(bloom_event)
            db.session.commit()
            
            return bloom_event.id
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @staticmethod
    def get_bloom_events_in_radius(latitude, longitude, radius_km, start_date=None, end_date=None):
        """Get bloom events within radius of a location"""
        # Simple bounding box query (for more accuracy, use PostGIS)
        lat_delta = radius_km / 111.0  # Approximate km per degree latitude
        lng_delta = radius_km / (111.0 * abs(latitude))  # Adjust for longitude
        
        query = BloomEvent.query.filter(
            BloomEvent.latitude.between(latitude - lat_delta, latitude + lat_delta),
            BloomEvent.longitude.between(longitude - lng_delta, longitude + lng_delta)
        )
        
        if start_date:
            query = query.filter(BloomEvent.peak_date >= start_date)
        if end_date:
            query = query.filter(BloomEvent.peak_date <= end_date)
        
        return query.all()
    
    @staticmethod
    def save_vegetation_indices(location, date, satellite, indices):
        """Save vegetation index data"""
        try:
            vi_record = VegetationIndex(
                latitude=location['latitude'],
                longitude=location['longitude'],
                observation_date=date,
                satellite=satellite,
                ndvi=indices.get('ndvi'),
                evi=indices.get('evi'),
                savi=indices.get('savi'),
                ndwi=indices.get('ndwi')
            )
            
            db.session.add(vi_record)
            db.session.commit()
            
            return vi_record.id
            
        except Exception as e:
            db.session.rollback()
            raise e
