"""
PostgreSQL client wrapper for Cerberus services
Provides connection pooling and helper methods
"""
import os
import psycopg2
from psycopg2 import pool
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager


class PostgresClient:
    """PostgreSQL client with connection pooling"""
    
    def __init__(self, url: Optional[str] = None, min_conn: int = 1, max_conn: int = 10):
        """
        Initialize PostgreSQL client with connection pool
        
        Args:
            url: PostgreSQL connection URL
            min_conn: Minimum connections in pool
            max_conn: Maximum connections in pool
        """
        self.url = url or os.getenv(
            "POSTGRES_URL",
            "postgresql://cerberus:cerberus_password@postgres:5432/cerberus"
        )
        
        try:
            self.pool = psycopg2.pool.SimpleConnectionPool(
                min_conn,
                max_conn,
                self.url
            )
            if self.pool:
                print(f"PostgreSQL connection pool created: {min_conn}-{max_conn} connections")
        except Exception as e:
            print(f"Failed to create PostgreSQL connection pool: {e}")
            self.pool = None
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for getting a connection from the pool
        
        Usage:
            with client.get_connection() as conn:
                cursor = conn.cursor()
                ...
        """
        conn = None
        try:
            if self.pool:
                conn = self.pool.getconn()
                yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn and self.pool:
                self.pool.putconn(conn)
    
    def execute(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch: bool = False,
        fetchone: bool = False
    ) -> Optional[List[Tuple]]:
        """
        Execute a query
        
        Args:
            query: SQL query
            params: Query parameters
            fetch: If True, fetch all results
            fetchone: If True, fetch one result
        
        Returns:
            Query results or None
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                if fetchone:
                    return cursor.fetchone()
                elif fetch:
                    return cursor.fetchall()
                else:
                    conn.commit()
                    return None
        except Exception as e:
            print(f"PostgreSQL execute error: {e}")
            return None
    
    def execute_many(self, query: str, params_list: List[Tuple]) -> bool:
        """
        Execute a query with multiple parameter sets
        
        Args:
            query: SQL query
            params_list: List of parameter tuples
        
        Returns:
            True if successful
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, params_list)
                conn.commit()
                return True
        except Exception as e:
            print(f"PostgreSQL executemany error: {e}")
            return False
    
    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[Tuple]:
        """Fetch all results from a query"""
        result = self.execute(query, params, fetch=True)
        return result if result else []
    
    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[Tuple]:
        """Fetch one result from a query"""
        return self.execute(query, params, fetchone=True)
    
    def fetch_dict(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """
        Fetch results as list of dictionaries
        
        Returns:
            List of row dictionaries with column names as keys
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                
                return [dict(zip(columns, row)) for row in rows]
        except Exception as e:
            print(f"PostgreSQL fetch_dict error: {e}")
            return []
    
    def insert(self, table: str, data: Dict[str, Any]) -> Optional[int]:
        """
        Insert a row and return the ID
        
        Args:
            table: Table name
            data: Dictionary of column: value
        
        Returns:
            Inserted row ID or None
        """
        columns = list(data.keys())
        values = list(data.values())
        placeholders = ', '.join(['%s'] * len(values))
        columns_str = ', '.join(columns)
        
        query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders}) RETURNING id"
        
        result = self.execute(query, tuple(values), fetchone=True)
        return result[0] if result else None
    
    def update(self, table: str, data: Dict[str, Any], where: str, where_params: Tuple) -> bool:
        """
        Update rows
        
        Args:
            table: Table name
            data: Dictionary of column: value to update
            where: WHERE clause (without WHERE keyword)
            where_params: Parameters for WHERE clause
        
        Returns:
            True if successful
        """
        set_clause = ', '.join([f"{col} = %s" for col in data.keys()])
        query = f"UPDATE {table} SET {set_clause} WHERE {where}"
        
        params = tuple(list(data.values()) + list(where_params))
        result = self.execute(query, params)
        return result is not None
    
    def delete(self, table: str, where: str, where_params: Tuple) -> bool:
        """
        Delete rows
        
        Args:
            table: Table name
            where: WHERE clause (without WHERE keyword)
            where_params: Parameters for WHERE clause
        
        Returns:
            True if successful
        """
        query = f"DELETE FROM {table} WHERE {where}"
        result = self.execute(query, where_params)
        return result is not None
    
    def table_exists(self, table: str) -> bool:
        """Check if a table exists"""
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = %s
            )
        """
        result = self.execute(query, (table,), fetchone=True)
        return result[0] if result else False
    
    def create_table(self, table: str, schema: str) -> bool:
        """
        Create a table
        
        Args:
            table: Table name
            schema: Table schema SQL
        
        Returns:
            True if successful
        """
        query = f"CREATE TABLE IF NOT EXISTS {table} ({schema})"
        result = self.execute(query)
        return result is not None
    
    def ping(self) -> bool:
        """Check if PostgreSQL is accessible"""
        try:
            result = self.execute("SELECT 1", fetchone=True)
            return result is not None
        except Exception:
            return False
    
    def close(self):
        """Close all connections in the pool"""
        if self.pool:
            self.pool.closeall()
            print("PostgreSQL connection pool closed")


# Global instance
_postgres_client: Optional[PostgresClient] = None


def get_postgres_client() -> PostgresClient:
    """Get or create PostgreSQL client singleton"""
    global _postgres_client
    if _postgres_client is None:
        _postgres_client = PostgresClient()
    return _postgres_client
