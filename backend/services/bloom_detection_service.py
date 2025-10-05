"""
Bloom Detection Service
Advanced algorithms for detecting bloom events from vegetation indices
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from scipy import signal
from scipy.stats import zscore
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import logging

logger = logging.getLogger(__name__)

class BloomDetectionService:
    """Service for detecting bloom events from vegetation index time series"""
    
    def __init__(self):
        self.ndvi_bloom_threshold = 0.4
        self.evi_bloom_threshold = 0.3
        self.min_bloom_duration = 14  # days
        self.max_bloom_duration = 120  # days
        
    def detect_bloom_events(
        self, 
        vegetation_data: Dict, 
        latitude: float, 
        longitude: float
    ) -> List[Dict]:
        """
        Detect bloom events from vegetation index time series
        
        Args:
            vegetation_data: Dictionary containing time series data
            latitude: Latitude of the location
            longitude: Longitude of the location
            
        Returns:
            List of detected bloom events
        """
        try:
            time_series = vegetation_data.get('time_series', [])
            
            if not time_series:
                return []
            
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(time_series)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # Clean and interpolate missing values
            df = self._clean_time_series(df)
            
            # Apply smoothing to reduce noise
            df = self._smooth_time_series(df)
            
            # Detect bloom events using multiple methods
            bloom_events = []
            
            # Method 1: Threshold-based detection
            threshold_blooms = self._detect_threshold_blooms(df)
            bloom_events.extend(threshold_blooms)
            
            # Method 2: Peak detection
            peak_blooms = self._detect_peak_blooms(df)
            bloom_events.extend(peak_blooms)
            
            # Method 3: Change point detection
            change_point_blooms = self._detect_change_point_blooms(df)
            bloom_events.extend(change_point_blooms)
            
            # Merge overlapping events and filter by duration
            merged_blooms = self._merge_bloom_events(bloom_events)
            
            # Add location and confidence information
            final_blooms = []
            for bloom in merged_blooms:
                bloom_info = {
                    'id': f"bloom_{latitude}_{longitude}_{bloom['start_date']}",
                    'location': {'latitude': latitude, 'longitude': longitude},
                    'start_date': bloom['start_date'],
                    'peak_date': bloom['peak_date'],
                    'end_date': bloom['end_date'],
                    'duration_days': bloom['duration_days'],
                    'peak_ndvi': bloom['peak_ndvi'],
                    'peak_evi': bloom['peak_evi'],
                    'bloom_intensity': bloom['bloom_intensity'],
                    'confidence_score': bloom['confidence_score'],
                    'detection_method': bloom['detection_method'],
                    'bloom_stage': self._determine_bloom_stage(bloom, df),
                    'species_hints': self._get_species_hints(bloom, latitude)
                }
                final_blooms.append(bloom_info)
            
            return final_blooms
            
        except Exception as e:
            logger.error(f"Error detecting bloom events: {str(e)}")
            return []
    
    def forecast_bloom_events(
        self, 
        historical_data: Dict, 
        latitude: float, 
        longitude: float, 
        forecast_days: int = 30
    ) -> Dict:
        """
        Forecast bloom events for the next N days based on historical patterns
        
        Args:
            historical_data: Historical vegetation index data
            latitude: Latitude of the location
            longitude: Longitude of the location
            forecast_days: Number of days to forecast
            
        Returns:
            Dictionary containing bloom forecast
        """
        try:
            time_series = historical_data.get('time_series', [])
            
            if not time_series or len(time_series) < 50:  # Need sufficient data
                return {'error': 'Insufficient historical data for forecasting'}
            
            # Convert to DataFrame
            df = pd.DataFrame(time_series)
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
            
            # Clean and smooth data
            df = self._clean_time_series(df)
            df = self._smooth_time_series(df)
            
            # Extract seasonal patterns
            seasonal_patterns = self._extract_seasonal_patterns(df)
            
            # Predict future values using multiple methods
            forecast_data = self._generate_forecast(df, forecast_days, seasonal_patterns)
            
            # Detect potential bloom events in forecast
            forecast_blooms = self._detect_forecast_blooms(forecast_data, latitude)
            
            # Calculate forecast confidence
            confidence = self._calculate_forecast_confidence(df, seasonal_patterns)
            
            return {
                'forecast_period_days': forecast_days,
                'forecast_start_date': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
                'forecast_end_date': (datetime.now() + timedelta(days=forecast_days)).strftime('%Y-%m-%d'),
                'predicted_blooms': forecast_blooms,
                'forecast_confidence': confidence,
                'seasonal_patterns': seasonal_patterns,
                'forecast_data': forecast_data.to_dict('records')
            }
            
        except Exception as e:
            logger.error(f"Error forecasting bloom events: {str(e)}")
            return {'error': str(e)}
    
    def _clean_time_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and interpolate missing values in time series"""
        try:
            # Remove obvious outliers (values outside reasonable range)
            df.loc[df['ndvi'] < -1, 'ndvi'] = np.nan
            df.loc[df['ndvi'] > 1, 'ndvi'] = np.nan
            df.loc[df['evi'] < -1, 'evi'] = np.nan
            df.loc[df['evi'] > 1, 'evi'] = np.nan
            
            # Interpolate missing values
            df['ndvi'] = df['ndvi'].interpolate(method='linear', limit=3)
            df['evi'] = df['evi'].interpolate(method='linear', limit=3)
            
            # Remove remaining NaN values
            df = df.dropna(subset=['ndvi', 'evi'])
            
            return df
            
        except Exception as e:
            logger.error(f"Error cleaning time series: {str(e)}")
            return df
    
    def _smooth_time_series(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply smoothing to reduce noise in time series"""
        try:
            # Apply Savitzky-Golay filter for smoothing
            window_length = min(11, len(df) // 3)  # Adaptive window length
            if window_length % 2 == 0:
                window_length += 1  # Must be odd
            
            if window_length >= 5:
                df['ndvi_smooth'] = signal.savgol_filter(df['ndvi'], window_length, 3)
                df['evi_smooth'] = signal.savgol_filter(df['evi'], window_length, 3)
            else:
                df['ndvi_smooth'] = df['ndvi']
                df['evi_smooth'] = df['evi']
            
            return df
            
        except Exception as e:
            logger.error(f"Error smoothing time series: {str(e)}")
            df['ndvi_smooth'] = df['ndvi']
            df['evi_smooth'] = df['evi']
            return df
    
    def _detect_threshold_blooms(self, df: pd.DataFrame) -> List[Dict]:
        """Detect blooms using threshold-based method"""
        try:
            blooms = []
            
            # Find periods where both NDVI and EVI exceed thresholds
            bloom_mask = (df['ndvi_smooth'] > self.ndvi_bloom_threshold) & \
                        (df['evi_smooth'] > self.evi_bloom_threshold)
            
            # Find continuous bloom periods
            bloom_periods = self._find_continuous_periods(bloom_mask, df['date'])
            
            for start_idx, end_idx in bloom_periods:
                if end_idx - start_idx >= 2:  # Minimum 2 data points
                    bloom_data = df.iloc[start_idx:end_idx+1]
                    
                    # Find peak within bloom period
                    peak_idx = start_idx + bloom_data['ndvi_smooth'].idxmax() - bloom_data.index[0]
                    
                    bloom = {
                        'start_date': df.iloc[start_idx]['date'].strftime('%Y-%m-%d'),
                        'peak_date': df.iloc[peak_idx]['date'].strftime('%Y-%m-%d'),
                        'end_date': df.iloc[end_idx]['date'].strftime('%Y-%m-%d'),
                        'duration_days': (df.iloc[end_idx]['date'] - df.iloc[start_idx]['date']).days,
                        'peak_ndvi': float(df.iloc[peak_idx]['ndvi_smooth']),
                        'peak_evi': float(df.iloc[peak_idx]['evi_smooth']),
                        'bloom_intensity': float((df.iloc[peak_idx]['ndvi_smooth'] + df.iloc[peak_idx]['evi_smooth']) / 2),
                        'confidence_score': 0.7,
                        'detection_method': 'threshold'
                    }
                    blooms.append(bloom)
            
            return blooms
            
        except Exception as e:
            logger.error(f"Error in threshold bloom detection: {str(e)}")
            return []
    
    def _detect_peak_blooms(self, df: pd.DataFrame) -> List[Dict]:
        """Detect blooms using peak detection method"""
        try:
            blooms = []
            
            # Find peaks in NDVI time series
            ndvi_peaks, _ = signal.find_peaks(
                df['ndvi_smooth'], 
                height=self.ndvi_bloom_threshold,
                distance=3,  # Minimum 3 data points between peaks
                prominence=0.1
            )
            
            for peak_idx in ndvi_peaks:
                # Define bloom window around peak
                start_idx = max(0, peak_idx - 5)
                end_idx = min(len(df) - 1, peak_idx + 5)
                
                # Refine start and end based on NDVI values
                start_idx = self._find_bloom_start(df, peak_idx, start_idx)
                end_idx = self._find_bloom_end(df, peak_idx, end_idx)
                
                duration = (df.iloc[end_idx]['date'] - df.iloc[start_idx]['date']).days
                
                if self.min_bloom_duration <= duration <= self.max_bloom_duration:
                    bloom = {
                        'start_date': df.iloc[start_idx]['date'].strftime('%Y-%m-%d'),
                        'peak_date': df.iloc[peak_idx]['date'].strftime('%Y-%m-%d'),
                        'end_date': df.iloc[end_idx]['date'].strftime('%Y-%m-%d'),
                        'duration_days': duration,
                        'peak_ndvi': float(df.iloc[peak_idx]['ndvi_smooth']),
                        'peak_evi': float(df.iloc[peak_idx]['evi_smooth']),
                        'bloom_intensity': float((df.iloc[peak_idx]['ndvi_smooth'] + df.iloc[peak_idx]['evi_smooth']) / 2),
                        'confidence_score': 0.8,
                        'detection_method': 'peak'
                    }
                    blooms.append(bloom)
            
            return blooms
            
        except Exception as e:
            logger.error(f"Error in peak bloom detection: {str(e)}")
            return []
    
    def _detect_change_point_blooms(self, df: pd.DataFrame) -> List[Dict]:
        """Detect blooms using change point detection"""
        try:
            blooms = []
            
            # Calculate first derivative to find change points
            df['ndvi_diff'] = df['ndvi_smooth'].diff()
            df['evi_diff'] = df['evi_smooth'].diff()
            
            # Find significant increases (bloom start) and decreases (bloom end)
            ndvi_increase_threshold = df['ndvi_diff'].std() * 1.5
            ndvi_decrease_threshold = -df['ndvi_diff'].std() * 1.5
            
            increase_points = df[df['ndvi_diff'] > ndvi_increase_threshold].index.tolist()
            decrease_points = df[df['ndvi_diff'] < ndvi_decrease_threshold].index.tolist()
            
            # Match increase and decrease points to form bloom periods
            for start_idx in increase_points:
                # Find corresponding decrease point
                end_candidates = [idx for idx in decrease_points if idx > start_idx]
                if end_candidates:
                    end_idx = min(end_candidates)
                    
                    # Find peak between start and end
                    bloom_data = df.iloc[start_idx:end_idx+1]
                    peak_idx = start_idx + bloom_data['ndvi_smooth'].idxmax() - bloom_data.index[0]
                    
                    duration = (df.iloc[end_idx]['date'] - df.iloc[start_idx]['date']).days
                    
                    if (self.min_bloom_duration <= duration <= self.max_bloom_duration and
                        df.iloc[peak_idx]['ndvi_smooth'] > self.ndvi_bloom_threshold):
                        
                        bloom = {
                            'start_date': df.iloc[start_idx]['date'].strftime('%Y-%m-%d'),
                            'peak_date': df.iloc[peak_idx]['date'].strftime('%Y-%m-%d'),
                            'end_date': df.iloc[end_idx]['date'].strftime('%Y-%m-%d'),
                            'duration_days': duration,
                            'peak_ndvi': float(df.iloc[peak_idx]['ndvi_smooth']),
                            'peak_evi': float(df.iloc[peak_idx]['evi_smooth']),
                            'bloom_intensity': float((df.iloc[peak_idx]['ndvi_smooth'] + df.iloc[peak_idx]['evi_smooth']) / 2),
                            'confidence_score': 0.6,
                            'detection_method': 'change_point'
                        }
                        blooms.append(bloom)
            
            return blooms
            
        except Exception as e:
            logger.error(f"Error in change point bloom detection: {str(e)}")
            return []
    
    def _merge_bloom_events(self, bloom_events: List[Dict]) -> List[Dict]:
        """Merge overlapping bloom events and remove duplicates"""
        try:
            if not bloom_events:
                return []
            
            # Sort by start date
            sorted_blooms = sorted(bloom_events, key=lambda x: x['start_date'])
            
            merged = []
            current_bloom = sorted_blooms[0].copy()
            
            for bloom in sorted_blooms[1:]:
                current_end = datetime.strptime(current_bloom['end_date'], '%Y-%m-%d')
                bloom_start = datetime.strptime(bloom['start_date'], '%Y-%m-%d')
                
                # Check for overlap (within 7 days)
                if (bloom_start - current_end).days <= 7:
                    # Merge blooms
                    current_bloom['end_date'] = max(current_bloom['end_date'], bloom['end_date'])
                    current_bloom['peak_ndvi'] = max(current_bloom['peak_ndvi'], bloom['peak_ndvi'])
                    current_bloom['peak_evi'] = max(current_bloom['peak_evi'], bloom['peak_evi'])
                    current_bloom['bloom_intensity'] = max(current_bloom['bloom_intensity'], bloom['bloom_intensity'])
                    current_bloom['confidence_score'] = max(current_bloom['confidence_score'], bloom['confidence_score'])
                    
                    # Update duration
                    start_date = datetime.strptime(current_bloom['start_date'], '%Y-%m-%d')
                    end_date = datetime.strptime(current_bloom['end_date'], '%Y-%m-%d')
                    current_bloom['duration_days'] = (end_date - start_date).days
                else:
                    # No overlap, add current bloom and start new one
                    merged.append(current_bloom)
                    current_bloom = bloom.copy()
            
            # Add the last bloom
            merged.append(current_bloom)
            
            # Filter by minimum duration
            filtered = [bloom for bloom in merged if bloom['duration_days'] >= self.min_bloom_duration]
            
            return filtered
            
        except Exception as e:
            logger.error(f"Error merging bloom events: {str(e)}")
            return bloom_events
    
    def _find_continuous_periods(self, mask: pd.Series, dates: pd.Series) -> List[Tuple[int, int]]:
        """Find continuous periods where mask is True"""
        periods = []
        start_idx = None
        
        for i, is_bloom in enumerate(mask):
            if is_bloom and start_idx is None:
                start_idx = i
            elif not is_bloom and start_idx is not None:
                periods.append((start_idx, i - 1))
                start_idx = None
        
        # Handle case where bloom period extends to end of data
        if start_idx is not None:
            periods.append((start_idx, len(mask) - 1))
        
        return periods
    
    def _find_bloom_start(self, df: pd.DataFrame, peak_idx: int, initial_start: int) -> int:
        """Find the actual start of bloom by looking backwards from peak"""
        threshold = df.iloc[peak_idx]['ndvi_smooth'] * 0.5  # 50% of peak value
        
        for i in range(peak_idx - 1, initial_start - 1, -1):
            if df.iloc[i]['ndvi_smooth'] < threshold:
                return i + 1
        
        return initial_start
    
    def _find_bloom_end(self, df: pd.DataFrame, peak_idx: int, initial_end: int) -> int:
        """Find the actual end of bloom by looking forwards from peak"""
        threshold = df.iloc[peak_idx]['ndvi_smooth'] * 0.5  # 50% of peak value
        
        for i in range(peak_idx + 1, initial_end + 1):
            if df.iloc[i]['ndvi_smooth'] < threshold:
                return i - 1
        
        return initial_end
    
    def _determine_bloom_stage(self, bloom: Dict, df: pd.DataFrame) -> str:
        """Determine current bloom stage based on current date"""
        try:
            current_date = datetime.now().date()
            start_date = datetime.strptime(bloom['start_date'], '%Y-%m-%d').date()
            peak_date = datetime.strptime(bloom['peak_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(bloom['end_date'], '%Y-%m-%d').date()
            
            if current_date < start_date:
                return 'pre_bloom'
            elif start_date <= current_date < peak_date:
                return 'early_bloom'
            elif current_date == peak_date:
                return 'peak_bloom'
            elif peak_date < current_date <= end_date:
                return 'late_bloom'
            else:
                return 'post_bloom'
                
        except Exception:
            return 'unknown'
    
    def _get_species_hints(self, bloom: Dict, latitude: float) -> List[str]:
        """Get potential species based on bloom characteristics and location"""
        hints = []
        
        # Based on latitude (climate zone)
        abs_lat = abs(latitude)
        if abs_lat < 23.5:  # Tropical
            hints.extend(['Tropical flowering trees', 'Hibiscus', 'Bougainvillea'])
        elif abs_lat < 40:  # Subtropical
            hints.extend(['Cherry blossom', 'Citrus trees', 'Oleander'])
        elif abs_lat < 60:  # Temperate
            hints.extend(['Apple blossom', 'Wildflowers', 'Deciduous trees'])
        else:  # Arctic
            hints.extend(['Arctic willow', 'Tundra flowers'])
        
        # Based on bloom intensity
        if bloom['bloom_intensity'] > 0.8:
            hints.extend(['Agricultural crops', 'Orchard trees'])
        elif bloom['bloom_intensity'] > 0.6:
            hints.extend(['Wildflower meadows', 'Grasslands'])
        
        # Based on bloom duration
        if bloom['duration_days'] > 60:
            hints.extend(['Perennial flowers', 'Long-blooming shrubs'])
        elif bloom['duration_days'] < 30:
            hints.extend(['Annual flowers', 'Fruit tree blossoms'])
        
        return hints[:3]  # Return top 3 hints
    
    def _extract_seasonal_patterns(self, df: pd.DataFrame) -> Dict:
        """Extract seasonal patterns from historical data"""
        try:
            df['month'] = df['date'].dt.month
            df['day_of_year'] = df['date'].dt.dayofyear
            
            # Calculate monthly averages
            monthly_avg = df.groupby('month')[['ndvi_smooth', 'evi_smooth']].mean()
            
            # Find peak months
            peak_month = monthly_avg['ndvi_smooth'].idxmax()
            
            # Calculate seasonal amplitude
            amplitude = monthly_avg['ndvi_smooth'].max() - monthly_avg['ndvi_smooth'].min()
            
            return {
                'peak_month': int(peak_month),
                'seasonal_amplitude': float(amplitude),
                'monthly_averages': monthly_avg.to_dict(),
                'typical_bloom_period': {
                    'start_month': int((peak_month - 1) % 12 + 1),
                    'end_month': int((peak_month + 1) % 12 + 1)
                }
            }
            
        except Exception as e:
            logger.error(f"Error extracting seasonal patterns: {str(e)}")
            return {}
    
    def _generate_forecast(self, df: pd.DataFrame, forecast_days: int, seasonal_patterns: Dict) -> pd.DataFrame:
        """Generate forecast data using seasonal patterns and trends"""
        try:
            # Simple seasonal forecast based on historical patterns
            last_date = df['date'].max()
            forecast_dates = pd.date_range(
                start=last_date + timedelta(days=1),
                periods=forecast_days,
                freq='D'
            )
            
            forecast_data = []
            for date in forecast_dates:
                month = date.month
                
                # Get seasonal baseline from historical data
                if 'monthly_averages' in seasonal_patterns:
                    monthly_data = seasonal_patterns['monthly_averages']
                    baseline_ndvi = monthly_data.get('ndvi_smooth', {}).get(month, 0.3)
                    baseline_evi = monthly_data.get('evi_smooth', {}).get(month, 0.2)
                else:
                    baseline_ndvi = 0.3
                    baseline_evi = 0.2
                
                # Add some random variation
                ndvi_forecast = baseline_ndvi + np.random.normal(0, 0.05)
                evi_forecast = baseline_evi + np.random.normal(0, 0.03)
                
                forecast_data.append({
                    'date': date,
                    'ndvi_forecast': max(0, min(1, ndvi_forecast)),
                    'evi_forecast': max(0, min(1, evi_forecast))
                })
            
            return pd.DataFrame(forecast_data)
            
        except Exception as e:
            logger.error(f"Error generating forecast: {str(e)}")
            return pd.DataFrame()
    
    def _detect_forecast_blooms(self, forecast_df: pd.DataFrame, latitude: float) -> List[Dict]:
        """Detect potential bloom events in forecast data"""
        try:
            if forecast_df.empty:
                return []
            
            # Apply same detection logic as historical data
            bloom_mask = (forecast_df['ndvi_forecast'] > self.ndvi_bloom_threshold) & \
                        (forecast_df['evi_forecast'] > self.evi_bloom_threshold)
            
            bloom_periods = self._find_continuous_periods(bloom_mask, forecast_df['date'])
            
            forecast_blooms = []
            for start_idx, end_idx in bloom_periods:
                if end_idx - start_idx >= 2:
                    bloom_data = forecast_df.iloc[start_idx:end_idx+1]
                    peak_idx = start_idx + bloom_data['ndvi_forecast'].idxmax() - bloom_data.index[0]
                    
                    bloom = {
                        'start_date': forecast_df.iloc[start_idx]['date'].strftime('%Y-%m-%d'),
                        'peak_date': forecast_df.iloc[peak_idx]['date'].strftime('%Y-%m-%d'),
                        'end_date': forecast_df.iloc[end_idx]['date'].strftime('%Y-%m-%d'),
                        'duration_days': (forecast_df.iloc[end_idx]['date'] - forecast_df.iloc[start_idx]['date']).days,
                        'predicted_peak_ndvi': float(forecast_df.iloc[peak_idx]['ndvi_forecast']),
                        'predicted_peak_evi': float(forecast_df.iloc[peak_idx]['evi_forecast']),
                        'bloom_probability': 0.7,  # Base probability for forecast
                        'uncertainty_range': {
                            'ndvi_min': float(forecast_df.iloc[peak_idx]['ndvi_forecast'] - 0.1),
                            'ndvi_max': float(forecast_df.iloc[peak_idx]['ndvi_forecast'] + 0.1),
                            'date_uncertainty_days': 5
                        }
                    }
                    forecast_blooms.append(bloom)
            
            return forecast_blooms
            
        except Exception as e:
            logger.error(f"Error detecting forecast blooms: {str(e)}")
            return []
    
    def _calculate_forecast_confidence(self, df: pd.DataFrame, seasonal_patterns: Dict) -> float:
        """Calculate confidence level for the forecast"""
        try:
            # Base confidence on data quality and seasonal pattern strength
            data_quality = min(1.0, len(df) / 100)  # More data = higher confidence
            
            seasonal_strength = seasonal_patterns.get('seasonal_amplitude', 0)
            pattern_confidence = min(1.0, seasonal_strength * 2)
            
            # Combined confidence
            overall_confidence = (data_quality * 0.6 + pattern_confidence * 0.4)
            
            return round(overall_confidence, 2)
            
        except Exception:
            return 0.5  # Default moderate confidence
