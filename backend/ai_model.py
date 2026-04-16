"""
AI Traffic Prediction Module
Smart City Navigator - AI-Based Smart City Navigation System

Uses Random Forest Regressor to predict traffic conditions and travel times
based on historical and simulated data.
"""

import numpy as np
import pandas as pd
import joblib
import os
from typing import Dict, Optional, Tuple
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


class TrafficPredictor:
    """
    AI-powered traffic prediction system using Random Forest Regression.
    
    Predicts:
    - Travel time based on various factors
    - Congestion levels
    - Traffic patterns
    """
    
    def __init__(self):
        self.model: Optional[RandomForestRegressor] = None
        self._model_loaded = False
        self._model_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "models",
            "traffic_model.pkl"
        )
        self._data_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "data",
            "traffic_dataset.csv"
        )
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize or load the prediction model"""
        if os.path.exists(self._model_path):
            try:
                self.model = joblib.load(self._model_path)
                self._model_loaded = True
                print(f"Loaded pre-trained model from {self._model_path}")
            except Exception as e:
                print(f"Error loading model: {e}")
                self.model = self._create_and_train_model()
        else:
            self.model = self._create_and_train_model()
    
    def is_model_loaded(self) -> bool:
        """Check if model is loaded"""
        return self._model_loaded and self.model is not None
    
    def _create_synthetic_data(self) -> pd.DataFrame:
        """
        Generate synthetic traffic data for training.
        
        Features:
        - hour: Hour of day (0-23)
        - day_of_week: Day of week (0-6)
        - road_type: Type of road (highway=0, arterial=1, local=2)
        - distance: Distance in kilometers
        - is_peak_hour: Whether it's peak hour (0 or 1)
        
        Target:
        - travel_time: Time to travel in minutes
        - congestion_level: Level of congestion (0-1)
        """
        np.random.seed(42)
        
        n_samples = 50000
        
        data = {
            'hour': np.random.randint(0, 24, n_samples),
            'day_of_week': np.random.randint(0, 7, n_samples),
            'road_type': np.random.randint(0, 3, n_samples),
            'distance': np.random.uniform(0.5, 50, n_samples),
            'is_peak_hour': np.zeros(n_samples, dtype=int)
        }
        
        data['is_peak_hour'] = ((data['hour'] >= 7) & (data['hour'] <= 9) | 
                                 (data['hour'] >= 17) & (data['hour'] <= 19)).astype(int)
        
        congestion_base = np.zeros(n_samples)
        
        for i in range(n_samples):
            hour = data['hour'][i]
            
            if 7 <= hour <= 9:
                congestion_base[i] = 0.6 + np.random.uniform(0, 0.3)
            elif 12 <= hour <= 14:
                congestion_base[i] = 0.4 + np.random.uniform(0, 0.2)
            elif 17 <= hour <= 19:
                congestion_base[i] = 0.7 + np.random.uniform(0, 0.3)
            elif 22 <= hour or hour <= 5:
                congestion_base[i] = 0.1 + np.random.uniform(0, 0.1)
            else:
                congestion_base[i] = 0.3 + np.random.uniform(0, 0.2)
            
            if data['road_type'][i] == 0:
                congestion_base[i] *= 1.2
            elif data['road_type'][i] == 2:
                congestion_base[i] *= 0.8
            
            if data['day_of_week'][i] >= 5:
                congestion_base[i] *= 0.7
            
            data['congestion_level'] = np.clip(congestion_base, 0, 1)
        
        travel_time_base = data['distance'] * 1.2
        
        speed_multiplier = {
            0: 1.0,
            1: 1.2,
            2: 1.5
        }
        
        data['travel_time'] = np.zeros(n_samples)
        for i in range(n_samples):
            base_time = data['distance'][i] * speed_multiplier[data['road_type'][i]]
            congestion_penalty = 1 + data['congestion_level'][i] * 1.5
            peak_penalty = 1.3 if data['is_peak_hour'][i] else 1.0
            data['travel_time'][i] = base_time * congestion_penalty * peak_penalty + np.random.uniform(-2, 2)
        
        df = pd.DataFrame(data)
        
        self._save_dataset(df)
        
        return df
    
    def _save_dataset(self, df: pd.DataFrame):
        """Save generated dataset"""
        os.makedirs(os.path.dirname(self._data_path), exist_ok=True)
        df.to_csv(self._data_path, index=False)
        print(f"Dataset saved to {self._data_path}")
    
    def _create_and_train_model(self) -> RandomForestRegressor:
        """Create and train the Random Forest model"""
        print("Creating and training new traffic prediction model...")
        
        df = self._create_synthetic_data()
        
        features = ['hour', 'day_of_week', 'road_type', 'distance', 'is_peak_hour']
        target_time = 'travel_time'
        target_congestion = 'congestion_level'
        
        X = df[features]
        y_time = df[target_time]
        y_congestion = df[target_congestion]
        
        X_train, X_test, y_time_train, y_time_test = train_test_split(
            X, y_time, test_size=0.2, random_state=42
        )
        
        _, _, y_congestion_train, y_congestion_test = train_test_split(
            X, y_congestion, test_size=0.2, random_state=42
        )
        
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        print("Training Random Forest model...")
        model.fit(X_train, y_time_train)
        
        y_pred = model.predict(X_test)
        mae = mean_absolute_error(y_time_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_time_test, y_pred))
        r2 = r2_score(y_time_test, y_pred)
        
        print(f"Model Training Complete!")
        print(f"  MAE: {mae:.2f} minutes")
        print(f"  RMSE: {rmse:.2f} minutes")
        print(f"  R² Score: {r2:.4f}")
        
        self._save_model(model)
        self._model_loaded = True
        
        return model
    
    def _save_model(self, model: RandomForestRegressor):
        """Save trained model to disk"""
        os.makedirs(os.path.dirname(self._model_path), exist_ok=True)
        joblib.dump(model, self._model_path)
        print(f"Model saved to {self._model_path}")
    
    def predict(
        self,
        hour: int,
        day_of_week: int,
        road_type: str,
        distance: float,
        is_peak_hour: bool = False
    ) -> Dict:
        """
        Predict traffic conditions based on input parameters.
        
        Args:
            hour: Hour of day (0-23)
            day_of_week: Day of week (0=Monday, 6=Sunday)
            road_type: Type of road (highway, arterial, local)
            distance: Distance in kilometers
            is_peak_hour: Whether it's during peak hours
        
        Returns:
            Dictionary containing:
            - travel_time: Estimated travel time in minutes
            - congestion_level: Predicted congestion (0-1)
            - confidence: Model confidence score
            - hour_factor, road_type_factor, peak_factor
        """
        if self.model is None:
            self._initialize_model()
        
        road_type_map = {
            'highway': 0,
            'arterial': 1,
            'local': 2
        }
        
        road_type_encoded = road_type_map.get(road_type.lower(), 1)
        
        features = np.array([[
            hour,
            day_of_week,
            road_type_encoded,
            distance,
            1 if is_peak_hour else 0
        ]])
        
        travel_time_pred = self.model.predict(features)[0]
        
        congestion_base = 0.2
        
        if 7 <= hour <= 9:
            congestion_base = 0.65
        elif 12 <= hour <= 14:
            congestion_base = 0.45
        elif 17 <= hour <= 19:
            congestion_base = 0.75
        elif 22 <= hour or hour <= 5:
            congestion_base = 0.1
        
        road_factor_map = {0: 1.2, 1: 1.0, 2: 0.8}
        congestion_base *= road_factor_map.get(road_type_encoded, 1.0)
        
        if is_peak_hour:
            congestion_base *= 1.3
        
        congestion_level = min(1.0, max(0.0, congestion_base))
        
        confidence = self._calculate_confidence(hour, day_of_week, is_peak_hour)
        
        hour_factor = congestion_base / 0.75 if congestion_base > 0 else 0
        road_type_factor = road_type_encoded / 2
        peak_factor = 1.3 if is_peak_hour else 1.0
        
        return {
            'travel_time': round(float(travel_time_pred), 2),
            'congestion_level': round(congestion_level, 3),
            'confidence': round(confidence, 3),
            'hour_factor': round(hour_factor, 3),
            'road_type_factor': round(road_type_factor, 3),
            'peak_factor': round(peak_factor, 3)
        }
    
    def _calculate_confidence(
        self,
        hour: int,
        day_of_week: int,
        is_peak_hour: bool
    ) -> float:
        """
        Calculate model confidence based on input characteristics.
        More common scenarios have higher confidence.
        """
        confidence = 0.8
        
        if 8 <= hour <= 18:
            confidence += 0.1
        
        if day_of_week in [0, 1, 2, 3, 4]:
            confidence += 0.05
        
        if is_peak_hour:
            confidence += 0.05
        
        return min(1.0, confidence)
    
    async def retrain(self, new_data: Optional[pd.DataFrame] = None) -> Dict:
        """
        Retrain the model with new data.
        
        Args:
            new_data: Optional new training data. If None, regenerates synthetic data.
        
        Returns:
            Dictionary with training metrics
        """
        print("Retraining traffic prediction model...")
        
        if new_data is None:
            new_data = self._create_synthetic_data()
        
        features = ['hour', 'day_of_week', 'road_type', 'distance', 'is_peak_hour']
        target = 'travel_time'
        
        X = new_data[features]
        y = new_data[target]
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        self.model = RandomForestRegressor(
            n_estimators=150,
            max_depth=20,
            min_samples_split=4,
            min_samples_leaf=2,
            random_state=42,
            n_jobs=-1
        )
        
        self.model.fit(X_train, y_train)
        
        y_pred = self.model.predict(X_test)
        
        metrics = {
            'mae': round(mean_absolute_error(y_test, y_pred), 4),
            'rmse': round(np.sqrt(mean_squared_error(y_test, y_pred)), 4),
            'r2': round(r2_score(y_test, y_pred), 4),
            'training_samples': len(X_train),
            'test_samples': len(X_test)
        }
        
        self._save_model(self.model)
        
        print(f"Retraining complete. Metrics: {metrics}")
        
        return metrics
    
    def get_feature_importance(self) -> Dict:
        """Get feature importance scores from the model"""
        if self.model is None:
            return {}
        
        features = ['hour', 'day_of_week', 'road_type', 'distance', 'is_peak_hour']
        importance = self.model.feature_importances_
        
        return {
            feature: round(float(imp), 4)
            for feature, imp in zip(features, importance)
        }
    
    def predict_batch(self, inputs: List[Dict]) -> List[Dict]:
        """Predict traffic for multiple inputs"""
        predictions = []
        
        for inp in inputs:
            pred = self.predict(
                hour=inp['hour'],
                day_of_week=inp['day_of_week'],
                road_type=inp['road_type'],
                distance=inp['distance'],
                is_peak_hour=inp.get('is_peak_hour', False)
            )
            predictions.append(pred)
        
        return predictions
    
    def get_traffic_patterns(self) -> Dict:
        """Get typical traffic patterns by hour"""
        patterns = {}
        
        for hour in range(24):
            is_peak = hour in [8, 9, 17, 18, 19]
            
            pred = self.predict(
                hour=hour,
                day_of_week=0,
                road_type='arterial',
                distance=10,
                is_peak_hour=is_peak
            )
            
            patterns[hour] = {
                'congestion_level': pred['congestion_level'],
                'travel_time_10km': pred['travel_time'],
                'is_peak': is_peak,
                'description': self._get_hour_description(hour)
            }
        
        return patterns
    
    def _get_hour_description(self, hour: int) -> str:
        """Get human-readable description for the hour"""
        descriptions = {
            0: "Midnight",
            1: "Late Night",
            2: "Late Night",
            3: "Late Night",
            4: "Early Morning",
            5: "Early Morning",
            6: "Early Morning",
            7: "Morning Rush",
            8: "Morning Rush",
            9: "Morning Rush",
            10: "Late Morning",
            11: "Late Morning",
            12: "Lunch Time",
            13: "Afternoon",
            14: "Afternoon",
            15: "Afternoon",
            16: "Evening Rush",
            17: "Evening Rush",
            18: "Evening Rush",
            19: "Evening",
            20: "Evening",
            21: "Night",
            22: "Night",
            23: "Night"
        }
        return descriptions.get(hour, "Unknown")
