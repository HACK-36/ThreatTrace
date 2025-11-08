"""
Event Bus for Cerberus - Kafka-based message streaming
Handles evidence pointers, telemetry, and cross-service events
"""
import os
import json
import logging
from typing import Optional, Callable, Dict, Any
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError

logger = logging.getLogger(__name__)


class CerberusEventBus:
    """
    Unified event bus for Cerberus components
    
    Topics:
    - cerberus.evidence.ready - Evidence pointer messages
    - cerberus.telemetry - Real-time telemetry events
    - cerberus.alerts - Security alerts
    """
    
    def __init__(
        self,
        bootstrap_servers: Optional[str] = None,
        client_id: Optional[str] = None
    ):
        """
        Initialize event bus
        
        Args:
            bootstrap_servers: Kafka broker addresses
            client_id: Client identifier for this service
        """
        self.bootstrap_servers = bootstrap_servers or os.getenv(
            "KAFKA_BOOTSTRAP_SERVERS",
            "localhost:9092"
        )
        self.client_id = client_id or "cerberus-client"
        
        self.producer: Optional[KafkaProducer] = None
        self.consumers: Dict[str, KafkaConsumer] = {}
        
        logger.info(f"Event bus initialized: {self.bootstrap_servers}")
    
    def get_producer(self) -> KafkaProducer:
        """Get or create Kafka producer"""
        if self.producer is None:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers.split(","),
                client_id=self.client_id,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1  # Ensure ordering
            )
            logger.info("Kafka producer created")
        return self.producer
    
    def publish(
        self,
        topic: str,
        message: Dict[str, Any],
        key: Optional[str] = None
    ) -> bool:
        """
        Publish message to topic
        
        Args:
            topic: Kafka topic name
            message: Message dict (will be JSON serialized)
            key: Optional message key for partitioning
            
        Returns:
            True if published successfully
        """
        try:
            producer = self.get_producer()
            
            key_bytes = key.encode('utf-8') if key else None
            
            future = producer.send(topic, value=message, key=key_bytes)
            record_metadata = future.get(timeout=10)
            
            logger.debug(
                f"Published to {topic} "
                f"(partition={record_metadata.partition}, "
                f"offset={record_metadata.offset})"
            )
            return True
        
        except KafkaError as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error publishing to {topic}: {e}")
            return False
    
    def publish_evidence_pointer(self, pointer_dict: Dict[str, Any]) -> bool:
        """
        Publish evidence pointer to dedicated topic
        
        Args:
            pointer_dict: Evidence pointer as dict
            
        Returns:
            True if published
        """
        return self.publish(
            "cerberus.evidence.ready",
            pointer_dict,
            key=pointer_dict.get("event_id")
        )
    
    def publish_telemetry(self, event_dict: Dict[str, Any]) -> bool:
        """
        Publish telemetry event
        
        Args:
            event_dict: Telemetry event dict
            
        Returns:
            True if published
        """
        return self.publish(
            "cerberus.telemetry",
            event_dict,
            key=event_dict.get("session_id")
        )
    
    def publish_alert(self, alert_dict: Dict[str, Any]) -> bool:
        """
        Publish security alert
        
        Args:
            alert_dict: Alert dict
            
        Returns:
            True if published
        """
        return self.publish(
            "cerberus.alerts",
            alert_dict,
            key=alert_dict.get("event_id")
        )
    
    def subscribe(
        self,
        topic: str,
        group_id: str,
        handler: Callable[[Dict[str, Any]], None],
        auto_offset_reset: str = 'latest'
    ):
        """
        Subscribe to topic and process messages
        
        Args:
            topic: Topic to subscribe to
            group_id: Consumer group ID
            handler: Function to call for each message
            auto_offset_reset: Where to start reading ('earliest' or 'latest')
        """
        try:
            consumer = KafkaConsumer(
                topic,
                bootstrap_servers=self.bootstrap_servers.split(","),
                client_id=self.client_id,
                group_id=group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8')),
                auto_offset_reset=auto_offset_reset,
                enable_auto_commit=True
            )
            
            self.consumers[topic] = consumer
            logger.info(f"Subscribed to {topic} (group={group_id})")
            
            # Process messages
            for message in consumer:
                try:
                    handler(message.value)
                except Exception as e:
                    logger.error(f"Error processing message from {topic}: {e}")
        
        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")
            raise
    
    def close(self):
        """Close all connections"""
        if self.producer:
            self.producer.close()
            logger.info("Producer closed")
        
        for topic, consumer in self.consumers.items():
            consumer.close()
            logger.info(f"Consumer closed: {topic}")


# Singleton instance
_event_bus: Optional[CerberusEventBus] = None


def get_event_bus(client_id: Optional[str] = None) -> CerberusEventBus:
    """Get singleton event bus instance"""
    global _event_bus
    if _event_bus is None:
        _event_bus = CerberusEventBus(client_id=client_id)
    return _event_bus
