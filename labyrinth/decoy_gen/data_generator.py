"""
Synthetic Data Generator for Labyrinth
Creates realistic fake data for the honeypot
"""
from faker import Faker
from typing import List, Dict
import random
import string
from datetime import datetime, timedelta

fake = Faker()


class DecoyDataGenerator:
    """Generate synthetic data for honeypot"""
    
    def __init__(self, seed: int = 42):
        Faker.seed(seed)
        random.seed(seed)
    
    def generate_users(self, count: int = 100) -> List[Dict]:
        """Generate fake user records"""
        users = []
        
        for i in range(count):
            user = {
                "id": f"USR-{10000 + i}",
                "email": fake.email(),
                "name": fake.name(),
                "username": fake.user_name(),
                "role": random.choice(["user", "admin", "developer", "analyst"]),
                "department": random.choice(["Engineering", "Sales", "Marketing", "Finance", "HR"]),
                "created_at": fake.date_time_between(start_date="-2y", end_date="now").isoformat(),
                "last_login": fake.date_time_between(start_date="-30d", end_date="now").isoformat(),
                "api_key": self._generate_api_key(),
                "phone": fake.phone_number(),
                "address": fake.address().replace('\n', ', '),
                # Obviously fake SSN
                "ssn": f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}",
                "salary": random.randint(50000, 200000),
                "is_active": random.choice([True, True, True, False]),  # 75% active
            }
            users.append(user)
        
        return users
    
    def generate_documents(self, count: int = 50) -> List[Dict]:
        """Generate fake document records"""
        documents = []
        
        for i in range(count):
            doc = {
                "id": f"DOC-{20000 + i}",
                "title": fake.catch_phrase(),
                "filename": f"{fake.slug()}.{random.choice(['pdf', 'docx', 'xlsx', 'txt'])}",
                "content_preview": fake.text(max_nb_chars=200),
                "owner": f"USR-{random.randint(10000, 10099)}",
                "created_at": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
                "modified_at": fake.date_time_between(start_date="-60d", end_date="now").isoformat(),
                "size_bytes": random.randint(1024, 10485760),  # 1KB to 10MB
                "classification": random.choice(["public", "internal", "confidential", "restricted"]),
                "tags": [fake.word() for _ in range(random.randint(1, 5))],
                "download_url": f"/api/v1/documents/{20000 + i}/download",
            }
            documents.append(doc)
        
        return documents
    
    def generate_api_keys(self, count: int = 20) -> List[Dict]:
        """Generate fake API keys"""
        keys = []
        
        for i in range(count):
            key = {
                "id": f"KEY-{30000 + i}",
                "key": self._generate_api_key(),
                "name": f"{fake.word()}-{fake.word()}-key",
                "owner": f"USR-{random.randint(10000, 10099)}",
                "created_at": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
                "last_used": fake.date_time_between(start_date="-7d", end_date="now").isoformat(),
                "permissions": random.sample(["read", "write", "delete", "admin"], k=random.randint(1, 3)),
                "rate_limit": random.choice([100, 1000, 10000, -1]),  # -1 = unlimited
                "is_active": random.choice([True, True, True, False]),
            }
            keys.append(key)
        
        return keys
    
    def generate_transactions(self, count: int = 200) -> List[Dict]:
        """Generate fake transaction records"""
        transactions = []
        
        for i in range(count):
            txn = {
                "id": f"TXN-{40000 + i}",
                "user_id": f"USR-{random.randint(10000, 10099)}",
                "amount": round(random.uniform(10.0, 5000.0), 2),
                "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
                "status": random.choice(["completed", "pending", "failed"]),
                "timestamp": fake.date_time_between(start_date="-90d", end_date="now").isoformat(),
                "description": fake.sentence(nb_words=6),
                "payment_method": random.choice(["credit_card", "debit_card", "paypal", "bank_transfer"]),
                # Fake credit card (not valid)
                "card_last4": str(random.randint(1000, 9999)),
            }
            transactions.append(txn)
        
        return transactions
    
    def generate_database_config(self) -> Dict:
        """Generate fake database configuration (looks real but isn't)"""
        return {
            "host": "db.internal.acmecorp.com",
            "port": 5432,
            "database": "production_db",
            "username": "app_user",
            # Obviously fake password
            "password": "P@ssw0rd123!FAKE",
            "ssl_mode": "require",
            "pool_size": 20,
            "max_overflow": 10,
            "connection_string": "postgresql://app_user:P@ssw0rd123!FAKE@db.internal.acmecorp.com:5432/production_db"
        }
    
    def generate_aws_credentials(self) -> Dict:
        """Generate fake AWS credentials"""
        return {
            "access_key_id": f"AKIA{self._random_string(16, uppercase=True)}",
            "secret_access_key": self._random_string(40),
            "region": random.choice(["us-east-1", "us-west-2", "eu-west-1"]),
            "bucket": f"{fake.slug()}-production-data",
            "note": "FAKE CREDENTIALS - Not valid"
        }
    
    def generate_admin_credentials(self) -> List[Dict]:
        """Generate fake admin credentials"""
        return [
            {
                "username": "admin",
                "password": "admin123",  # Deliberately weak
                "role": "superadmin",
                "note": "Default admin account"
            },
            {
                "username": "root",
                "password": "toor",
                "role": "root",
                "note": "Root access"
            },
            {
                "username": "service_account",
                "password": "S3rv1c3P@ss",
                "role": "service",
                "note": "Service account for automation"
            }
        ]
    
    def _generate_api_key(self, prefix: str = "ak_live_") -> str:
        """Generate realistic-looking API key"""
        return prefix + self._random_string(32)
    
    def _random_string(self, length: int, uppercase: bool = False) -> str:
        """Generate random alphanumeric string"""
        chars = string.ascii_uppercase + string.digits if uppercase else string.ascii_lowercase + string.digits
        return ''.join(random.choices(chars, k=length))


# Singleton instance
_generator = None

def get_generator() -> DecoyDataGenerator:
    """Get singleton data generator"""
    global _generator
    if _generator is None:
        _generator = DecoyDataGenerator()
    return _generator
