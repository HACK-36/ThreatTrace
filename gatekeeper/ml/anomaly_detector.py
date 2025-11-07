"""
ML-based Anomaly Detection for Gatekeeper
Uses Isolation Forest and LSTM for request classification
"""
import numpy as np
import pickle
from typing import Dict, List, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os


class AnomalyDetector:
    """ML-based anomaly detection for HTTP requests"""
    
    def __init__(self, model_dir: str = None):
        self.model_dir = model_dir or os.path.join(os.path.dirname(__file__), 'models')
        self.isolation_forest = None
        self.scaler = None
        self.feature_names = []
        self.poi_threshold = 0.75  # Anomaly score threshold for POI tagging
        
        # Load or initialize models
        self._load_models()
    
    def _load_models(self):
        """Load pre-trained models or create new ones"""
        iso_forest_path = os.path.join(self.model_dir, 'isolation_forest.pkl')
        scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
        
        if os.path.exists(iso_forest_path) and os.path.exists(scaler_path):
            print(f"Loading models from {self.model_dir}")
            self.isolation_forest = joblib.load(iso_forest_path)
            self.scaler = joblib.load(scaler_path)
        else:
            print("Initializing new models (train with real data in production)")
            # Initialize with default parameters
            self.isolation_forest = IsolationForest(
                n_estimators=100,
                max_samples='auto',
                contamination=0.1,  # Expect 10% of traffic to be anomalous
                random_state=42,
                n_jobs=-1
            )
            self.scaler = StandardScaler()
            self._train_on_synthetic_data()
    
    def _train_on_synthetic_data(self):
        """Train on synthetic data for demo purposes"""
        # Generate synthetic "normal" traffic features
        np.random.seed(42)
        n_samples = 1000
        n_features = 102
        
        # Normal traffic: lower variance, centered around typical values
        normal_data = np.random.normal(loc=0.1, scale=0.2, size=(n_samples, n_features))
        
        # Fit scaler and model
        self.scaler.fit(normal_data)
        scaled_data = self.scaler.transform(normal_data)
        self.isolation_forest.fit(scaled_data)
        
        # Save models
        os.makedirs(self.model_dir, exist_ok=True)
        joblib.dump(self.isolation_forest, os.path.join(self.model_dir, 'isolation_forest.pkl'))
        joblib.dump(self.scaler, os.path.join(self.model_dir, 'scaler.pkl'))
        print(f"Models trained and saved to {self.model_dir}")
    
    def predict(self, features: Dict[str, float]) -> Tuple[float, bool]:
        """
        Predict anomaly score for a request
        
        Args:
            features: Dict of feature_name -> value (from FeatureExtractor)
            
        Returns:
            Tuple of (anomaly_score, is_poi)
            - anomaly_score: 0.0 (normal) to 1.0 (highly anomalous)
            - is_poi: True if should be tagged as Person of Interest
        """
        # Convert features dict to array
        feature_vector = self._features_to_array(features)
        
        # Scale features
        scaled_features = self.scaler.transform([feature_vector])
        
        # Get anomaly score from Isolation Forest
        # Score is between -1 (anomaly) and 1 (normal)
        iso_score = self.isolation_forest.score_samples(scaled_features)[0]
        
        # Convert to 0-1 range where 1 = anomaly
        anomaly_score = (1 - iso_score) / 2
        anomaly_score = max(0.0, min(1.0, anomaly_score))  # Clamp to [0, 1]
        
        # Determine if POI
        is_poi = anomaly_score >= self.poi_threshold
        
        return anomaly_score, is_poi
    
    def _features_to_array(self, features: Dict[str, float]) -> np.ndarray:
        """Convert features dict to numpy array"""
        if not self.feature_names:
            # First time: establish feature order
            self.feature_names = sorted(features.keys())
        
        # Ensure all features are present
        feature_vector = []
        for fname in self.feature_names:
            feature_vector.append(features.get(fname, 0.0))
        
        return np.array(feature_vector)
    
    def train_incremental(self, features_batch: List[Dict[str, float]], labels: List[bool]):
        """
        Incrementally train the model with new labeled data
        
        Args:
            features_batch: List of feature dicts
            labels: List of True (anomaly) / False (normal)
        """
        # Convert to arrays
        X = np.array([self._features_to_array(f) for f in features_batch])
        
        # Filter for normal traffic only (Isolation Forest is unsupervised)
        normal_indices = [i for i, label in enumerate(labels) if not label]
        if normal_indices:
            X_normal = X[normal_indices]
            
            # Partial fit scaler
            self.scaler.partial_fit(X_normal)
            
            # Note: Sklearn's IsolationForest doesn't support incremental learning
            # In production, use incremental algorithms or periodic retraining
            print(f"Received {len(features_batch)} samples for training (incremental training not fully implemented)")
    
    def save_models(self):
        """Save models to disk"""
        os.makedirs(self.model_dir, exist_ok=True)
        joblib.dump(self.isolation_forest, os.path.join(self.model_dir, 'isolation_forest.pkl'))
        joblib.dump(self.scaler, os.path.join(self.model_dir, 'scaler.pkl'))
        print(f"Models saved to {self.model_dir}")
    
    def get_model_info(self) -> Dict:
        """Get model metadata"""
        return {
            "model_type": "IsolationForest",
            "n_estimators": self.isolation_forest.n_estimators if self.isolation_forest else 0,
            "contamination": self.isolation_forest.contamination if self.isolation_forest else 0,
            "poi_threshold": self.poi_threshold,
            "feature_count": len(self.feature_names),
            "model_loaded": self.isolation_forest is not None
        }


class LSTMBehavioralClassifier:
    """
    LSTM-based behavioral classifier (placeholder)
    In production, this would use PyTorch/TensorFlow for sequence modeling
    """
    
    def __init__(self):
        self.model = None
        self.sequence_length = 10  # Last 10 requests in session
    
    def predict(self, session_history: List[Dict]) -> float:
        """
        Predict behavioral anomaly score based on session history
        
        Args:
            session_history: List of feature dicts from recent requests
            
        Returns:
            Behavioral anomaly score (0-1)
        """
        # Placeholder implementation
        # In production, this would use a trained LSTM model
        
        if len(session_history) < 3:
            return 0.0  # Not enough history
        
        # Simple heuristic: check for rapid pattern changes
        recent_scores = [req.get('ml_score', 0.0) for req in session_history[-self.sequence_length:]]
        
        if not recent_scores:
            return 0.0
        
        # High variance in scores = suspicious behavior
        variance = np.var(recent_scores)
        mean_score = np.mean(recent_scores)
        
        # Combine variance and mean for behavioral score
        behavioral_score = min(1.0, (variance * 2) + (mean_score * 0.5))
        
        return behavioral_score
    
    def train(self, sequences: List[List[Dict]], labels: List[bool]):
        """Train LSTM on labeled sequences (placeholder)"""
        print(f"LSTM training placeholder: {len(sequences)} sequences")
        # In production: implement proper LSTM training
        pass
