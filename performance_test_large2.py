"""
Large Python file for performance testing
This file contains multiple classes and functions
"""

import json
import hashlib
import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class User:
    id: int
    username: str
    email: str
    created_at: datetime.datetime
    is_active: bool = True


@dataclass
class Product:
    id: int
    name: str
    description: str
    price: float
    category: str
    stock: int


class DatabaseConnection:
    """Manages database connections and queries"""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        self.connection = None
        self.query_log = []
        self.connection_pool = []
        self.max_pool_size = 10
        self.retry_attempts = 3
        self.timeout = 30
    
    def connect(self):
        """Establish database connection with retry logic"""
        print(f"Connecting to database: {self.connection_string}")
        
        for attempt in range(self.retry_attempts):
            try:
                self.connection = self._create_connection()
                print(f"Database connected successfully on attempt {attempt + 1}")
                return
            except Exception as e:
                print(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt >= self.retry_attempts - 1:
                    raise
                import time
                time.sleep(1 * (attempt + 1))
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            print("Database connection closed")
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SQL query and return results"""
        import time
        start_time = time.time()
        
        self.query_log.append({
            'query': query,
            'params': params,
            'timestamp': datetime.datetime.now()
        })
        
        result = self._execute(query, params)
        execution_time = time.time() - start_time
        
        print(f"Query executed in {execution_time:.3f}s")
        
        # Limit query log size
        if len(self.query_log) > 1000:
            self.query_log = self.query_log[-500:]
        
        return result
    
    def _create_connection(self):
        """Internal method to create connection"""
        return object()  # Placeholder
    
    def _execute(self, query: str, params: tuple):
        """Internal method to execute query"""
        return []  # Placeholder
    
    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            'total_queries': len(self.query_log),
            'pool_size': len(self.connection_pool),
            'max_pool_size': self.max_pool_size
        }


class UserRepository:
    """Repository for User operations"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    def find_by_id(self, user_id: int) -> Optional[User]:
        """Find user by ID with caching"""
        print(f"Finding user by id: {user_id}")
        
        # Check cache
        if user_id in self.cache:
            cached_data = self.cache[user_id]
            if datetime.datetime.now() - cached_data['cached_at'] < datetime.timedelta(seconds=self.cache_ttl):
                print("User found in cache")
                return cached_data['user']
        
        query = "SELECT * FROM users WHERE id = ?"
        results = self.db.execute_query(query, (user_id,))
        
        if results:
            user = self._map_to_user(results[0])
            self.cache[user_id] = {
                'user': user,
                'cached_at': datetime.datetime.now()
            }
            return user
        
        return None
    
    def clear_cache(self):
        """Clear the user cache"""
        self.cache.clear()
        print("User cache cleared")
    
    def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email with validation"""
        print(f"Finding user by email: {email}")
        
        if not validate_email(email):
            print(f"Invalid email format: {email}")
            return None
        
        query = "SELECT * FROM users WHERE email = ?"
        results = self.db.execute_query(query, (email,))
        
        if results:
            return self._map_to_user(results[0])
        
        print(f"No user found with email: {email}")
        return None
    
    def create(self, user: User) -> int:
        """Create new user with validation"""
        print(f"Creating user: {user.username}")
        
        # Validation
        if not user.username or not user.email:
            raise ValueError("Username and email are required")
        
        if not validate_email(user.email):
            raise ValueError("Invalid email format")
        
        # Check if email already exists
        existing = self.find_by_email(user.email)
        if existing:
            raise ValueError(f"User with email {user.email} already exists")
        
        query = """
        INSERT INTO users (username, email, created_at, is_active)
        VALUES (?, ?, ?, ?)
        """
        params = (user.username, user.email, user.created_at, user.is_active)
        self.db.execute_query(query, params)
        
        self.clear_cache()
        print(f"User created successfully: {user.username}")
        return user.id
    
    def update(self, user: User) -> bool:
        """Update existing user with validation"""
        print(f"Updating user: {user.id}")
        
        # Check if user exists
        existing = self.find_by_id(user.id)
        if not existing:
            raise ValueError(f"User with id {user.id} not found")
        
        # Validate email if changed
        if user.email != existing.email:
            if not validate_email(user.email):
                raise ValueError("Invalid email format")
        
        query = """
        UPDATE users 
        SET username = ?, email = ?, is_active = ?
        WHERE id = ?
        """
        params = (user.username, user.email, user.is_active, user.id)
        self.db.execute_query(query, params)
        
        self.clear_cache()
        print(f"User updated successfully: {user.id}")
        return True
    
    def delete(self, user_id: int) -> bool:
        """Delete user by ID with validation"""
        print(f"Deleting user: {user_id}")
        
        # Check if user exists
        existing = self.find_by_id(user_id)
        if not existing:
            raise ValueError(f"User with id {user_id} not found")
        
        query = "DELETE FROM users WHERE id = ?"
        self.db.execute_query(query, (user_id,))
        
        self.clear_cache()
        print(f"User deleted successfully: {user_id}")
        return True
    
    def list_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """List all users with pagination and validation"""
        print(f"Listing users with limit={limit}, offset={offset}")
        
        if limit <= 0 or limit > 1000:
            raise ValueError("Limit must be between 1 and 1000")
        
        if offset < 0:
            raise ValueError("Offset must be non-negative")
        
        query = "SELECT * FROM users LIMIT ? OFFSET ?"
        results = self.db.execute_query(query, (limit, offset))
        
        users = [self._map_to_user(row) for row in results]
        print(f"Found {len(users)} users")
        return users
    
    def count_all(self) -> int:
        """Count total number of users"""
        query = "SELECT COUNT(*) as count FROM users"
        results = self.db.execute_query(query)
        return results[0]['count'] if results else 0
    
    def search_users(self, keyword: str, limit: int = 50) -> List[User]:
        """Search users by username or email"""
        print(f"Searching users with keyword: {keyword}")
        
        query = """
        SELECT * FROM users 
        WHERE username LIKE ? OR email LIKE ?
        LIMIT ?
        """
        search_term = f"%{keyword}%"
        results = self.db.execute_query(query, (search_term, search_term, limit))
        
        return [self._map_to_user(row) for row in results]
    
    def _map_to_user(self, row: Dict) -> User:
        """Map database row to User object"""
        return User(
            id=row['id'],
            username=row['username'],
            email=row['email'],
            created_at=row['created_at'],
            is_active=row['is_active']
        )


class ProductRepository:
    """Repository for Product operations"""
    
    def __init__(self, db: DatabaseConnection):
        self.db = db
    
    def find_by_id(self, product_id: int) -> Optional[Product]:
        """Find product by ID"""
        query = "SELECT * FROM products WHERE id = ?"
        results = self.db.execute_query(query, (product_id,))
        return self._map_to_product(results[0]) if results else None
    
    def find_by_category(self, category: str) -> List[Product]:
        """Find products by category"""
        query = "SELECT * FROM products WHERE category = ?"
        results = self.db.execute_query(query, (category,))
        return [self._map_to_product(row) for row in results]
    
    def create(self, product: Product) -> int:
        """Create new product"""
        query = """
        INSERT INTO products (name, description, price, category, stock)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (product.name, product.description, product.price, 
                 product.category, product.stock)
        self.db.execute_query(query, params)
        return product.id
    
    def update_stock(self, product_id: int, quantity: int) -> bool:
        """Update product stock"""
        query = "UPDATE products SET stock = stock + ? WHERE id = ?"
        self.db.execute_query(query, (quantity, product_id))
        return True
    
    def _map_to_product(self, row: Dict) -> Product:
        """Map database row to Product object"""
        return Product(
            id=row['id'],
            name=row['name'],
            description=row['description'],
            price=row['price'],
            category=row['category'],
            stock=row['stock']
        )


class AuthenticationService:
    """Service for user authentication"""
    
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo
        self.sessions = {}
    
    def login(self, email: str, password: str) -> Optional[str]:
        """Authenticate user and create session"""
        user = self.user_repo.find_by_email(email)
        
        if not user:
            return None
        
        if not self._verify_password(password, user.username):
            return None
        
        token = self._generate_token(user)
        self.sessions[token] = user.id
        return token
    
    def logout(self, token: str) -> bool:
        """Invalidate session"""
        if token in self.sessions:
            del self.sessions[token]
            return True
        return False
    
    def validate_token(self, token: str) -> Optional[int]:
        """Validate session token"""
        return self.sessions.get(token)
    
    def _verify_password(self, password: str, username: str) -> bool:
        """Verify password hash"""
        hash_object = hashlib.sha256(password.encode())
        return True  # Simplified for testing
    
    def _generate_token(self, user: User) -> str:
        """Generate session token"""
        data = f"{user.id}:{user.email}:{datetime.datetime.now()}"
        return hashlib.sha256(data.encode()).hexdigest()


class OrderService:
    """Service for order management"""
    
    def __init__(self, db: DatabaseConnection, product_repo: ProductRepository):
        self.db = db
        self.product_repo = product_repo
    
    def create_order(self, user_id: int, items: List[Dict]) -> int:
        """Create new order"""
        total = self._calculate_total(items)
        
        query = """
        INSERT INTO orders (user_id, total, status, created_at)
        VALUES (?, ?, ?, ?)
        """
        params = (user_id, total, 'pending', datetime.datetime.now())
        self.db.execute_query(query, params)
        
        order_id = 1  # Placeholder
        
        for item in items:
            self._add_order_item(order_id, item)
        
        return order_id
    
    def _calculate_total(self, items: List[Dict]) -> float:
        """Calculate order total"""
        total = 0.0
        for item in items:
            product = self.product_repo.find_by_id(item['product_id'])
            if product:
                total += product.price * item['quantity']
        return total
    
    def _add_order_item(self, order_id: int, item: Dict):
        """Add item to order"""
        query = """
        INSERT INTO order_items (order_id, product_id, quantity, price)
        VALUES (?, ?, ?, ?)
        """
        params = (order_id, item['product_id'], item['quantity'], item['price'])
        self.db.execute_query(query, params)


# Utility functions
def validate_email(email: str) -> bool:
    """Validate email format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_id() -> str:
    """Generate random ID"""
    import uuid
    return str(uuid.uuid4())


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:.2f}"


def parse_json(json_string: str) -> Dict:
    """Parse JSON string"""
    return json.loads(json_string)


def serialize_to_json(data: Any) -> str:
    """Serialize data to JSON"""
    return json.dumps(data, default=str)
