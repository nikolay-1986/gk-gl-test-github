// Large JavaScript file for performance testing
// This file contains multiple functions and code blocks

class DatabaseManager {
    constructor(config) {
        this.config = config;
        this.connection = null;
        this.queryCache = new Map();
        this.connectionPool = [];
        this.maxConnections = config.maxConnections || 10;
        this.retryAttempts = config.retryAttempts || 3;
    }

    async connect() {
        console.log('Connecting to database with retry logic...');
        let attempts = 0;
        while (attempts < this.retryAttempts) {
            try {
                this.connection = await this.establishConnection();
                console.log('Connected successfully on attempt:', attempts + 1);
                break;
            } catch (error) {
                attempts++;
                console.error(`Connection attempt ${attempts} failed:`, error.message);
                if (attempts >= this.retryAttempts) throw error;
                await this.sleep(1000 * attempts);
            }
        }
    }

    async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    async query(sql, params) {
        const cacheKey = this.generateCacheKey(sql, params);
        if (this.queryCache.has(cacheKey)) {
            console.log('Cache hit for query:', sql);
            return this.queryCache.get(cacheKey);
        }
        
        console.log('Executing query:', sql);
        const startTime = Date.now();
        const result = await this.executeQuery(sql, params);
        const executionTime = Date.now() - startTime;
        
        console.log(`Query executed in ${executionTime}ms`);
        
        if (this.queryCache.size > 1000) {
            this.clearOldestCacheEntries();
        }
        
        this.queryCache.set(cacheKey, result);
        return result;
    }

    clearOldestCacheEntries() {
        const entries = Array.from(this.queryCache.entries());
        const toRemove = entries.slice(0, 100);
        toRemove.forEach(([key]) => this.queryCache.delete(key));
    }

    generateCacheKey(sql, params) {
        return `${sql}:${JSON.stringify(params)}`;
    }
}

class UserService {
    constructor(dbManager) {
        this.db = dbManager;
        this.users = [];
        this.userCache = new Map();
        this.logger = console;
    }

    async getUser(id) {
        this.logger.log(`Fetching user with id: ${id}`);
        
        if (this.userCache.has(id)) {
            this.logger.log('User found in cache');
            return this.userCache.get(id);
        }
        
        const sql = 'SELECT * FROM users WHERE id = ?';
        const result = await this.db.query(sql, [id]);
        
        if (result && result[0]) {
            this.userCache.set(id, result[0]);
            return result[0];
        }
        
        this.logger.warn(`User with id ${id} not found`);
        return null;
    }

    clearCache() {
        this.userCache.clear();
        this.logger.log('User cache cleared');
    }

    async createUser(userData) {
        this.logger.log('Creating new user:', userData.email);
        
        // Validate user data
        if (!userData.name || !userData.email || !userData.role) {
            throw new Error('Missing required user fields');
        }
        
        if (!this.validateEmail(userData.email)) {
            throw new Error('Invalid email format');
        }
        
        const sql = 'INSERT INTO users (name, email, role) VALUES (?, ?, ?)';
        const params = [userData.name, userData.email, userData.role];
        const result = await this.db.query(sql, params);
        
        this.logger.log('User created successfully with id:', result.insertId);
        this.clearCache();
        
        return result;
    }

    validateEmail(email) {
        const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return regex.test(email);
    }

    async updateUser(id, userData) {
        this.logger.log(`Updating user ${id}`);
        
        const existingUser = await this.getUser(id);
        if (!existingUser) {
            throw new Error(`User with id ${id} not found`);
        }
        
        const sql = 'UPDATE users SET name = ?, email = ?, role = ? WHERE id = ?';
        const params = [
            userData.name || existingUser.name,
            userData.email || existingUser.email,
            userData.role || existingUser.role,
            id
        ];
        
        const result = await this.db.query(sql, params);
        this.clearCache();
        
        this.logger.log('User updated successfully');
        return result;
    }

    async deleteUser(id) {
        this.logger.log(`Deleting user ${id}`);
        
        const existingUser = await this.getUser(id);
        if (!existingUser) {
            throw new Error(`User with id ${id} not found`);
        }
        
        const sql = 'DELETE FROM users WHERE id = ?';
        const result = await this.db.query(sql, [id]);
        this.clearCache();
        
        this.logger.log('User deleted successfully');
        return result;
    }

    async listAllUsers(limit = 100, offset = 0) {
        this.logger.log(`Listing users with limit ${limit}, offset ${offset}`);
        const sql = 'SELECT * FROM users LIMIT ? OFFSET ?';
        return await this.db.query(sql, [limit, offset]);
    }
}

class AuthenticationService {
    constructor(userService) {
        this.userService = userService;
        this.sessions = new Map();
        this.sessionTimeout = 3600000; // 1 hour
        this.maxSessions = 10000;
    }

    async login(email, password) {
        console.log(`Login attempt for email: ${email}`);
        
        if (!email || !password) {
            throw new Error('Email and password are required');
        }
        
        const user = await this.findUserByEmail(email);
        if (!user) {
            console.warn('User not found:', email);
            throw new Error('User not found');
        }

        const isValid = await this.validatePassword(password, user.password);
        if (!isValid) {
            console.warn('Invalid password for user:', email);
            throw new Error('Invalid password');
        }

        const token = this.generateToken();
        const sessionData = {
            userId: user.id,
            createdAt: Date.now(),
            lastActivity: Date.now()
        };
        
        this.sessions.set(token, sessionData);
        this.cleanupExpiredSessions();
        
        console.log('Login successful for user:', user.id);
        return token;
    }

    cleanupExpiredSessions() {
        if (this.sessions.size > this.maxSessions) {
            const now = Date.now();
            for (const [token, data] of this.sessions.entries()) {
                if (now - data.lastActivity > this.sessionTimeout) {
                    this.sessions.delete(token);
                }
            }
        }
    }

    async logout(token) {
        console.log('Logging out session:', token);
        
        if (!this.sessions.has(token)) {
            console.warn('Session not found:', token);
            return false;
        }
        
        this.sessions.delete(token);
        console.log('Logout successful');
        return true;
    }

    validateToken(token) {
        if (!this.sessions.has(token)) {
            return false;
        }
        
        const sessionData = this.sessions.get(token);
        const now = Date.now();
        
        if (now - sessionData.lastActivity > this.sessionTimeout) {
            this.sessions.delete(token);
            return false;
        }
        
        sessionData.lastActivity = now;
        return true;
    }

    getSessionInfo(token) {
        return this.sessions.get(token);
    }
}

class ProductService {
    constructor(dbManager) {
        this.db = dbManager;
        this.products = [];
        this.productCache = new Map();
        this.categoryCache = new Map();
    }

    async getProduct(id) {
        console.log(`Fetching product: ${id}`);
        
        if (this.productCache.has(id)) {
            console.log('Product found in cache');
            return this.productCache.get(id);
        }
        
        const sql = 'SELECT * FROM products WHERE id = ?';
        const result = await this.db.query(sql, [id]);
        
        if (result && result[0]) {
            this.productCache.set(id, result[0]);
            return result[0];
        }
        
        return null;
    }

    clearCache() {
        this.productCache.clear();
        this.categoryCache.clear();
    }

    async listProducts(filters) {
        console.log('Listing products with filters:', filters);
        
        let sql = 'SELECT * FROM products WHERE 1=1';
        const params = [];

        if (filters.category) {
            sql += ' AND category = ?';
            params.push(filters.category);
        }

        if (filters.minPrice !== undefined) {
            sql += ' AND price >= ?';
            params.push(filters.minPrice);
        }

        if (filters.maxPrice !== undefined) {
            sql += ' AND price <= ?';
            params.push(filters.maxPrice);
        }

        if (filters.inStock) {
            sql += ' AND stock > 0';
        }

        if (filters.sortBy) {
            const allowedSorts = ['price', 'name', 'category'];
            if (allowedSorts.includes(filters.sortBy)) {
                const order = filters.sortOrder === 'desc' ? 'DESC' : 'ASC';
                sql += ` ORDER BY ${filters.sortBy} ${order}`;
            }
        }

        if (filters.limit) {
            sql += ' LIMIT ?';
            params.push(filters.limit);
        }

        const results = await this.db.query(sql, params);
        console.log(`Found ${results.length} products`);
        return results;
    }

    async createProduct(productData) {
        console.log('Creating new product:', productData.name);
        
        // Validation
        if (!productData.name || !productData.price || !productData.category) {
            throw new Error('Missing required product fields');
        }
        
        if (productData.price < 0) {
            throw new Error('Price cannot be negative');
        }
        
        const sql = 'INSERT INTO products (name, description, price, category) VALUES (?, ?, ?, ?)';
        const params = [
            productData.name,
            productData.description || '',
            productData.price,
            productData.category
        ];
        
        const result = await this.db.query(sql, params);
        this.clearCache();
        
        console.log('Product created with id:', result.insertId);
        return result;
    }

    async updateProduct(id, productData) {
        console.log(`Updating product ${id}`);
        
        const existing = await this.getProduct(id);
        if (!existing) {
            throw new Error('Product not found');
        }
        
        const sql = 'UPDATE products SET name = ?, description = ?, price = ?, category = ? WHERE id = ?';
        const params = [
            productData.name || existing.name,
            productData.description || existing.description,
            productData.price !== undefined ? productData.price : existing.price,
            productData.category || existing.category,
            id
        ];
        
        const result = await this.db.query(sql, params);
        this.clearCache();
        
        return result;
    }

    async deleteProduct(id) {
        console.log(`Deleting product ${id}`);
        const sql = 'DELETE FROM products WHERE id = ?';
        const result = await this.db.query(sql, [id]);
        this.clearCache();
        return result;
    }
}

class OrderService {
    constructor(dbManager, productService) {
        this.db = dbManager;
        this.productService = productService;
    }

    async createOrder(userId, items) {
        const total = await this.calculateTotal(items);
        const sql = 'INSERT INTO orders (user_id, total, status) VALUES (?, ?, ?)';
        const orderId = await this.db.query(sql, [userId, total, 'pending']);

        for (const item of items) {
            await this.addOrderItem(orderId, item);
        }

        return orderId;
    }

    async calculateTotal(items) {
        let total = 0;
        for (const item of items) {
            const product = await this.productService.getProduct(item.productId);
            total += product.price * item.quantity;
        }
        return total;
    }

    async getOrder(id) {
        const sql = 'SELECT * FROM orders WHERE id = ?';
        const result = await this.db.query(sql, [id]);
        return result[0];
    }
}

class PaymentService {
    constructor(orderService) {
        this.orderService = orderService;
    }

    async processPayment(orderId, paymentMethod) {
        const order = await this.orderService.getOrder(orderId);
        
        if (!order) {
            throw new Error('Order not found');
        }

        // Process payment logic here
        const result = await this.chargePayment(paymentMethod, order.total);
        
        if (result.success) {
            await this.updateOrderStatus(orderId, 'paid');
            return { success: true, transactionId: result.transactionId };
        }

        return { success: false, error: result.error };
    }

    async chargePayment(paymentMethod, amount) {
        // Simulate payment processing
        return { success: true, transactionId: 'TXN' + Date.now() };
    }

    async updateOrderStatus(orderId, status) {
        const sql = 'UPDATE orders SET status = ? WHERE id = ?';
        return await this.db.query(sql, [status, orderId]);
    }
}

// Utility functions
function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email);
}

function generateRandomId() {
    return Math.random().toString(36).substring(2, 15);
}

function formatDate(date) {
    return date.toISOString().split('T')[0];
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Export modules
module.exports = {
    DatabaseManager,
    UserService,
    AuthenticationService,
    ProductService,
    OrderService,
    PaymentService,
    validateEmail,
    generateRandomId,
    formatDate,
    sleep
};
