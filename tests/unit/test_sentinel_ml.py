"""
Stage 11: Comprehensive Unit Tests for Sentinel ML Components
Tests feature extraction, classification, anomaly detection, and inference
"""
import pytest
import json
from datetime import datetime

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from sentinel.ml.feature_extractor import FeatureExtractor
from sentinel.ml.payload_classifier import PayloadClassifier, generate_synthetic_training_data
from sentinel.ml.anomaly_detector import BehavioralAnomalyDetector
from sentinel.ml.inference_engine import InferenceEngine
from sentinel.ml.explainability import ExplainabilityEngine


class TestFeatureExtractor:
    """Test feature extraction pipeline"""
    
    def test_extract_basic_features(self):
        """Test basic feature extraction"""
        extractor = FeatureExtractor()
        
        evidence = {
            "session_id": "test_001",
            "har": {
                "log": {
                    "entries": [
                        {
                            "startedDateTime": "2025-11-08T22:00:00Z",
                            "time": 150,
                            "request": {
                                "method": "GET",
                                "url": "http://example.com/api?id=1",
                                "headers": [{"name": "User-Agent", "value": "test"}],
                                "queryString": [{"name": "id", "value": "1"}]
                            },
                            "response": {"status": 200, "bodySize": 1024}
                        }
                    ]
                }
            },
            "extracted_payloads": [],
            "enrichment": {"tags": [], "meta": {}}
        }
        
        features = extractor.extract(evidence)
        
        assert features is not None
        assert "session_id" in features
        assert features["session_id"] == "test_001"
        assert "n_requests" in features
        assert features["n_requests"] == 1
    
    def test_extract_sql_injection_features(self):
        """Test SQL injection feature detection"""
        extractor = FeatureExtractor()
        
        evidence = {
            "session_id": "test_sqli",
            "har": {"log": {"entries": []}},
            "extracted_payloads": [
                {"value": "1' OR '1'='1", "type": "sql_injection"}
            ],
            "enrichment": {"tags": [], "meta": {}}
        }
        
        features = extractor.extract(evidence)
        
        assert features["contains_sql_keywords"] == 1
        assert features["max_payload_entropy"] > 0
    
    def test_entropy_calculation(self):
        """Test entropy calculation"""
        extractor = FeatureExtractor()
        
        # Low entropy
        low_entropy = extractor._calculate_entropy("aaaaaaa")
        assert low_entropy < 1.0
        
        # High entropy
        high_entropy = extractor._calculate_entropy("a1b2c3d4!@#$%^&*()")
        assert high_entropy > 3.0


class TestPayloadClassifier:
    """Test payload classification"""
    
    def test_rule_based_sql_injection(self):
        """Test rule-based SQL injection detection"""
        classifier = PayloadClassifier()
        
        payloads = [
            "1' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--"
        ]
        
        for payload in payloads:
            result = classifier.predict(payload)
            assert result["class"] == "sql_injection"
            assert result["confidence"] > 0.5
    
    def test_rule_based_xss(self):
        """Test rule-based XSS detection"""
        classifier = PayloadClassifier()
        
        payloads = [
            "<script>alert(1)</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>"
        ]
        
        for payload in payloads:
            result = classifier.predict(payload)
            assert result["class"] == "xss"
            assert result["confidence"] > 0.5
    
    def test_rule_based_command_injection(self):
        """Test rule-based command injection detection"""
        classifier = PayloadClassifier()
        
        payloads = [
            "; cat /etc/passwd",
            "| whoami",
            "$(ls -la)"
        ]
        
        for payload in payloads:
            result = classifier.predict(payload)
            assert result["class"] == "command_injection"
            assert result["confidence"] > 0.5
    
    def test_benign_classification(self):
        """Test benign payload classification"""
        classifier = PayloadClassifier()
        
        payloads = [
            "john@example.com",
            "search query",
            "normal text"
        ]
        
        for payload in payloads:
            result = classifier.predict(payload)
            assert result["class"] == "benign"
    
    def test_training(self):
        """Test classifier training"""
        classifier = PayloadClassifier()
        
        # Generate synthetic training data
        training_data = generate_synthetic_training_data()
        
        # Train
        classifier.train(training_data)
        
        # Verify training
        assert hasattr(classifier, 'is_trained')
        # Note: is_trained may be False if sklearn not available


class TestAnomalyDetector:
    """Test behavioral anomaly detection"""
    
    def test_heuristic_scoring(self):
        """Test heuristic anomaly scoring"""
        detector = BehavioralAnomalyDetector()
        
        # Normal features
        normal_features = {
            "n_requests": 5,
            "request_rate_per_min": 10,
            "error_rate": 0.1,
            "contains_sql_keywords": 0,
            "max_payload_entropy": 3.0
        }
        
        normal_score = detector.score(normal_features)
        assert 0 <= normal_score <= 1
        assert normal_score < 0.5  # Should be low
        
        # Anomalous features
        anomalous_features = {
            "n_requests": 100,
            "request_rate_per_min": 150,
            "error_rate": 0.8,
            "contains_sql_keywords": 1,
            "contains_xss_patterns": 1,
            "max_payload_entropy": 7.8,
            "ua_changes": 10
        }
        
        anomalous_score = detector.score(anomalous_features)
        assert anomalous_score > 0.5  # Should be high


class TestInferenceEngine:
    """Test full inference pipeline"""
    
    def test_benign_session_analysis(self):
        """Test analysis of benign session"""
        engine = InferenceEngine()
        
        evidence = {
            "session_id": "benign_001",
            "har": {
                "log": {
                    "entries": [
                        {
                            "startedDateTime": "2025-11-08T22:00:00Z",
                            "time": 100,
                            "request": {
                                "method": "GET",
                                "url": "http://example.com/page",
                                "headers": [],
                                "queryString": []
                            },
                            "response": {"status": 200, "bodySize": 1024}
                        }
                    ]
                }
            },
            "extracted_payloads": [],
            "enrichment": {"tags": [], "meta": {}}
        }
        
        verdict = engine.analyze(evidence)
        
        assert verdict is not None
        assert "verdict" in verdict
        assert verdict["session_id"] == "benign_001"
        assert verdict["final_score"] < 0.5
    
    def test_malicious_session_analysis(self):
        """Test analysis of malicious session"""
        engine = InferenceEngine()
        
        evidence = {
            "session_id": "malicious_001",
            "har": {
                "log": {
                    "entries": [
                        {
                            "startedDateTime": "2025-11-08T22:00:00Z",
                            "time": 200,
                            "request": {
                                "method": "GET",
                                "url": "http://example.com/admin?id=1' OR '1'='1",
                                "headers": [],
                                "queryString": [{"name": "id", "value": "1' OR '1'='1"}]
                            },
                            "response": {"status": 500, "bodySize": 1024}
                        }
                    ] * 10  # Multiple similar requests
                }
            },
            "extracted_payloads": [
                {"value": "1' OR '1'='1", "type": "sql_injection"}
            ],
            "enrichment": {"tags": ["poi", "sql_injection"], "meta": {}}
        }
        
        verdict = engine.analyze(evidence)
        
        assert verdict["final_score"] > 0.5
        assert len(verdict["payload_predictions"]) > 0
        assert verdict["payload_predictions"][0]["class"] == "sql_injection"


class TestExplainability:
    """Test explainability engine"""
    
    def test_explanation_generation(self):
        """Test generating explanations"""
        engine = ExplainabilityEngine()
        
        features = {
            "contains_sql_keywords": 1,
            "max_payload_entropy": 7.5,
            "error_rate": 0.6,
            "request_rate_per_min": 75
        }
        
        verdict = {
            "session_id": "test_explain",
            "verdict": "simulate",
            "final_score": 0.88,
            "behavioral_score": 0.82,
            "payload_predictions": [
                {"class": "sql_injection", "confidence": 0.95}
            ]
        }
        
        explanation = engine.explain_verdict(features, verdict)
        
        assert explanation is not None
        assert "narrative" in explanation
        assert "feature_importances" in explanation
        assert len(explanation["feature_importances"]) > 0
    
    def test_shap_summary(self):
        """Test SHAP summary generation"""
        engine = ExplainabilityEngine()
        
        features = {"contains_sql_keywords": 1, "error_rate": 0.8}
        verdict = {"session_id": "test", "verdict": "simulate", "final_score": 0.9}
        
        explanation = engine.explain_verdict(features, verdict)
        
        assert "shap_summary" in explanation
        assert "top_positive_features" in explanation["shap_summary"]


# Pytest fixtures
@pytest.fixture
def sample_evidence():
    """Sample evidence for testing"""
    return {
        "session_id": "test_session",
        "har": {
            "log": {
                "entries": [
                    {
                        "startedDateTime": "2025-11-08T22:00:00Z",
                        "time": 150,
                        "request": {
                            "method": "GET",
                            "url": "http://example.com/api",
                            "headers": [],
                            "queryString": []
                        },
                        "response": {"status": 200, "bodySize": 1024}
                    }
                ]
            }
        },
        "extracted_payloads": [],
        "enrichment": {"tags": [], "meta": {}}
    }


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
