"""
Species Identification Service
Identifies plant species based on bloom characteristics, location, and phenology
"""

import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import json
import logging

logger = logging.getLogger(__name__)

class SpeciesIdentificationService:
    """Service for identifying plant species from bloom and location data"""
    
    def __init__(self):
        # Load species database
        self.species_database = self._load_species_database()
        self.climate_zones = self._define_climate_zones()
        
    def identify_species(
        self, 
        latitude: float, 
        longitude: float, 
        bloom_events: List[Dict], 
        phenology_metrics: Dict
    ) -> Dict:
        """
        Identify potential species based on location and bloom characteristics
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            bloom_events: List of detected bloom events
            phenology_metrics: Phenology analysis results
            
        Returns:
            Dictionary containing species identification results
        """
        try:
            if not bloom_events:
                return self._get_location_based_species(latitude, longitude)
            
            # Get climate zone
            climate_zone = self._get_climate_zone(latitude)
            
            # Analyze bloom characteristics
            bloom_profile = self._analyze_bloom_profile(bloom_events)
            
            # Match against species database
            species_matches = self._match_species(
                climate_zone, bloom_profile, phenology_metrics, latitude, longitude
            )
            
            # Calculate confidence scores
            scored_matches = self._calculate_species_confidence(
                species_matches, bloom_profile, climate_zone
            )
            
            # Get top matches
            top_species = sorted(scored_matches, key=lambda x: x['confidence'], reverse=True)[:5]
            
            return {
                'location': {'latitude': latitude, 'longitude': longitude},
                'climate_zone': climate_zone,
                'bloom_profile': bloom_profile,
                'species_matches': top_species,
                'identification_confidence': top_species[0]['confidence'] if top_species else 0.0,
                'ecological_context': self._get_ecological_context(latitude, longitude, top_species)
            }
            
        except Exception as e:
            logger.error(f"Error in species identification: {str(e)}")
            return {'error': str(e)}
    
    def identify_species_detailed(
        self, 
        latitude: float, 
        longitude: float, 
        bloom_characteristics: Dict
    ) -> Dict:
        """
        Detailed species identification from specific bloom characteristics
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            bloom_characteristics: Detailed bloom characteristics
            
        Returns:
            Detailed species identification results
        """
        try:
            climate_zone = self._get_climate_zone(latitude)
            
            # Extract characteristics
            peak_ndvi = bloom_characteristics.get('peak_ndvi', 0.5)
            bloom_duration = bloom_characteristics.get('bloom_duration', 30)
            bloom_timing = bloom_characteristics.get('bloom_timing', datetime.now().strftime('%Y-%m-%d'))
            
            # Convert bloom timing to day of year
            bloom_date = datetime.strptime(bloom_timing, '%Y-%m-%d')
            bloom_doy = bloom_date.timetuple().tm_yday
            
            # Create bloom profile
            bloom_profile = {
                'peak_intensity': peak_ndvi,
                'duration_days': bloom_duration,
                'bloom_day_of_year': bloom_doy,
                'bloom_month': bloom_date.month
            }
            
            # Match species
            species_matches = []
            for species in self.species_database:
                if climate_zone in species['climate_zones']:
                    match_score = self._calculate_detailed_match_score(species, bloom_profile)
                    if match_score > 0.3:  # Minimum threshold
                        species_matches.append({
                            'species_name': species['name'],
                            'scientific_name': species['scientific_name'],
                            'confidence': match_score,
                            'match_reasons': self._get_match_reasons(species, bloom_profile),
                            'species_info': species
                        })
            
            # Sort by confidence
            species_matches.sort(key=lambda x: x['confidence'], reverse=True)
            
            return {
                'location': {'latitude': latitude, 'longitude': longitude},
                'bloom_characteristics': bloom_characteristics,
                'climate_zone': climate_zone,
                'species_matches': species_matches[:3],  # Top 3 matches
                'confidence': species_matches[0]['confidence'] if species_matches else 0.0,
                'identification_method': 'detailed_characteristics'
            }
            
        except Exception as e:
            logger.error(f"Error in detailed species identification: {str(e)}")
            return {'error': str(e)}
    
    def _load_species_database(self) -> List[Dict]:
        """Load the species database with bloom characteristics"""
        return [
            {
                'name': 'Cherry Blossom',
                'scientific_name': 'Prunus serrulata',
                'climate_zones': ['temperate', 'subtropical'],
                'bloom_months': [3, 4, 5],
                'bloom_duration_range': [14, 35],
                'peak_ndvi_range': [0.6, 0.9],
                'peak_evi_range': [0.4, 0.7],
                'elevation_range': [0, 2000],
                'habitat': ['urban', 'forest', 'orchard'],
                'bloom_color': 'pink_white',
                'economic_importance': 'high',
                'pollinator_value': 'high'
            },
            {
                'name': 'Sunflower',
                'scientific_name': 'Helianthus annuus',
                'climate_zones': ['temperate', 'subtropical', 'arid'],
                'bloom_months': [6, 7, 8, 9],
                'bloom_duration_range': [30, 60],
                'peak_ndvi_range': [0.7, 0.95],
                'peak_evi_range': [0.5, 0.8],
                'elevation_range': [0, 1500],
                'habitat': ['agricultural', 'grassland'],
                'bloom_color': 'yellow',
                'economic_importance': 'very_high',
                'pollinator_value': 'very_high'
            },
            {
                'name': 'Apple Blossom',
                'scientific_name': 'Malus domestica',
                'climate_zones': ['temperate'],
                'bloom_months': [4, 5],
                'bloom_duration_range': [14, 28],
                'peak_ndvi_range': [0.6, 0.85],
                'peak_evi_range': [0.4, 0.65],
                'elevation_range': [0, 1000],
                'habitat': ['orchard', 'agricultural'],
                'bloom_color': 'white_pink',
                'economic_importance': 'very_high',
                'pollinator_value': 'high'
            },
            {
                'name': 'Wildflower Meadow',
                'scientific_name': 'Mixed species',
                'climate_zones': ['temperate', 'subtropical', 'mediterranean'],
                'bloom_months': [4, 5, 6, 7, 8],
                'bloom_duration_range': [45, 120],
                'peak_ndvi_range': [0.5, 0.8],
                'peak_evi_range': [0.3, 0.6],
                'elevation_range': [0, 2500],
                'habitat': ['grassland', 'meadow', 'prairie'],
                'bloom_color': 'mixed',
                'economic_importance': 'medium',
                'pollinator_value': 'very_high'
            },
            {
                'name': 'Tropical Hibiscus',
                'scientific_name': 'Hibiscus rosa-sinensis',
                'climate_zones': ['tropical', 'subtropical'],
                'bloom_months': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
                'bloom_duration_range': [90, 365],
                'peak_ndvi_range': [0.6, 0.9],
                'peak_evi_range': [0.4, 0.7],
                'elevation_range': [0, 800],
                'habitat': ['urban', 'tropical_forest', 'garden'],
                'bloom_color': 'red_pink_yellow',
                'economic_importance': 'medium',
                'pollinator_value': 'high'
            },
            {
                'name': 'Cotton',
                'scientific_name': 'Gossypium hirsutum',
                'climate_zones': ['subtropical', 'arid', 'temperate'],
                'bloom_months': [6, 7, 8],
                'bloom_duration_range': [45, 75],
                'peak_ndvi_range': [0.7, 0.9],
                'peak_evi_range': [0.5, 0.75],
                'elevation_range': [0, 1200],
                'habitat': ['agricultural'],
                'bloom_color': 'white_yellow',
                'economic_importance': 'very_high',
                'pollinator_value': 'medium'
            },
            {
                'name': 'Lavender',
                'scientific_name': 'Lavandula angustifolia',
                'climate_zones': ['mediterranean', 'temperate', 'arid'],
                'bloom_months': [6, 7, 8],
                'bloom_duration_range': [30, 60],
                'peak_ndvi_range': [0.4, 0.7],
                'peak_evi_range': [0.3, 0.5],
                'elevation_range': [0, 1800],
                'habitat': ['mediterranean', 'garden', 'agricultural'],
                'bloom_color': 'purple',
                'economic_importance': 'high',
                'pollinator_value': 'very_high'
            },
            {
                'name': 'Canola/Rapeseed',
                'scientific_name': 'Brassica napus',
                'climate_zones': ['temperate'],
                'bloom_months': [4, 5, 6],
                'bloom_duration_range': [25, 45],
                'peak_ndvi_range': [0.7, 0.9],
                'peak_evi_range': [0.5, 0.75],
                'elevation_range': [0, 1000],
                'habitat': ['agricultural'],
                'bloom_color': 'bright_yellow',
                'economic_importance': 'very_high',
                'pollinator_value': 'high'
            },
            {
                'name': 'Arctic Willow',
                'scientific_name': 'Salix arctica',
                'climate_zones': ['arctic', 'subarctic'],
                'bloom_months': [5, 6, 7],
                'bloom_duration_range': [14, 30],
                'peak_ndvi_range': [0.3, 0.6],
                'peak_evi_range': [0.2, 0.4],
                'elevation_range': [0, 3000],
                'habitat': ['tundra', 'alpine'],
                'bloom_color': 'yellow_catkins',
                'economic_importance': 'low',
                'pollinator_value': 'high'
            },
            {
                'name': 'Almond Blossom',
                'scientific_name': 'Prunus dulcis',
                'climate_zones': ['mediterranean', 'subtropical'],
                'bloom_months': [2, 3, 4],
                'bloom_duration_range': [14, 28],
                'peak_ndvi_range': [0.6, 0.8],
                'peak_evi_range': [0.4, 0.6],
                'elevation_range': [0, 1500],
                'habitat': ['orchard', 'agricultural'],
                'bloom_color': 'white_pink',
                'economic_importance': 'very_high',
                'pollinator_value': 'very_high'
            }
        ]
    
    def _define_climate_zones(self) -> Dict:
        """Define climate zones based on latitude"""
        return {
            'tropical': {'lat_range': [0, 23.5], 'description': 'Hot, humid, year-round growing season'},
            'subtropical': {'lat_range': [23.5, 35], 'description': 'Warm, distinct seasons'},
            'temperate': {'lat_range': [35, 50], 'description': 'Moderate climate, four seasons'},
            'subarctic': {'lat_range': [50, 66.5], 'description': 'Cold winters, short summers'},
            'arctic': {'lat_range': [66.5, 90], 'description': 'Very cold, short growing season'},
            'mediterranean': {'lat_range': [30, 45], 'description': 'Dry summers, mild winters'},
            'arid': {'lat_range': [15, 35], 'description': 'Low precipitation, high evaporation'}
        }
    
    def _get_climate_zone(self, latitude: float) -> str:
        """Determine climate zone based on latitude"""
        abs_lat = abs(latitude)
        
        if abs_lat <= 23.5:
            return 'tropical'
        elif abs_lat <= 35:
            return 'subtropical'
        elif abs_lat <= 50:
            return 'temperate'
        elif abs_lat <= 66.5:
            return 'subarctic'
        else:
            return 'arctic'
    
    def _analyze_bloom_profile(self, bloom_events: List[Dict]) -> Dict:
        """Analyze bloom events to create a profile"""
        if not bloom_events:
            return {}
        
        # Calculate average characteristics
        peak_ndvi_values = [event['peak_ndvi'] for event in bloom_events]
        peak_evi_values = [event['peak_evi'] for event in bloom_events]
        durations = [event['duration_days'] for event in bloom_events]
        intensities = [event['bloom_intensity'] for event in bloom_events]
        
        # Extract bloom months
        bloom_months = []
        for event in bloom_events:
            try:
                bloom_date = datetime.strptime(event['peak_date'], '%Y-%m-%d')
                bloom_months.append(bloom_date.month)
            except:
                continue
        
        return {
            'avg_peak_ndvi': np.mean(peak_ndvi_values),
            'avg_peak_evi': np.mean(peak_evi_values),
            'avg_duration': np.mean(durations),
            'avg_intensity': np.mean(intensities),
            'bloom_months': list(set(bloom_months)),
            'num_bloom_events': len(bloom_events),
            'ndvi_range': [min(peak_ndvi_values), max(peak_ndvi_values)],
            'evi_range': [min(peak_evi_values), max(peak_evi_values)]
        }
    
    def _match_species(
        self, 
        climate_zone: str, 
        bloom_profile: Dict, 
        phenology_metrics: Dict, 
        latitude: float, 
        longitude: float
    ) -> List[Dict]:
        """Match bloom profile against species database"""
        matches = []
        
        for species in self.species_database:
            # Check climate zone compatibility
            if climate_zone not in species['climate_zones']:
                continue
            
            # Check bloom month overlap
            if bloom_profile.get('bloom_months'):
                month_overlap = set(bloom_profile['bloom_months']) & set(species['bloom_months'])
                if not month_overlap:
                    continue
            
            # Check NDVI range compatibility
            if 'avg_peak_ndvi' in bloom_profile:
                ndvi_compatible = (
                    species['peak_ndvi_range'][0] <= bloom_profile['avg_peak_ndvi'] <= species['peak_ndvi_range'][1]
                )
                if not ndvi_compatible:
                    continue
            
            # Check duration compatibility
            if 'avg_duration' in bloom_profile:
                duration_compatible = (
                    species['bloom_duration_range'][0] <= bloom_profile['avg_duration'] <= species['bloom_duration_range'][1]
                )
                if not duration_compatible:
                    continue
            
            matches.append(species)
        
        return matches
    
    def _calculate_species_confidence(
        self, 
        species_matches: List[Dict], 
        bloom_profile: Dict, 
        climate_zone: str
    ) -> List[Dict]:
        """Calculate confidence scores for species matches"""
        scored_matches = []
        
        for species in species_matches:
            confidence_factors = []
            
            # Climate zone match (base score)
            if climate_zone in species['climate_zones']:
                confidence_factors.append(0.3)
            
            # Bloom month match
            if bloom_profile.get('bloom_months'):
                month_overlap = set(bloom_profile['bloom_months']) & set(species['bloom_months'])
                month_score = len(month_overlap) / len(species['bloom_months'])
                confidence_factors.append(month_score * 0.25)
            
            # NDVI match
            if 'avg_peak_ndvi' in bloom_profile:
                ndvi_center = np.mean(species['peak_ndvi_range'])
                ndvi_range = species['peak_ndvi_range'][1] - species['peak_ndvi_range'][0]
                ndvi_distance = abs(bloom_profile['avg_peak_ndvi'] - ndvi_center)
                ndvi_score = max(0, 1 - (ndvi_distance / ndvi_range))
                confidence_factors.append(ndvi_score * 0.2)
            
            # Duration match
            if 'avg_duration' in bloom_profile:
                duration_center = np.mean(species['bloom_duration_range'])
                duration_range = species['bloom_duration_range'][1] - species['bloom_duration_range'][0]
                duration_distance = abs(bloom_profile['avg_duration'] - duration_center)
                duration_score = max(0, 1 - (duration_distance / duration_range))
                confidence_factors.append(duration_score * 0.15)
            
            # Intensity match (EVI)
            if 'avg_peak_evi' in bloom_profile:
                evi_center = np.mean(species['peak_evi_range'])
                evi_range = species['peak_evi_range'][1] - species['peak_evi_range'][0]
                evi_distance = abs(bloom_profile['avg_peak_evi'] - evi_center)
                evi_score = max(0, 1 - (evi_distance / evi_range))
                confidence_factors.append(evi_score * 0.1)
            
            # Calculate overall confidence
            total_confidence = sum(confidence_factors)
            
            scored_matches.append({
                'species_name': species['name'],
                'scientific_name': species['scientific_name'],
                'confidence': min(1.0, total_confidence),
                'habitat': species['habitat'],
                'economic_importance': species['economic_importance'],
                'pollinator_value': species['pollinator_value'],
                'bloom_color': species['bloom_color'],
                'species_data': species
            })
        
        return scored_matches
    
    def _calculate_detailed_match_score(self, species: Dict, bloom_profile: Dict) -> float:
        """Calculate detailed match score for specific bloom characteristics"""
        score_components = []
        
        # Month match
        if bloom_profile['bloom_month'] in species['bloom_months']:
            score_components.append(0.3)
        else:
            # Partial credit for adjacent months
            adjacent_months = [
                (bloom_profile['bloom_month'] - 1) % 12 + 1,
                (bloom_profile['bloom_month'] + 1) % 12 + 1
            ]
            if any(month in species['bloom_months'] for month in adjacent_months):
                score_components.append(0.15)
        
        # NDVI intensity match
        ndvi_min, ndvi_max = species['peak_ndvi_range']
        if ndvi_min <= bloom_profile['peak_intensity'] <= ndvi_max:
            score_components.append(0.25)
        else:
            # Partial credit based on distance
            ndvi_center = (ndvi_min + ndvi_max) / 2
            distance = abs(bloom_profile['peak_intensity'] - ndvi_center)
            max_distance = (ndvi_max - ndvi_min) / 2
            score_components.append(max(0, 0.25 * (1 - distance / max_distance)))
        
        # Duration match
        dur_min, dur_max = species['bloom_duration_range']
        if dur_min <= bloom_profile['duration_days'] <= dur_max:
            score_components.append(0.2)
        else:
            # Partial credit based on distance
            dur_center = (dur_min + dur_max) / 2
            distance = abs(bloom_profile['duration_days'] - dur_center)
            max_distance = (dur_max - dur_min) / 2
            score_components.append(max(0, 0.2 * (1 - distance / max_distance)))
        
        # Base habitat/climate compatibility
        score_components.append(0.25)  # Base score for being in database
        
        return sum(score_components)
    
    def _get_match_reasons(self, species: Dict, bloom_profile: Dict) -> List[str]:
        """Get reasons why this species matches the bloom profile"""
        reasons = []
        
        if bloom_profile['bloom_month'] in species['bloom_months']:
            reasons.append(f"Blooms in {datetime(2000, bloom_profile['bloom_month'], 1).strftime('%B')}")
        
        ndvi_min, ndvi_max = species['peak_ndvi_range']
        if ndvi_min <= bloom_profile['peak_intensity'] <= ndvi_max:
            reasons.append(f"NDVI intensity matches expected range ({ndvi_min:.2f}-{ndvi_max:.2f})")
        
        dur_min, dur_max = species['bloom_duration_range']
        if dur_min <= bloom_profile['duration_days'] <= dur_max:
            reasons.append(f"Bloom duration matches expected range ({dur_min}-{dur_max} days)")
        
        if species['economic_importance'] in ['high', 'very_high']:
            reasons.append("Economically important species")
        
        if species['pollinator_value'] in ['high', 'very_high']:
            reasons.append("High value for pollinators")
        
        return reasons
    
    def _get_location_based_species(self, latitude: float, longitude: float) -> Dict:
        """Get likely species based only on location when no bloom data is available"""
        climate_zone = self._get_climate_zone(latitude)
        
        # Get all species for this climate zone
        location_species = [
            species for species in self.species_database 
            if climate_zone in species['climate_zones']
        ]
        
        # Sort by economic importance and pollinator value
        importance_scores = {
            'very_high': 4, 'high': 3, 'medium': 2, 'low': 1
        }
        
        scored_species = []
        for species in location_species:
            score = (
                importance_scores.get(species['economic_importance'], 1) +
                importance_scores.get(species['pollinator_value'], 1)
            )
            scored_species.append({
                'species_name': species['name'],
                'scientific_name': species['scientific_name'],
                'confidence': min(1.0, score / 8),  # Normalize to 0-1
                'habitat': species['habitat'],
                'economic_importance': species['economic_importance'],
                'pollinator_value': species['pollinator_value']
            })
        
        scored_species.sort(key=lambda x: x['confidence'], reverse=True)
        
        return {
            'location': {'latitude': latitude, 'longitude': longitude},
            'climate_zone': climate_zone,
            'species_matches': scored_species[:5],
            'identification_method': 'location_based',
            'note': 'Species identification based on location only - bloom data needed for higher accuracy'
        }
    
    def _get_ecological_context(
        self, 
        latitude: float, 
        longitude: float, 
        species_matches: List[Dict]
    ) -> Dict:
        """Get ecological context for the identified species"""
        if not species_matches:
            return {}
        
        top_species = species_matches[0]
        
        # Determine ecosystem type
        climate_zone = self._get_climate_zone(latitude)
        
        ecosystem_info = {
            'climate_zone': climate_zone,
            'primary_habitat': top_species.get('habitat', ['unknown'])[0] if top_species.get('habitat') else 'unknown',
            'conservation_status': 'stable',  # Would be looked up in real implementation
            'ecosystem_services': [],
            'threats': [],
            'management_recommendations': []
        }
        
        # Add ecosystem services based on species type
        if top_species.get('pollinator_value') in ['high', 'very_high']:
            ecosystem_info['ecosystem_services'].append('Pollinator support')
        
        if top_species.get('economic_importance') in ['high', 'very_high']:
            ecosystem_info['ecosystem_services'].append('Economic value')
        
        # Add habitat-specific information
        primary_habitat = ecosystem_info['primary_habitat']
        if primary_habitat == 'agricultural':
            ecosystem_info['management_recommendations'].extend([
                'Monitor for optimal harvest timing',
                'Implement pollinator-friendly practices',
                'Consider integrated pest management'
            ])
        elif primary_habitat in ['grassland', 'meadow', 'prairie']:
            ecosystem_info['management_recommendations'].extend([
                'Maintain habitat connectivity',
                'Control invasive species',
                'Implement rotational management'
            ])
        elif primary_habitat == 'forest':
            ecosystem_info['management_recommendations'].extend([
                'Preserve old-growth areas',
                'Maintain forest health',
                'Monitor for climate change impacts'
            ])
        
        return ecosystem_info
