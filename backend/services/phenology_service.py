"""
Phenology Service
Advanced phenological analysis including Start/Peak/End of Season detection
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from scipy import signal
from scipy.stats import zscore
from sklearn.preprocessing import StandardScaler
import logging

logger = logging.getLogger(__name__)

class PhenologyService:
    """Service for phenological analysis of vegetation time series"""
    
    def __init__(self):
        # Phenology thresholds (percentage of seasonal amplitude)
        self.sos_threshold = 0.2  # Start of Season: 20% of amplitude above baseline
        self.eos_threshold = 0.2  # End of Season: 20% of amplitude above baseline
        self.peak_prominence = 0.1  # Minimum prominence for peak detection
        
        # Quality control parameters
        self.min_data_points = 10  # Minimum observations for analysis
        self.max_gap_days = 32     # Maximum gap in days for interpolation
        
    def calculate_phenology_metrics(self, vegetation_data: Dict) -> Dict:
        """
        Calculate comprehensive phenology metrics from vegetation time series
        
        Args:
            vegetation_data: Dictionary containing time series data
            
        Returns:
            Dictionary containing phenology metrics
        """
        try:
            time_series = vegetation_data.get('time_series', [])
            
            if not time_series or len(time_series) < self.min_data_points:
                return {'error': 'Insufficient data for phenology analysis'}
            
            # Convert to DataFrame
            df = pd.DataFrame(time_series)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # Clean and smooth data
            df = self._clean_and_smooth_data(df)
            
            if len(df) < self.min_data_points:
                return {'error': 'Insufficient valid data after cleaning'}
            
            # Calculate basic statistics
            basic_stats = self._calculate_basic_statistics(df)
            
            # Detect phenological phases
            phenology_phases = self._detect_phenology_phases(df, basic_stats)
            
            # Calculate rates of change
            change_rates = self._calculate_change_rates(df, phenology_phases)
            
            # Assess data quality
            quality_metrics = self._assess_data_quality(df, vegetation_data)
            
            # Combine all metrics
            phenology_metrics = {
                'basic_statistics': basic_stats,
                'phenology_phases': phenology_phases,
                'change_rates': change_rates,
                'quality_metrics': quality_metrics,
                'analysis_period': {
                    'start_date': df['date'].min().strftime('%Y-%m-%d'),
                    'end_date': df['date'].max().strftime('%Y-%m-%d'),
                    'total_days': (df['date'].max() - df['date'].min()).days,
                    'observations': len(df)
                }
            }
            
            return phenology_metrics
            
        except Exception as e:
            logger.error(f"Error calculating phenology metrics: {str(e)}")
            return {'error': str(e)}
    
    def get_annual_phenology_metrics(self, latitude: float, longitude: float, year: int) -> Dict:
        """
        Get comprehensive phenology metrics for a specific year and location
        
        Args:
            latitude: Latitude of the location
            longitude: Longitude of the location
            year: Year for analysis
            
        Returns:
            Dictionary containing annual phenology metrics
        """
        try:
            # This would typically fetch data from database or NASA service
            # For now, we'll simulate the analysis
            
            # Generate mock annual data for demonstration
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            
            # Create mock time series (in real implementation, this would come from NASA data)
            mock_data = self._generate_mock_annual_data(latitude, year)
            
            # Calculate phenology metrics
            phenology_metrics = self.calculate_phenology_metrics({'time_series': mock_data})
            
            # Add location and year context
            phenology_metrics['location'] = {'latitude': latitude, 'longitude': longitude}
            phenology_metrics['year'] = year
            phenology_metrics['climate_zone'] = self._get_climate_zone(latitude)
            
            # Add seasonal context
            phenology_metrics['seasonal_context'] = self._get_seasonal_context(latitude, year)
            
            return phenology_metrics
            
        except Exception as e:
            logger.error(f"Error getting annual phenology metrics: {str(e)}")
            return {'error': str(e)}
    
    def _clean_and_smooth_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and smooth vegetation index time series"""
        try:
            # Remove obvious outliers
            for col in ['ndvi', 'evi']:
                if col in df.columns:
                    # Remove values outside reasonable range
                    df.loc[df[col] < -1, col] = np.nan
                    df.loc[df[col] > 1, col] = np.nan
                    
                    # Remove statistical outliers (beyond 3 standard deviations)
                    z_scores = np.abs(zscore(df[col].dropna()))
                    df.loc[df[col].index[z_scores > 3], col] = np.nan
            
            # Interpolate missing values
            df['ndvi'] = df['ndvi'].interpolate(method='linear', limit=3)
            df['evi'] = df['evi'].interpolate(method='linear', limit=3)
            
            # Remove rows with remaining NaN values
            df = df.dropna(subset=['ndvi', 'evi'])
            
            # Apply smoothing if we have enough data points
            if len(df) >= 7:
                # Savitzky-Golay smoothing
                window_length = min(7, len(df) // 2)
                if window_length % 2 == 0:
                    window_length += 1
                
                if window_length >= 5:
                    df['ndvi_smooth'] = signal.savgol_filter(df['ndvi'], window_length, 3)
                    df['evi_smooth'] = signal.savgol_filter(df['evi'], window_length, 3)
                else:
                    df['ndvi_smooth'] = df['ndvi']
                    df['evi_smooth'] = df['evi']
            else:
                df['ndvi_smooth'] = df['ndvi']
                df['evi_smooth'] = df['evi']
            
            return df
            
        except Exception as e:
            logger.error(f"Error cleaning and smoothing data: {str(e)}")
            return df
    
    def _calculate_basic_statistics(self, df: pd.DataFrame) -> Dict:
        """Calculate basic statistical measures"""
        try:
            ndvi_values = df['ndvi_smooth'].values
            evi_values = df['evi_smooth'].values
            
            # Basic statistics
            stats = {
                'ndvi': {
                    'min': float(np.min(ndvi_values)),
                    'max': float(np.max(ndvi_values)),
                    'mean': float(np.mean(ndvi_values)),
                    'std': float(np.std(ndvi_values)),
                    'amplitude': float(np.max(ndvi_values) - np.min(ndvi_values))
                },
                'evi': {
                    'min': float(np.min(evi_values)),
                    'max': float(np.max(evi_values)),
                    'mean': float(np.mean(evi_values)),
                    'std': float(np.std(evi_values)),
                    'amplitude': float(np.max(evi_values) - np.min(evi_values))
                }
            }
            
            # Seasonal metrics
            stats['seasonal_metrics'] = {
                'coefficient_of_variation_ndvi': stats['ndvi']['std'] / stats['ndvi']['mean'] if stats['ndvi']['mean'] > 0 else 0,
                'coefficient_of_variation_evi': stats['evi']['std'] / stats['evi']['mean'] if stats['evi']['mean'] > 0 else 0,
                'vegetation_productivity': (stats['ndvi']['mean'] + stats['evi']['mean']) / 2,
                'seasonal_variability': (stats['ndvi']['amplitude'] + stats['evi']['amplitude']) / 2
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating basic statistics: {str(e)}")
            return {}
    
    def _detect_phenology_phases(self, df: pd.DataFrame, basic_stats: Dict) -> Dict:
        """Detect Start of Season, Peak of Season, and End of Season"""
        try:
            ndvi_values = df['ndvi_smooth'].values
            dates = df['date'].values
            
            # Get baseline and amplitude
            baseline = basic_stats['ndvi']['min']
            amplitude = basic_stats['ndvi']['amplitude']
            
            # Calculate thresholds
            sos_value = baseline + (amplitude * self.sos_threshold)
            eos_value = baseline + (amplitude * self.eos_threshold)
            
            # Find Start of Season (first crossing of threshold)
            sos_idx = None
            for i, ndvi in enumerate(ndvi_values):
                if ndvi >= sos_value:
                    sos_idx = i
                    break
            
            # Find Peak of Season (maximum NDVI)
            pos_idx = np.argmax(ndvi_values)
            
            # Find End of Season (last crossing of threshold after peak)
            eos_idx = None
            for i in range(pos_idx, len(ndvi_values)):
                if ndvi_values[i] < eos_value:
                    eos_idx = i
                    break
            
            # If no end found, use last data point
            if eos_idx is None:
                eos_idx = len(ndvi_values) - 1
            
            # Calculate derived metrics
            phases = {
                'start_of_season': {
                    'date': dates[sos_idx].strftime('%Y-%m-%d') if sos_idx is not None else None,
                    'day_of_year': dates[sos_idx].timetuple().tm_yday if sos_idx is not None else None,
                    'ndvi_value': float(ndvi_values[sos_idx]) if sos_idx is not None else None
                },
                'peak_of_season': {
                    'date': dates[pos_idx].strftime('%Y-%m-%d'),
                    'day_of_year': dates[pos_idx].timetuple().tm_yday,
                    'ndvi_value': float(ndvi_values[pos_idx])
                },
                'end_of_season': {
                    'date': dates[eos_idx].strftime('%Y-%m-%d') if eos_idx is not None else None,
                    'day_of_year': dates[eos_idx].timetuple().tm_yday if eos_idx is not None else None,
                    'ndvi_value': float(ndvi_values[eos_idx]) if eos_idx is not None else None
                }
            }
            
            # Calculate growing season length
            if sos_idx is not None and eos_idx is not None:
                growing_season_length = (dates[eos_idx] - dates[sos_idx]).days
                phases['growing_season_length'] = growing_season_length
            else:
                phases['growing_season_length'] = None
            
            # Calculate phase durations
            if sos_idx is not None:
                green_up_duration = (dates[pos_idx] - dates[sos_idx]).days
                phases['green_up_duration'] = green_up_duration
            else:
                phases['green_up_duration'] = None
            
            if eos_idx is not None:
                senescence_duration = (dates[eos_idx] - dates[pos_idx]).days
                phases['senescence_duration'] = senescence_duration
            else:
                phases['senescence_duration'] = None
            
            return phases
            
        except Exception as e:
            logger.error(f"Error detecting phenology phases: {str(e)}")
            return {}
    
    def _calculate_change_rates(self, df: pd.DataFrame, phenology_phases: Dict) -> Dict:
        """Calculate rates of vegetation change during different phases"""
        try:
            ndvi_values = df['ndvi_smooth'].values
            dates = df['date'].values
            
            # Calculate daily change rates
            daily_changes = np.diff(ndvi_values)
            date_diffs = np.diff([d.timestamp() for d in dates]) / (24 * 3600)  # Convert to days
            daily_rates = daily_changes / date_diffs
            
            # Overall statistics
            change_rates = {
                'overall': {
                    'mean_daily_change': float(np.mean(daily_rates)),
                    'max_daily_increase': float(np.max(daily_rates)),
                    'max_daily_decrease': float(np.min(daily_rates)),
                    'std_daily_change': float(np.std(daily_rates))
                }
            }
            
            # Phase-specific rates
            sos_date = phenology_phases.get('start_of_season', {}).get('date')
            pos_date = phenology_phases.get('peak_of_season', {}).get('date')
            eos_date = phenology_phases.get('end_of_season', {}).get('date')
            
            if sos_date and pos_date:
                # Green-up rate
                sos_dt = datetime.strptime(sos_date, '%Y-%m-%d')
                pos_dt = datetime.strptime(pos_date, '%Y-%m-%d')
                
                sos_idx = df[df['date'] == sos_dt].index[0] if len(df[df['date'] == sos_dt]) > 0 else None
                pos_idx = df[df['date'] == pos_dt].index[0] if len(df[df['date'] == pos_dt]) > 0 else None
                
                if sos_idx is not None and pos_idx is not None:
                    green_up_rates = daily_rates[sos_idx:pos_idx]
                    change_rates['green_up'] = {
                        'mean_rate': float(np.mean(green_up_rates)) if len(green_up_rates) > 0 else 0,
                        'max_rate': float(np.max(green_up_rates)) if len(green_up_rates) > 0 else 0
                    }
            
            if pos_date and eos_date:
                # Senescence rate
                pos_dt = datetime.strptime(pos_date, '%Y-%m-%d')
                eos_dt = datetime.strptime(eos_date, '%Y-%m-%d')
                
                pos_idx = df[df['date'] == pos_dt].index[0] if len(df[df['date'] == pos_dt]) > 0 else None
                eos_idx = df[df['date'] == eos_dt].index[0] if len(df[df['date'] == eos_dt]) > 0 else None
                
                if pos_idx is not None and eos_idx is not None:
                    senescence_rates = daily_rates[pos_idx:eos_idx]
                    change_rates['senescence'] = {
                        'mean_rate': float(np.mean(senescence_rates)) if len(senescence_rates) > 0 else 0,
                        'min_rate': float(np.min(senescence_rates)) if len(senescence_rates) > 0 else 0
                    }
            
            return change_rates
            
        except Exception as e:
            logger.error(f"Error calculating change rates: {str(e)}")
            return {}
    
    def _assess_data_quality(self, df: pd.DataFrame, original_data: Dict) -> Dict:
        """Assess the quality of the phenology analysis"""
        try:
            total_possible_obs = len(original_data.get('time_series', []))
            valid_obs = len(df)
            
            # Calculate temporal coverage
            if len(df) > 1:
                date_range = (df['date'].max() - df['date'].min()).days
                expected_obs = date_range / 16  # MODIS 16-day composites
                temporal_completeness = min(1.0, valid_obs / expected_obs) if expected_obs > 0 else 0
            else:
                temporal_completeness = 0
            
            # Calculate data gaps
            if len(df) > 1:
                date_diffs = df['date'].diff().dt.days.dropna()
                max_gap = date_diffs.max()
                mean_gap = date_diffs.mean()
                gap_count = len(date_diffs[date_diffs > self.max_gap_days])
            else:
                max_gap = mean_gap = gap_count = 0
            
            # Quality score (0-1)
            quality_factors = [
                min(1.0, valid_obs / 20),  # Sufficient observations
                temporal_completeness,      # Temporal coverage
                max(0, 1 - (gap_count / valid_obs)) if valid_obs > 0 else 0,  # Gap penalty
                min(1.0, df['ndvi_smooth'].std() / 0.2)  # Sufficient variability
            ]
            
            overall_quality = np.mean(quality_factors)
            
            quality_metrics = {
                'data_completeness': float(valid_obs / total_possible_obs) if total_possible_obs > 0 else 0,
                'temporal_completeness': float(temporal_completeness),
                'valid_observations': int(valid_obs),
                'total_observations': int(total_possible_obs),
                'max_gap_days': int(max_gap),
                'mean_gap_days': float(mean_gap),
                'large_gap_count': int(gap_count),
                'overall_quality_score': float(overall_quality),
                'quality_rating': self._get_quality_rating(overall_quality)
            }
            
            return quality_metrics
            
        except Exception as e:
            logger.error(f"Error assessing data quality: {str(e)}")
            return {'overall_quality_score': 0.0, 'quality_rating': 'poor'}
    
    def _get_quality_rating(self, quality_score: float) -> str:
        """Convert quality score to rating"""
        if quality_score >= 0.8:
            return 'excellent'
        elif quality_score >= 0.6:
            return 'good'
        elif quality_score >= 0.4:
            return 'fair'
        else:
            return 'poor'
    
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
    
    def _get_seasonal_context(self, latitude: float, year: int) -> Dict:
        """Get seasonal context for the analysis"""
        climate_zone = self._get_climate_zone(latitude)
        
        # Determine hemisphere
        hemisphere = 'northern' if latitude >= 0 else 'southern'
        
        # Expected growing season based on climate zone and hemisphere
        if climate_zone == 'tropical':
            expected_seasons = {
                'wet_season': [5, 6, 7, 8, 9, 10] if hemisphere == 'northern' else [11, 12, 1, 2, 3, 4],
                'dry_season': [11, 12, 1, 2, 3, 4] if hemisphere == 'northern' else [5, 6, 7, 8, 9, 10]
            }
        elif climate_zone in ['subtropical', 'temperate']:
            expected_seasons = {
                'growing_season': [3, 4, 5, 6, 7, 8, 9, 10] if hemisphere == 'northern' else [9, 10, 11, 12, 1, 2, 3, 4],
                'dormant_season': [11, 12, 1, 2] if hemisphere == 'northern' else [5, 6, 7, 8]
            }
        else:  # subarctic, arctic
            expected_seasons = {
                'short_growing_season': [5, 6, 7, 8, 9] if hemisphere == 'northern' else [11, 12, 1, 2, 3],
                'long_dormant_season': [10, 11, 12, 1, 2, 3, 4] if hemisphere == 'northern' else [4, 5, 6, 7, 8, 9, 10]
            }
        
        return {
            'climate_zone': climate_zone,
            'hemisphere': hemisphere,
            'expected_seasons': expected_seasons,
            'year': year
        }
    
    def _generate_mock_annual_data(self, latitude: float, year: int) -> List[Dict]:
        """Generate mock annual data for demonstration purposes"""
        # This is a placeholder - in real implementation, this would fetch actual NASA data
        
        # Create dates for the year (16-day intervals like MODIS)
        start_date = datetime(year, 1, 1)
        dates = [start_date + timedelta(days=i*16) for i in range(23)]  # ~23 observations per year
        
        # Generate seasonal pattern based on latitude
        climate_zone = self._get_climate_zone(latitude)
        hemisphere = 'northern' if latitude >= 0 else 'southern'
        
        mock_data = []
        for i, date in enumerate(dates):
            day_of_year = date.timetuple().tm_yday
            
            # Adjust for hemisphere
            if hemisphere == 'southern':
                day_of_year = (day_of_year + 182) % 365
            
            # Generate seasonal NDVI pattern
            if climate_zone == 'tropical':
                # Two peaks per year (wet seasons)
                base_ndvi = 0.4 + 0.3 * (np.sin(2 * np.pi * day_of_year / 365) + 
                                        0.5 * np.sin(4 * np.pi * day_of_year / 365))
            elif climate_zone in ['subtropical', 'temperate']:
                # Single peak in growing season
                base_ndvi = 0.2 + 0.5 * np.sin(2 * np.pi * (day_of_year - 90) / 365)
            else:  # subarctic, arctic
                # Short, intense growing season
                base_ndvi = 0.1 + 0.4 * np.sin(2 * np.pi * (day_of_year - 120) / 365) ** 2
            
            # Add noise
            ndvi = max(0, min(1, base_ndvi + np.random.normal(0, 0.05)))
            evi = max(0, min(1, ndvi * 0.8 + np.random.normal(0, 0.03)))
            
            mock_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'ndvi': round(ndvi, 4),
                'evi': round(evi, 4)
            })
        
        return mock_data
