package com.example.performance;

import java.util.*;
import java.time.LocalDateTime;
import java.sql.*;

/**
 * Large Java file for performance testing
 * Contains multiple classes and methods
 */

public class PerformanceTestApplication {
    
    private DatabaseManager dbManager;
    private UserService userService;
    private ProductService productService;
    
    public PerformanceTestApplication(String connectionString) {
        this.dbManager = new DatabaseManager(connectionString);
        this.userService = new UserService(dbManager);
        this.productService = new ProductService(dbManager);
    }
    
    public void initialize() {
        System.out.println("Initializing application...");
        dbManager.connect();
        System.out.println("Application initialized successfully");
    }
    
    public void shutdown() {
        System.out.println("Shutting down application...");
        dbManager.disconnect();
        System.out.println("Application shut down successfully");
    }
}

class DatabaseManager {
    private String connectionString;
    private Connection connection;
    private Map<String, PreparedStatement> statementCache;
    private int maxCacheSize = 100;
    private int retryAttempts = 3;
    private int connectionTimeout = 30000;
    
    public DatabaseManager(String connectionString) {
        this.connectionString = connectionString;
        this.statementCache = new HashMap<>();
    }
    
    public void connect() {
        int attempts = 0;
        Exception lastException = null;
        
        while (attempts < retryAttempts) {
            try {
                System.out.println("Connecting to database (attempt " + (attempts + 1) + "): " + connectionString);
                connection = DriverManager.getConnection(connectionString);
                connection.setAutoCommit(false);
                System.out.println("Database connection established successfully");
                return;
            } catch (SQLException e) {
                attempts++;
                lastException = e;
                System.err.println("Connection attempt " + attempts + " failed: " + e.getMessage());
                
                if (attempts < retryAttempts) {
                    try {
                        Thread.sleep(1000 * attempts);
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                    }
                }
            }
        }
        
        if (lastException != null) {
            System.err.println("Failed to connect after " + retryAttempts + " attempts");
        }
    }
    
    public void commit() throws SQLException {
        if (connection != null && !connection.getAutoCommit()) {
            connection.commit();
        }
    }
    
    public void rollback() throws SQLException {
        if (connection != null && !connection.getAutoCommit()) {
            connection.rollback();
        }
    }
    
    public void disconnect() {
        try {
            if (connection != null && !connection.isClosed()) {
                // Close all cached statements
                for (PreparedStatement stmt : statementCache.values()) {
                    if (stmt != null && !stmt.isClosed()) {
                        stmt.close();
                    }
                }
                statementCache.clear();
                
                connection.close();
                System.out.println("Database connection closed successfully");
            }
        } catch (SQLException e) {
            System.err.println("Error closing connection: " + e.getMessage());
        }
    }
    
    public boolean isConnected() {
        try {
            return connection != null && !connection.isClosed() && connection.isValid(5);
        } catch (SQLException e) {
            return false;
        }
    }
    
    public ResultSet executeQuery(String sql, Object... params) throws SQLException {
        System.out.println("Executing query: " + sql);
        long startTime = System.currentTimeMillis();
        
        if (!isConnected()) {
            throw new SQLException("Database connection is not available");
        }
        
        PreparedStatement stmt = getPreparedStatement(sql);
        setParameters(stmt, params);
        ResultSet rs = stmt.executeQuery();
        
        long executionTime = System.currentTimeMillis() - startTime;
        System.out.println("Query executed in " + executionTime + "ms");
        
        return rs;
    }
    
    public int executeUpdate(String sql, Object... params) throws SQLException {
        System.out.println("Executing update: " + sql);
        long startTime = System.currentTimeMillis();
        
        if (!isConnected()) {
            throw new SQLException("Database connection is not available");
        }
        
        PreparedStatement stmt = getPreparedStatement(sql);
        setParameters(stmt, params);
        int rowsAffected = stmt.executeUpdate();
        
        long executionTime = System.currentTimeMillis() - startTime;
        System.out.println("Update executed in " + executionTime + "ms, rows affected: " + rowsAffected);
        
        return rowsAffected;
    }
    
    private PreparedStatement getPreparedStatement(String sql) throws SQLException {
        if (!statementCache.containsKey(sql)) {
            if (statementCache.size() >= maxCacheSize) {
                clearOldestStatements();
            }
            statementCache.put(sql, connection.prepareStatement(sql));
            System.out.println("Statement cached: " + sql.substring(0, Math.min(50, sql.length())));
        }
        return statementCache.get(sql);
    }
    
    private void clearOldestStatements() {
        int toRemove = maxCacheSize / 4;
        Iterator<Map.Entry<String, PreparedStatement>> iterator = statementCache.entrySet().iterator();
        
        while (iterator.hasNext() && toRemove > 0) {
            Map.Entry<String, PreparedStatement> entry = iterator.next();
            try {
                entry.getValue().close();
            } catch (SQLException e) {
                System.err.println("Error closing statement: " + e.getMessage());
            }
            iterator.remove();
            toRemove--;
        }
    }
    
    private void setParameters(PreparedStatement stmt, Object... params) throws SQLException {
        for (int i = 0; i < params.length; i++) {
            stmt.setObject(i + 1, params[i]);
        }
    }
}

class User {
    private int id;
    private String username;
    private String email;
    private LocalDateTime createdAt;
    private boolean isActive;
    
    public User(int id, String username, String email) {
        this.id = id;
        this.username = username;
        this.email = email;
        this.createdAt = LocalDateTime.now();
        this.isActive = true;
    }
    
    public int getId() { return id; }
    public void setId(int id) { this.id = id; }
    
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    
    public String getEmail() { return email; }
    public void setEmail(String email) { this.email = email; }
    
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    
    public boolean isActive() { return isActive; }
    public void setActive(boolean active) { isActive = active; }
    
    @Override
    public String toString() {
        return "User{id=" + id + ", username='" + username + "', email='" + email + "'}";
    }
}

class UserService {
    private DatabaseManager db;
    private Map<Integer, User> userCache;
    private long cacheTimeout = 300000; // 5 minutes
    
    public UserService(DatabaseManager db) {
        this.db = db;
        this.userCache = new HashMap<>();
    }
    
    public User findById(int id) throws SQLException {
        System.out.println("Finding user by ID: " + id);
        
        // Check cache
        if (userCache.containsKey(id)) {
            System.out.println("User found in cache");
            return userCache.get(id);
        }
        
        String sql = "SELECT * FROM users WHERE id = ?";
        ResultSet rs = db.executeQuery(sql, id);
        
        if (rs.next()) {
            User user = mapToUser(rs);
            userCache.put(id, user);
            return user;
        }
        
        System.out.println("User not found with ID: " + id);
        return null;
    }
    
    public void clearCache() {
        userCache.clear();
        System.out.println("User cache cleared");
    }
    
    public User findByEmail(String email) throws SQLException {
        System.out.println("Finding user by email: " + email);
        
        if (email == null || email.trim().isEmpty()) {
            throw new IllegalArgumentException("Email cannot be null or empty");
        }
        
        if (!isValidEmail(email)) {
            System.out.println("Invalid email format: " + email);
            return null;
        }
        
        String sql = "SELECT * FROM users WHERE email = ?";
        ResultSet rs = db.executeQuery(sql, email);
        
        if (rs.next()) {
            return mapToUser(rs);
        }
        
        System.out.println("User not found with email: " + email);
        return null;
    }
    
    private boolean isValidEmail(String email) {
        return email.matches("^[A-Za-z0-9+_.-]+@(.+)$");
    }
    
    public int createUser(User user) throws SQLException {
        System.out.println("Creating user: " + user.getUsername());
        
        // Validation
        if (user.getUsername() == null || user.getUsername().trim().isEmpty()) {
            throw new IllegalArgumentException("Username cannot be null or empty");
        }
        
        if (user.getEmail() == null || !isValidEmail(user.getEmail())) {
            throw new IllegalArgumentException("Invalid email address");
        }
        
        // Check if user already exists
        User existing = findByEmail(user.getEmail());
        if (existing != null) {
            throw new SQLException("User with email " + user.getEmail() + " already exists");
        }
        
        String sql = "INSERT INTO users (username, email, created_at, is_active) VALUES (?, ?, ?, ?)";
        int rowsAffected = db.executeUpdate(sql, user.getUsername(), user.getEmail(), 
                               user.getCreatedAt(), user.isActive());
        
        clearCache();
        System.out.println("User created successfully");
        return rowsAffected;
    }
    
    public boolean updateUser(User user) throws SQLException {
        System.out.println("Updating user: " + user.getId());
        
        // Check if user exists
        User existing = findById(user.getId());
        if (existing == null) {
            throw new SQLException("User with id " + user.getId() + " not found");
        }
        
        // Validate email if changed
        if (!user.getEmail().equals(existing.getEmail()) && !isValidEmail(user.getEmail())) {
            throw new IllegalArgumentException("Invalid email address");
        }
        
        String sql = "UPDATE users SET username = ?, email = ?, is_active = ? WHERE id = ?";
        int rowsAffected = db.executeUpdate(sql, user.getUsername(), user.getEmail(), 
                                           user.isActive(), user.getId());
        
        clearCache();
        System.out.println("User updated successfully");
        return rowsAffected > 0;
    }
    
    public boolean deleteUser(int id) throws SQLException {
        System.out.println("Deleting user: " + id);
        
        // Check if user exists
        User existing = findById(id);
        if (existing == null) {
            throw new SQLException("User with id " + id + " not found");
        }
        
        String sql = "DELETE FROM users WHERE id = ?";
        int rowsAffected = db.executeUpdate(sql, id);
        
        clearCache();
        System.out.println("User deleted successfully");
        return rowsAffected > 0;
    }
    
    public List<User> listUsers(int limit, int offset) throws SQLException {
        System.out.println("Listing users with limit=" + limit + ", offset=" + offset);
        
        if (limit <= 0 || limit > 1000) {
            throw new IllegalArgumentException("Limit must be between 1 and 1000");
        }
        
        if (offset < 0) {
            throw new IllegalArgumentException("Offset must be non-negative");
        }
        
        String sql = "SELECT * FROM users LIMIT ? OFFSET ?";
        ResultSet rs = db.executeQuery(sql, limit, offset);
        
        List<User> users = new ArrayList<>();
        while (rs.next()) {
            users.add(mapToUser(rs));
        }
        
        System.out.println("Found " + users.size() + " users");
        return users;
    }
    
    public int countUsers() throws SQLException {
        String sql = "SELECT COUNT(*) as count FROM users";
        ResultSet rs = db.executeQuery(sql);
        
        if (rs.next()) {
            return rs.getInt("count");
        }
        return 0;
    }
    
    public List<User> searchUsers(String keyword, int limit) throws SQLException {
        System.out.println("Searching users with keyword: " + keyword);
        
        String sql = "SELECT * FROM users WHERE username LIKE ? OR email LIKE ? LIMIT ?";
        String searchTerm = "%" + keyword + "%";
        ResultSet rs = db.executeQuery(sql, searchTerm, searchTerm, limit);
        
        List<User> users = new ArrayList<>();
        while (rs.next()) {
            users.add(mapToUser(rs));
        }
        
        return users;
    }
    
    private User mapToUser(ResultSet rs) throws SQLException {
        User user = new User(
            rs.getInt("id"),
            rs.getString("username"),
            rs.getString("email")
        );
        user.setActive(rs.getBoolean("is_active"));
        return user;
    }
}

class Product {
    private int id;
    private String name;
    private String description;
    private double price;
    private String category;
    private int stock;
    
    public Product(int id, String name, String description, double price, String category, int stock) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.price = price;
        this.category = category;
        this.stock = stock;
    }
    
    public int getId() { return id; }
    public void setId(int id) { this.id = id; }
    
    public String getName() { return name; }
    public void setName(String name) { this.name = name; }
    
    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }
    
    public double getPrice() { return price; }
    public void setPrice(double price) { this.price = price; }
    
    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }
    
    public int getStock() { return stock; }
    public void setStock(int stock) { this.stock = stock; }
    
    @Override
    public String toString() {
        return "Product{id=" + id + ", name='" + name + "', price=" + price + "}";
    }
}

class ProductService {
    private DatabaseManager db;
    
    public ProductService(DatabaseManager db) {
        this.db = db;
    }
    
    public Product findById(int id) throws SQLException {
        String sql = "SELECT * FROM products WHERE id = ?";
        ResultSet rs = db.executeQuery(sql, id);
        
        if (rs.next()) {
            return mapToProduct(rs);
        }
        return null;
    }
    
    public List<Product> findByCategory(String category) throws SQLException {
        String sql = "SELECT * FROM products WHERE category = ?";
        ResultSet rs = db.executeQuery(sql, category);
        
        List<Product> products = new ArrayList<>();
        while (rs.next()) {
            products.add(mapToProduct(rs));
        }
        return products;
    }
    
    public int createProduct(Product product) throws SQLException {
        String sql = "INSERT INTO products (name, description, price, category, stock) VALUES (?, ?, ?, ?, ?)";
        return db.executeUpdate(sql, product.getName(), product.getDescription(), 
                               product.getPrice(), product.getCategory(), product.getStock());
    }
    
    public boolean updateStock(int productId, int quantity) throws SQLException {
        String sql = "UPDATE products SET stock = stock + ? WHERE id = ?";
        int rowsAffected = db.executeUpdate(sql, quantity, productId);
        return rowsAffected > 0;
    }
    
    private Product mapToProduct(ResultSet rs) throws SQLException {
        return new Product(
            rs.getInt("id"),
            rs.getString("name"),
            rs.getString("description"),
            rs.getDouble("price"),
            rs.getString("category"),
            rs.getInt("stock")
        );
    }
}

class Order {
    private int id;
    private int userId;
    private double total;
    private String status;
    private LocalDateTime createdAt;
    private List<OrderItem> items;
    
    public Order(int id, int userId, double total, String status) {
        this.id = id;
        this.userId = userId;
        this.total = total;
        this.status = status;
        this.createdAt = LocalDateTime.now();
        this.items = new ArrayList<>();
    }
    
    public void addItem(OrderItem item) {
        items.add(item);
    }
    
    public int getId() { return id; }
    public int getUserId() { return userId; }
    public double getTotal() { return total; }
    public String getStatus() { return status; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public List<OrderItem> getItems() { return items; }
}

class OrderItem {
    private int productId;
    private int quantity;
    private double price;
    
    public OrderItem(int productId, int quantity, double price) {
        this.productId = productId;
        this.quantity = quantity;
        this.price = price;
    }
    
    public int getProductId() { return productId; }
    public int getQuantity() { return quantity; }
    public double getPrice() { return price; }
    public double getSubtotal() { return quantity * price; }
}
