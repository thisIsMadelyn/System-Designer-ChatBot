"""
Mock responses για testing χωρίς OpenAI API key.
Ενεργοποιείται με USE_MOCK=true στο .env
"""

from models.schemas import (
    RequirementsOutput,
    ArchitectureOutput,
    DatabaseOutput,
    ApiDesignOutput,
)

MOCK_REQUIREMENTS = RequirementsOutput(
    functional_requirements=[
        "User registration and authentication",
        "Product catalog with search and filtering",
        "Shopping cart management",
        "Order placement and tracking",
        "Admin panel for product management",
    ],
    non_functional_requirements=[
        "Response time under 200ms for 95% of requests",
        "99.9% uptime SLA",
        "Support for 10,000 concurrent users",
        "Data encryption at rest and in transit",
    ],
    constraints=[
        "Team of 3 developers",
        "3 month delivery deadline",
        "Must use Java Spring Boot",
        "Budget limited to cloud tier services",
    ],
    scale_estimation="~5,000 users/day, ~50,000 requests/day, low-medium traffic",
    summary="E-commerce platform requiring secure auth, product management, and order processing at medium scale.",
)

MOCK_ARCHITECTURE = ArchitectureOutput(
    architecture_style="Monolith",
    services=[
        {"name": "AuthModule", "responsibility": "JWT-based login, registration, token refresh", "spring_boot_module": "com.app.auth"},
        {"name": "ProductModule", "responsibility": "CRUD for products, categories, search", "spring_boot_module": "com.app.product"},
        {"name": "OrderModule", "responsibility": "Cart, order placement, order history", "spring_boot_module": "com.app.order"},
        {"name": "AdminModule", "responsibility": "Admin dashboard, user and product management", "spring_boot_module": "com.app.admin"},
    ],
    tradeoffs=[
        "Pro: Simpler deployment — single Docker container",
        "Pro: Easier debugging and local development",
        "Pro: Lower infrastructure cost at this scale",
        "Con: Harder to scale individual modules independently",
        "Con: Risk of tight coupling between modules over time",
    ],
    tech_stack={
        "backend": "Spring Boot 3.2",
        "database": "MySQL 8",
        "auth": "Spring Security 6 + JWT (jjwt)",
        "containerization": "Docker + Docker Compose",
        "other": ["Lombok", "MapStruct", "Hibernate Validator"],
    },
    summary="Modular monolith chosen due to small team size, tight deadline, and medium scale.",
)

MOCK_DATABASE = DatabaseOutput(
    entities=[
        {
            "name": "User",
            "fields": [
                {"name": "id", "type": "BIGINT", "constraints": "PRIMARY KEY AUTO_INCREMENT"},
                {"name": "email", "type": "VARCHAR(255)", "constraints": "NOT NULL UNIQUE"},
                {"name": "password_hash", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
                {"name": "role", "type": "ENUM('USER','ADMIN')", "constraints": "NOT NULL DEFAULT 'USER'"},
                {"name": "created_at", "type": "TIMESTAMP", "constraints": "DEFAULT CURRENT_TIMESTAMP"},
            ],
        },
        {
            "name": "Product",
            "fields": [
                {"name": "id", "type": "BIGINT", "constraints": "PRIMARY KEY AUTO_INCREMENT"},
                {"name": "name", "type": "VARCHAR(255)", "constraints": "NOT NULL"},
                {"name": "description", "type": "TEXT", "constraints": ""},
                {"name": "price", "type": "DECIMAL(10,2)", "constraints": "NOT NULL"},
                {"name": "stock", "type": "INT", "constraints": "NOT NULL DEFAULT 0"},
                {"name": "category_id", "type": "BIGINT", "constraints": "FOREIGN KEY REFERENCES categories(id)"},
            ],
        },
        {
            "name": "Order",
            "fields": [
                {"name": "id", "type": "BIGINT", "constraints": "PRIMARY KEY AUTO_INCREMENT"},
                {"name": "user_id", "type": "BIGINT", "constraints": "NOT NULL FOREIGN KEY REFERENCES users(id)"},
                {"name": "status", "type": "ENUM('PENDING','CONFIRMED','SHIPPED','DELIVERED','CANCELLED')", "constraints": "NOT NULL DEFAULT 'PENDING'"},
                {"name": "total_amount", "type": "DECIMAL(10,2)", "constraints": "NOT NULL"},
                {"name": "created_at", "type": "TIMESTAMP", "constraints": "DEFAULT CURRENT_TIMESTAMP"},
            ],
        },
    ],
    relationships=[
        "User 1--N Order : places",
        "Order M--N Product : contains (via order_items)",
        "Product M--1 Category : belongs to",
    ],
    mysql_schema_sql="""CREATE TABLE users (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('USER','ADMIN') NOT NULL DEFAULT 'USER',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE products (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    category_id BIGINT,
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

CREATE TABLE orders (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    status ENUM('PENDING','CONFIRMED','SHIPPED','DELIVERED','CANCELLED') NOT NULL DEFAULT 'PENDING',
    total_amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE order_items (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id),
    FOREIGN KEY (product_id) REFERENCES products(id)
);""",
    erd_mermaid="""erDiagram
    USER {
        bigint id PK
        varchar email
        varchar password_hash
        enum role
        timestamp created_at
    }
    CATEGORY {
        bigint id PK
        varchar name
    }
    PRODUCT {
        bigint id PK
        varchar name
        text description
        decimal price
        int stock
        bigint category_id FK
    }
    ORDER {
        bigint id PK
        bigint user_id FK
        enum status
        decimal total_amount
        timestamp created_at
    }
    ORDER_ITEMS {
        bigint id PK
        bigint order_id FK
        bigint product_id FK
        int quantity
        decimal unit_price
    }
    USER ||--o{ ORDER : places
    ORDER ||--|{ ORDER_ITEMS : contains
    PRODUCT ||--o{ ORDER_ITEMS : included_in
    CATEGORY ||--o{ PRODUCT : categorizes""",
    summary="5 tables covering users, products, categories, orders and order items with proper FK constraints.",
)

MOCK_API = ApiDesignOutput(
    endpoints=[
        {
            "method": "POST",
            "path": "/api/auth/register",
            "description": "Register new user",
            "request_body": {"email": "string", "password": "string"},
            "response": {"id": "number", "email": "string"},
            "auth_required": False,
            "roles": [],
        },
        {
            "method": "POST",
            "path": "/api/auth/login",
            "description": "Login and get JWT token",
            "request_body": {"email": "string", "password": "string"},
            "response": {"token": "string", "expires_in": "number"},
            "auth_required": False,
            "roles": [],
        },
        {
            "method": "GET",
            "path": "/api/products",
            "description": "List all products with pagination",
            "request_body": {},
            "response": {"content": "array", "totalPages": "number"},
            "auth_required": False,
            "roles": [],
        },
        {
            "method": "POST",
            "path": "/api/products",
            "description": "Create new product (admin only)",
            "request_body": {"name": "string", "price": "number", "stock": "number"},
            "response": {"id": "number"},
            "auth_required": True,
            "roles": ["ADMIN"],
        },
        {
            "method": "POST",
            "path": "/api/orders",
            "description": "Place a new order",
            "request_body": {"items": "array"},
            "response": {"orderId": "number", "status": "string"},
            "auth_required": True,
            "roles": ["USER"],
        },
        {
            "method": "GET",
            "path": "/api/orders/{id}",
            "description": "Get order details",
            "request_body": {},
            "response": {"id": "number", "status": "string", "items": "array"},
            "auth_required": True,
            "roles": ["USER", "ADMIN"],
        },
    ],
    spring_security_config="""SecurityFilterChain configuration:
- Permit all: POST /api/auth/register, POST /api/auth/login, GET /api/products
- Require ADMIN role: POST/PUT/DELETE /api/products, GET /api/admin/**
- Require USER role: POST /api/orders, GET /api/orders/**
- JWT filter added before UsernamePasswordAuthenticationFilter
- Token expiry: 24 hours, signed with HS256
- Stateless session management (no server-side sessions)""",
    api_mermaid_diagram="""sequenceDiagram
    Client->>+API: POST /api/auth/login
    API->>+DB: Validate credentials
    DB-->>-API: User found
    API-->>-Client: JWT Token

    Client->>+API: POST /api/orders (Bearer token)
    API->>+JWTFilter: Validate token
    JWTFilter-->>-API: User authenticated
    API->>+DB: Create order
    DB-->>-API: Order created
    API-->>-Client: orderId + status""",
    docker_compose_snippet="""version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - SPRING_DATASOURCE_URL=jdbc:mysql://db:3306/ecommerce
      - SPRING_DATASOURCE_USERNAME=root
      - SPRING_DATASOURCE_PASSWORD=secret
      - JWT_SECRET=your-secret-key
    depends_on:
      - db
  db:
    image: mysql:8
    environment:
      MYSQL_ROOT_PASSWORD: secret
      MYSQL_DATABASE: ecommerce
    volumes:
      - mysql_data:/var/lib/mysql
volumes:
  mysql_data:""",
    summary="RESTful API with JWT auth, role-based access control, product and order management endpoints.",
)