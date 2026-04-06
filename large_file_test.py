"""
Large test file with 1000+ lines to test Commit Composer performance
This file simulates a real-world scenario with multiple logical sections
"""

# Section 1: Database Models (Lines 1-200)
class User:
    """User model for authentication and profile management"""
    def __init__(self, user_id, username, email, password_hash):
        self.user_id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.created_at = None
        self.updated_at = None
        self.is_active = True
        self.is_admin = False
        self.profile_image = None
        self.bio = ""
        self.location = ""
        self.website = ""
        
    def validate_email(self):
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, self.email) is not None
    
    def update_password(self, new_password):
        """Update user password with hashing"""
        import hashlib
        self.password_hash = hashlib.sha256(new_password.encode()).hexdigest()
        self.updated_at = datetime.now()
    
    def get_full_profile(self):
        """Return complete user profile data"""
        return {
            'id': self.user_id,
            'username': self.username,
            'email': self.email,
            'bio': self.bio,
            'location': self.location,
            'website': self.website,
            'is_active': self.is_active,
            'created_at': self.created_at
        }

class Product:
    """Product model for e-commerce functionality"""
    def __init__(self, product_id, name, description, price):
        self.product_id = product_id
        self.name = name
        self.description = description
        self.price = price
        self.category = ""
        self.stock_quantity = 0
        self.sku = ""
        self.weight = 0.0
        self.dimensions = {}
        self.images = []
        self.is_available = True
        self.discount_percentage = 0
        
    def calculate_discounted_price(self):
        """Calculate price after discount"""
        if self.discount_percentage > 0:
            discount = self.price * (self.discount_percentage / 100)
            return self.price - discount
        return self.price
    
    def update_stock(self, quantity):
        """Update stock quantity"""
        self.stock_quantity += quantity
        if self.stock_quantity <= 0:
            self.is_available = False
    
    def add_image(self, image_url):
        """Add product image"""
        if len(self.images) < 10:
            self.images.append(image_url)
            return True
        return False

class Order:
    """Order model for purchase management"""
    def __init__(self, order_id, user_id, total_amount):
        self.order_id = order_id
        self.user_id = user_id
        self.total_amount = total_amount
        self.status = "pending"
        self.items = []
        self.shipping_address = {}
        self.billing_address = {}
        self.payment_method = ""
        self.tracking_number = ""
        self.created_at = None
        self.shipped_at = None
        self.delivered_at = None
        
    def add_item(self, product_id, quantity, price):
        """Add item to order"""
        item = {
            'product_id': product_id,
            'quantity': quantity,
            'price': price,
            'subtotal': quantity * price
        }
        self.items.append(item)
        self.recalculate_total()
    
    def recalculate_total(self):
        """Recalculate order total"""
        self.total_amount = sum(item['subtotal'] for item in self.items)
    
    def update_status(self, new_status):
        """Update order status"""
        valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
        if new_status in valid_statuses:
            self.status = new_status
            if new_status == "shipped":
                from datetime import datetime
                self.shipped_at = datetime.now()
            elif new_status == "delivered":
                from datetime import datetime
                self.delivered_at = datetime.now()

# Section 2: API Handlers (Lines 201-400)
class UserAPI:
    """API handlers for user operations"""
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_user(self, username, email, password):
        """Create new user account"""
        import hashlib
        from datetime import datetime
        
        # Validate input
        if not username or len(username) < 3:
            return {"error": "Username must be at least 3 characters"}
        if not email or '@' not in email:
            return {"error": "Invalid email address"}
        if not password or len(password) < 8:
            return {"error": "Password must be at least 8 characters"}
        
        # Check if user exists
        existing_user = self.db.query(f"SELECT * FROM users WHERE username='{username}'")
        if existing_user:
            return {"error": "Username already exists"}
        
        # Create user
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user_id = self.db.insert("users", {
            'username': username,
            'email': email,
            'password_hash': password_hash,
            'created_at': datetime.now()
        })
        
        return {"success": True, "user_id": user_id}
    
    def get_user(self, user_id):
        """Retrieve user by ID"""
        user = self.db.query(f"SELECT * FROM users WHERE user_id={user_id}")
        if not user:
            return {"error": "User not found"}
        return {"success": True, "user": user}
    
    def update_user(self, user_id, data):
        """Update user information"""
        allowed_fields = ['email', 'bio', 'location', 'website', 'profile_image']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return {"error": "No valid fields to update"}
        
        self.db.update("users", update_data, f"user_id={user_id}")
        return {"success": True}
    
    def delete_user(self, user_id):
        """Soft delete user account"""
        self.db.update("users", {'is_active': False}, f"user_id={user_id}")
        return {"success": True}

class ProductAPI:
    """API handlers for product operations"""
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_product(self, name, description, price, category):
        """Create new product"""
        if not name or len(name) < 3:
            return {"error": "Product name must be at least 3 characters"}
        if price <= 0:
            return {"error": "Price must be greater than 0"}
        
        product_id = self.db.insert("products", {
            'name': name,
            'description': description,
            'price': price,
            'category': category,
            'is_available': True
        })
        
        return {"success": True, "product_id": product_id}
    
    def get_product(self, product_id):
        """Retrieve product by ID"""
        product = self.db.query(f"SELECT * FROM products WHERE product_id={product_id}")
        if not product:
            return {"error": "Product not found"}
        return {"success": True, "product": product}
    
    def list_products(self, category=None, min_price=None, max_price=None):
        """List products with filters"""
        query = "SELECT * FROM products WHERE is_available=1"
        
        if category:
            query += f" AND category='{category}'"
        if min_price:
            query += f" AND price >= {min_price}"
        if max_price:
            query += f" AND price <= {max_price}"
        
        products = self.db.query(query)
        return {"success": True, "products": products, "count": len(products)}
    
    def update_product(self, product_id, data):
        """Update product information"""
        allowed_fields = ['name', 'description', 'price', 'category', 'stock_quantity', 'is_available']
        update_data = {k: v for k, v in data.items() if k in allowed_fields}
        
        if not update_data:
            return {"error": "No valid fields to update"}
        
        self.db.update("products", update_data, f"product_id={product_id}")
        return {"success": True}
    
    def delete_product(self, product_id):
        """Soft delete product"""
        self.db.update("products", {'is_available': False}, f"product_id={product_id}")
        return {"success": True}

class OrderAPI:
    """API handlers for order operations"""
    def __init__(self, db_connection):
        self.db = db_connection
        
    def create_order(self, user_id, items, shipping_address):
        """Create new order"""
        from datetime import datetime
        
        if not items or len(items) == 0:
            return {"error": "Order must contain at least one item"}
        
        # Calculate total
        total_amount = 0
        for item in items:
            product = self.db.query(f"SELECT * FROM products WHERE product_id={item['product_id']}")
            if not product or not product['is_available']:
                return {"error": f"Product {item['product_id']} not available"}
            total_amount += product['price'] * item['quantity']
        
        # Create order
        order_id = self.db.insert("orders", {
            'user_id': user_id,
            'total_amount': total_amount,
            'status': 'pending',
            'created_at': datetime.now()
        })
        
        # Add order items
        for item in items:
            self.db.insert("order_items", {
                'order_id': order_id,
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'price': item['price']
            })
        
        return {"success": True, "order_id": order_id, "total_amount": total_amount}
    
    def get_order(self, order_id):
        """Retrieve order by ID"""
        order = self.db.query(f"SELECT * FROM orders WHERE order_id={order_id}")
        if not order:
            return {"error": "Order not found"}
        
        items = self.db.query(f"SELECT * FROM order_items WHERE order_id={order_id}")
        order['items'] = items
        
        return {"success": True, "order": order}
    
    def update_order_status(self, order_id, status):
        """Update order status"""
        valid_statuses = ["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"]
        if status not in valid_statuses:
            return {"error": "Invalid status"}
        
        from datetime import datetime
        update_data = {'status': status}
        
        if status == "shipped":
            update_data['shipped_at'] = datetime.now()
        elif status == "delivered":
            update_data['delivered_at'] = datetime.now()
        
        self.db.update("orders", update_data, f"order_id={order_id}")
        return {"success": True}

# Section 3: Business Logic (Lines 401-600)
class ShoppingCart:
    """Shopping cart management"""
    def __init__(self, user_id):
        self.user_id = user_id
        self.items = []
        self.total = 0
        
    def add_item(self, product_id, quantity, price):
        """Add item to cart"""
        # Check if item already exists
        for item in self.items:
            if item['product_id'] == product_id:
                item['quantity'] += quantity
                item['subtotal'] = item['quantity'] * item['price']
                self.calculate_total()
                return True
        
        # Add new item
        self.items.append({
            'product_id': product_id,
            'quantity': quantity,
            'price': price,
            'subtotal': quantity * price
        })
        self.calculate_total()
        return True
    
    def remove_item(self, product_id):
        """Remove item from cart"""
        self.items = [item for item in self.items if item['product_id'] != product_id]
        self.calculate_total()
    
    def update_quantity(self, product_id, quantity):
        """Update item quantity"""
        for item in self.items:
            if item['product_id'] == product_id:
                if quantity <= 0:
                    self.remove_item(product_id)
                else:
                    item['quantity'] = quantity
                    item['subtotal'] = item['quantity'] * item['price']
                self.calculate_total()
                return True
        return False
    
    def calculate_total(self):
        """Calculate cart total"""
        self.total = sum(item['subtotal'] for item in self.items)
    
    def clear(self):
        """Clear all items from cart"""
        self.items = []
        self.total = 0
    
    def get_item_count(self):
        """Get total number of items"""
        return sum(item['quantity'] for item in self.items)

class PaymentProcessor:
    """Payment processing logic"""
    def __init__(self, gateway):
        self.gateway = gateway
        self.transactions = []
        
    def process_payment(self, order_id, amount, payment_method, card_data):
        """Process payment for order"""
        import random
        from datetime import datetime
        
        # Validate amount
        if amount <= 0:
            return {"error": "Invalid amount"}
        
        # Validate payment method
        valid_methods = ["credit_card", "debit_card", "paypal", "stripe"]
        if payment_method not in valid_methods:
            return {"error": "Invalid payment method"}
        
        # Process with gateway
        try:
            transaction_id = f"TXN-{random.randint(100000, 999999)}"
            
            # Simulate gateway processing
            gateway_response = self.gateway.charge(
                amount=amount,
                payment_method=payment_method,
                card_data=card_data
            )
            
            if gateway_response['status'] == 'success':
                transaction = {
                    'transaction_id': transaction_id,
                    'order_id': order_id,
                    'amount': amount,
                    'payment_method': payment_method,
                    'status': 'completed',
                    'timestamp': datetime.now()
                }
                self.transactions.append(transaction)
                return {"success": True, "transaction_id": transaction_id}
            else:
                return {"error": "Payment failed", "reason": gateway_response['error']}
                
        except Exception as e:
            return {"error": f"Payment processing error: {str(e)}"}
    
    def refund_payment(self, transaction_id, amount):
        """Process refund for transaction"""
        transaction = next((t for t in self.transactions if t['transaction_id'] == transaction_id), None)
        if not transaction:
            return {"error": "Transaction not found"}
        
        if amount > transaction['amount']:
            return {"error": "Refund amount exceeds transaction amount"}
        
        # Process refund with gateway
        try:
            refund_response = self.gateway.refund(
                transaction_id=transaction_id,
                amount=amount
            )
            
            if refund_response['status'] == 'success':
                transaction['refund_amount'] = amount
                transaction['refund_status'] = 'completed'
                return {"success": True, "refund_id": refund_response['refund_id']}
            else:
                return {"error": "Refund failed", "reason": refund_response['error']}
                
        except Exception as e:
            return {"error": f"Refund processing error: {str(e)}"}

class InventoryManager:
    """Inventory management logic"""
    def __init__(self, db_connection):
        self.db = db_connection
        
    def check_stock(self, product_id):
        """Check product stock level"""
        product = self.db.query(f"SELECT stock_quantity FROM products WHERE product_id={product_id}")
        if not product:
            return {"error": "Product not found"}
        return {"success": True, "stock": product['stock_quantity']}
    
    def update_stock(self, product_id, quantity_change):
        """Update product stock"""
        product = self.db.query(f"SELECT stock_quantity FROM products WHERE product_id={product_id}")
        if not product:
            return {"error": "Product not found"}
        
        new_stock = product['stock_quantity'] + quantity_change
        if new_stock < 0:
            return {"error": "Insufficient stock"}
        
        self.db.update("products", {'stock_quantity': new_stock}, f"product_id={product_id}")
        
        # Update availability
        if new_stock == 0:
            self.db.update("products", {'is_available': False}, f"product_id={product_id}")
        elif new_stock > 0 and not product['is_available']:
            self.db.update("products", {'is_available': True}, f"product_id={product_id}")
        
        return {"success": True, "new_stock": new_stock}
    
    def reserve_stock(self, product_id, quantity):
        """Reserve stock for order"""
        return self.update_stock(product_id, -quantity)
    
    def release_stock(self, product_id, quantity):
        """Release reserved stock"""
        return self.update_stock(product_id, quantity)
    
    def get_low_stock_products(self, threshold=10):
        """Get products with low stock"""
        products = self.db.query(f"SELECT * FROM products WHERE stock_quantity < {threshold} AND is_available=1")
        return {"success": True, "products": products, "count": len(products)}

# Section 4: Utilities (Lines 601-800)
class EmailService:
    """Email notification service"""
    def __init__(self, smtp_config):
        self.smtp_config = smtp_config
        self.sent_emails = []
        
    def send_email(self, to_address, subject, body, html=False):
        """Send email notification"""
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from datetime import datetime
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_config['from_address']
            msg['To'] = to_address
            
            if html:
                part = MIMEText(body, 'html')
            else:
                part = MIMEText(body, 'plain')
            
            msg.attach(part)
            
            # Send email
            with smtplib.SMTP(self.smtp_config['host'], self.smtp_config['port']) as server:
                server.starttls()
                server.login(self.smtp_config['username'], self.smtp_config['password'])
                server.send_message(msg)
            
            self.sent_emails.append({
                'to': to_address,
                'subject': subject,
                'sent_at': datetime.now(),
                'status': 'sent'
            })
            
            return {"success": True}
            
        except Exception as e:
            return {"error": f"Email sending failed: {str(e)}"}
    
    def send_welcome_email(self, user_email, username):
        """Send welcome email to new user"""
        subject = f"Welcome to Our Platform, {username}!"
        body = f"""
        Hello {username},
        
        Welcome to our platform! We're excited to have you on board.
        
        You can now:
        - Browse our product catalog
        - Add items to your cart
        - Place orders
        - Track your shipments
        
        If you have any questions, feel free to contact our support team.
        
        Best regards,
        The Team
        """
        return self.send_email(user_email, subject, body)
    
    def send_order_confirmation(self, user_email, order_id, total_amount):
        """Send order confirmation email"""
        subject = f"Order Confirmation - #{order_id}"
        body = f"""
        Thank you for your order!
        
        Order ID: {order_id}
        Total Amount: ${total_amount:.2f}
        
        We'll send you another email when your order ships.
        
        You can track your order status in your account dashboard.
        
        Best regards,
        The Team
        """
        return self.send_email(user_email, subject, body)
    
    def send_shipping_notification(self, user_email, order_id, tracking_number):
        """Send shipping notification email"""
        subject = f"Your Order Has Shipped - #{order_id}"
        body = f"""
        Great news! Your order has shipped.
        
        Order ID: {order_id}
        Tracking Number: {tracking_number}
        
        You can track your shipment using the tracking number above.
        
        Estimated delivery: 3-5 business days.
        
        Best regards,
        The Team
        """
        return self.send_email(user_email, subject, body)

class Logger:
    """Application logging utility"""
    def __init__(self, log_file):
        self.log_file = log_file
        self.log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
    def log(self, level, message, context=None):
        """Write log entry"""
        from datetime import datetime
        
        if level not in self.log_levels:
            level = 'INFO'
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level}] {message}"
        
        if context:
            log_entry += f" | Context: {context}"
        
        with open(self.log_file, 'a') as f:
            f.write(log_entry + '\n')
    
    def debug(self, message, context=None):
        """Log debug message"""
        self.log('DEBUG', message, context)
    
    def info(self, message, context=None):
        """Log info message"""
        self.log('INFO', message, context)
    
    def warning(self, message, context=None):
        """Log warning message"""
        self.log('WARNING', message, context)
    
    def error(self, message, context=None):
        """Log error message"""
        self.log('ERROR', message, context)
    
    def critical(self, message, context=None):
        """Log critical message"""
        self.log('CRITICAL', message, context)

class CacheManager:
    """Caching utility"""
    def __init__(self, ttl_seconds=3600):
        self.cache = {}
        self.ttl_seconds = ttl_seconds
        
    def get(self, key):
        """Get value from cache"""
        from datetime import datetime
        
        if key not in self.cache:
            return None
        
        entry = self.cache[key]
        if (datetime.now() - entry['timestamp']).seconds > self.ttl_seconds:
            del self.cache[key]
            return None
        
        return entry['value']
    
    def set(self, key, value):
        """Set value in cache"""
        from datetime import datetime
        
        self.cache[key] = {
            'value': value,
            'timestamp': datetime.now()
        }
    
    def delete(self, key):
        """Delete value from cache"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """Clear all cache"""
        self.cache = {}
    
    def cleanup(self):
        """Remove expired entries"""
        from datetime import datetime
        
        expired_keys = []
        for key, entry in self.cache.items():
            if (datetime.now() - entry['timestamp']).seconds > self.ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache[key]

# Section 5: Validators (Lines 801-1000)
class InputValidator:
    """Input validation utilities"""
    @staticmethod
    def validate_email(email):
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_password(password):
        """Validate password strength"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password)
        
        if not (has_upper and has_lower and has_digit):
            return False, "Password must contain uppercase, lowercase, and numbers"
        
        return True, "Valid password"
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format"""
        import re
        # Support multiple formats: (123) 456-7890, 123-456-7890, 1234567890
        patterns = [
            r'^\(\d{3}\)\s*\d{3}-\d{4}$',
            r'^\d{3}-\d{3}-\d{4}$',
            r'^\d{10}$'
        ]
        return any(re.match(pattern, phone) for pattern in patterns)
    
    @staticmethod
    def validate_credit_card(card_number):
        """Validate credit card number using Luhn algorithm"""
        # Remove spaces and dashes
        card_number = card_number.replace(' ', '').replace('-', '')
        
        if not card_number.isdigit():
            return False
        
        if len(card_number) < 13 or len(card_number) > 19:
            return False
        
        # Luhn algorithm
        total = 0
        reverse_digits = card_number[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        
        return total % 10 == 0
    
    @staticmethod
    def validate_zip_code(zip_code, country='US'):
        """Validate zip/postal code"""
        import re
        
        patterns = {
            'US': r'^\d{5}(-\d{4})?$',
            'CA': r'^[A-Z]\d[A-Z]\s*\d[A-Z]\d$',
            'UK': r'^[A-Z]{1,2}\d{1,2}\s*\d[A-Z]{2}$'
        }
        
        pattern = patterns.get(country)
        if not pattern:
            return False
        
        return re.match(pattern, zip_code.upper()) is not None
    
    @staticmethod
    def sanitize_input(text):
        """Sanitize user input to prevent XSS"""
        import html
        
        # HTML escape
        text = html.escape(text)
        
        # Remove potentially dangerous tags
        dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
        for pattern in dangerous_patterns:
            text = text.replace(pattern, '')
        
        return text
    
    @staticmethod
    def validate_url(url):
        """Validate URL format"""
        import re
        pattern = r'^https?://[a-zA-Z0-9-._~:/?#[\]@!$&\'()*+,;=]+$'
        return re.match(pattern, url) is not None

class DataFormatter:
    """Data formatting utilities"""
    @staticmethod
    def format_currency(amount, currency='USD'):
        """Format amount as currency"""
        symbols = {
            'USD': '$',
            'EUR': '€',
            'GBP': '£',
            'JPY': '¥'
        }
        symbol = symbols.get(currency, '$')
        return f"{symbol}{amount:,.2f}"
    
    @staticmethod
    def format_date(date_obj, format_string='%Y-%m-%d'):
        """Format date object"""
        return date_obj.strftime(format_string)
    
    @staticmethod
    def format_phone(phone):
        """Format phone number"""
        # Remove all non-digits
        digits = ''.join(filter(str.isdigit, phone))
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return phone
    
    @staticmethod
    def format_file_size(bytes_size):
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"
    
    @staticmethod
    def truncate_text(text, max_length, suffix='...'):
        """Truncate text to maximum length"""
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

class SecurityHelper:
    """Security utilities"""
    @staticmethod
    def hash_password(password, salt=None):
        """Hash password with salt"""
        import hashlib
        import os
        
        if salt is None:
            salt = os.urandom(32)
        
        key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        return salt + key
    
    @staticmethod
    def verify_password(password, hashed):
        """Verify password against hash"""
        import hashlib
        
        salt = hashed[:32]
        key = hashed[32:]
        
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt,
            100000
        )
        
        return key == new_key
    
    @staticmethod
    def generate_token(length=32):
        """Generate random token"""
        import secrets
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def encrypt_data(data, key):
        """Encrypt sensitive data"""
        from cryptography.fernet import Fernet
        
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data.encode())
        return encrypted
    
    @staticmethod
    def decrypt_data(encrypted_data, key):
        """Decrypt sensitive data"""
        from cryptography.fernet import Fernet
        
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_data)
        return decrypted.decode()

# Section 6: Additional Features (Lines 1001-1200)
class SearchEngine:
    """Product search functionality"""
    def __init__(self, db_connection):
        self.db = db_connection
        
    def search_products(self, query, filters=None):
        """Search products by query"""
        # Basic text search
        sql = f"SELECT * FROM products WHERE name LIKE '%{query}%' OR description LIKE '%{query}%'"
        
        if filters:
            if 'category' in filters:
                sql += f" AND category='{filters['category']}'"
            if 'min_price' in filters:
                sql += f" AND price >= {filters['min_price']}"
            if 'max_price' in filters:
                sql += f" AND price <= {filters['max_price']}"
            if 'in_stock' in filters and filters['in_stock']:
                sql += " AND stock_quantity > 0"
        
        results = self.db.query(sql)
        return {
            'success': True,
            'results': results,
            'count': len(results),
            'query': query
        }
    
    def search_by_category(self, category):
        """Search products by category"""
        products = self.db.query(f"SELECT * FROM products WHERE category='{category}' AND is_available=1")
        return {'success': True, 'products': products, 'count': len(products)}
    
    def get_popular_products(self, limit=10):
        """Get popular products based on sales"""
        sql = f"""
            SELECT p.*, COUNT(oi.product_id) as sales_count
            FROM products p
            LEFT JOIN order_items oi ON p.product_id = oi.product_id
            WHERE p.is_available = 1
            GROUP BY p.product_id
            ORDER BY sales_count DESC
            LIMIT {limit}
        """
        products = self.db.query(sql)
        return {'success': True, 'products': products}
    
    def get_related_products(self, product_id, limit=5):
        """Get related products"""
        product = self.db.query(f"SELECT category FROM products WHERE product_id={product_id}")
        if not product:
            return {'error': 'Product not found'}
        
        sql = f"""
            SELECT * FROM products
            WHERE category='{product['category']}'
            AND product_id != {product_id}
            AND is_available = 1
            LIMIT {limit}
        """
        products = self.db.query(sql)
        return {'success': True, 'products': products}

class RecommendationEngine:
    """Product recommendation system"""
    def __init__(self, db_connection):
        self.db = db_connection
        
    def get_recommendations_for_user(self, user_id, limit=10):
        """Get personalized product recommendations"""
        # Get user's purchase history
        user_orders = self.db.query(f"""
            SELECT DISTINCT oi.product_id, p.category
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            JOIN products p ON oi.product_id = p.product_id
            WHERE o.user_id = {user_id}
        """)
        
        if not user_orders:
            # No history, return popular products
            return self.get_popular_products(limit)
        
        # Get categories user has purchased from
        categories = list(set(order['category'] for order in user_orders))
        
        # Get products from those categories
        category_list = "','".join(categories)
        sql = f"""
            SELECT * FROM products
            WHERE category IN ('{category_list}')
            AND is_available = 1
            ORDER BY RAND()
            LIMIT {limit}
        """
        products = self.db.query(sql)
        return {'success': True, 'products': products}
    
    def get_frequently_bought_together(self, product_id, limit=5):
        """Get products frequently bought together"""
        sql = f"""
            SELECT p.*, COUNT(*) as frequency
            FROM order_items oi1
            JOIN order_items oi2 ON oi1.order_id = oi2.order_id
            JOIN products p ON oi2.product_id = p.product_id
            WHERE oi1.product_id = {product_id}
            AND oi2.product_id != {product_id}
            AND p.is_available = 1
            GROUP BY oi2.product_id
            ORDER BY frequency DESC
            LIMIT {limit}
        """
        products = self.db.query(sql)
        return {'success': True, 'products': products}
    
    def get_popular_products(self, limit=10):
        """Get popular products"""
        sql = f"""
            SELECT p.*, COUNT(oi.product_id) as sales
            FROM products p
            LEFT JOIN order_items oi ON p.product_id = oi.product_id
            WHERE p.is_available = 1
            GROUP BY p.product_id
            ORDER BY sales DESC
            LIMIT {limit}
        """
        products = self.db.query(sql)
        return {'success': True, 'products': products}

class ReviewSystem:
    """Product review management"""
    def __init__(self, db_connection):
        self.db = db_connection
        
    def add_review(self, user_id, product_id, rating, comment):
        """Add product review"""
        from datetime import datetime
        
        # Validate rating
        if rating < 1 or rating > 5:
            return {'error': 'Rating must be between 1 and 5'}
        
        # Check if user purchased product
        purchase = self.db.query(f"""
            SELECT o.order_id
            FROM orders o
            JOIN order_items oi ON o.order_id = oi.order_id
            WHERE o.user_id = {user_id}
            AND oi.product_id = {product_id}
            AND o.status = 'delivered'
        """)
        
        if not purchase:
            return {'error': 'You can only review products you have purchased'}
        
        # Add review
        review_id = self.db.insert('reviews', {
            'user_id': user_id,
            'product_id': product_id,
            'rating': rating,
            'comment': comment,
            'created_at': datetime.now()
        })
        
        # Update product average rating
        self.update_product_rating(product_id)
        
        return {'success': True, 'review_id': review_id}
    
    def get_product_reviews(self, product_id, limit=20, offset=0):
        """Get reviews for product"""
        sql = f"""
            SELECT r.*, u.username
            FROM reviews r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.product_id = {product_id}
            ORDER BY r.created_at DESC
            LIMIT {limit} OFFSET {offset}
        """
        reviews = self.db.query(sql)
        
        # Get total count
        count_sql = f"SELECT COUNT(*) as total FROM reviews WHERE product_id = {product_id}"
        count = self.db.query(count_sql)['total']
        
        return {
            'success': True,
            'reviews': reviews,
            'total': count,
            'page': offset // limit + 1
        }
    
    def update_product_rating(self, product_id):
        """Update product average rating"""
        sql = f"""
            SELECT AVG(rating) as avg_rating, COUNT(*) as review_count
            FROM reviews
            WHERE product_id = {product_id}
        """
        stats = self.db.query(sql)
        
        self.db.update('products', {
            'average_rating': stats['avg_rating'],
            'review_count': stats['review_count']
        }, f"product_id = {product_id}")
        
        return {'success': True}
    
    def delete_review(self, review_id, user_id):
        """Delete user's review"""
        review = self.db.query(f"SELECT * FROM reviews WHERE review_id = {review_id}")
        
        if not review:
            return {'error': 'Review not found'}
        
        if review['user_id'] != user_id:
            return {'error': 'Unauthorized'}
        
        product_id = review['product_id']
        self.db.delete('reviews', f"review_id = {review_id}")
        self.update_product_rating(product_id)
        
        return {'success': True}

class WishlistManager:
    """User wishlist management"""
    def __init__(self, db_connection):
        self.db = db_connection
        
    def add_to_wishlist(self, user_id, product_id):
        """Add product to wishlist"""
        from datetime import datetime
        
        # Check if already in wishlist
        existing = self.db.query(f"""
            SELECT * FROM wishlist
            WHERE user_id = {user_id} AND product_id = {product_id}
        """)
        
        if existing:
            return {'error': 'Product already in wishlist'}
        
        # Add to wishlist
        wishlist_id = self.db.insert('wishlist', {
            'user_id': user_id,
            'product_id': product_id,
            'added_at': datetime.now()
        })
        
        return {'success': True, 'wishlist_id': wishlist_id}
    
    def remove_from_wishlist(self, user_id, product_id):
        """Remove product from wishlist"""
        self.db.delete('wishlist', f"user_id = {user_id} AND product_id = {product_id}")
        return {'success': True}
    
    def get_wishlist(self, user_id):
        """Get user's wishlist"""
        sql = f"""
            SELECT p.*, w.added_at
            FROM wishlist w
            JOIN products p ON w.product_id = p.product_id
            WHERE w.user_id = {user_id}
            ORDER BY w.added_at DESC
        """
        products = self.db.query(sql)
        return {'success': True, 'products': products, 'count': len(products)}
    
    def move_to_cart(self, user_id, product_id):
        """Move wishlist item to cart"""
        # Remove from wishlist
        self.remove_from_wishlist(user_id, product_id)
        
        # Add to cart logic would go here
        return {'success': True}

# End of file - Total lines: 1200+
