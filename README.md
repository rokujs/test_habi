# Maintenance Service API

A microservice built with FastAPI to manage maintenance service orders, spare parts inventory, and service order images.

## 📋 Project Description

This project is a backend API that allows you to:
- Register and manage spare parts (items) with categories
- Create and manage maintenance service orders
- Handle service order items (linking spare parts to orders)
- Upload and manage service order images to AWS S3
- Track changes with audit logging

## 🏗️ Architecture & Technology Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Migrations**: Alembic
- **Storage**: AWS S3 (boto3)
- **Containerization**: Docker & Docker Compose
- **Testing**: Pytest
- **Python Version**: 3.12+

## 📁 Project Structure

```
habi_test/
├── app/
│   ├── core/          # Core configurations and utilities
│   ├── models/        # SQLAlchemy database models
│   ├── routers/       # API endpoints
│   ├── schemas/       # Pydantic schemas for validation
│   ├── services/      # Business logic and external services (S3)
│   ├── migrations/    # Alembic database migrations
│   ├── tests/         # Unit and integration tests
│   └── main.py        # Application entry point
├── docker-compose.yml
└── README.md
```

## 🚀 Getting Started

### Prerequisites

* **Docker**: Essential for running the application in a containerized environment. You can find installation instructions in the [official Docker documentation](https://docs.docker.com/get-docker/).
* **Git**: Necessary for cloning the project repository. Installation instructions are available in the [official Git documentation](https://git-scm.com/install/linux).

### Installation & Setup

1. **Clone the repository**
```bash
git clone https://github.com/rokujs/test_habi.git
cd test_habi
```

2. **Environment Variables**

You can use the provided `.env.example` file as a template. Copy it to create your own `.env` file:

```bash
cp app/.env.example app/.env
```

The `.env.example` file contains all the necessary environment variables with example values:
```env
# Database
DB_USER=app_habi
DB_PASSWORD=7slm59JUebyYZQ625vUJ
DB_HOST=postgres
DB_PORT=5432
DB_NAME=habi_db

# AWS S3
AWS_S3_BUCKET=maintenance-images-habi-test-sebastian
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=awsaccesskey
AWS_SECRET_ACCESS_KEY=awssecretkey
```

**Note**: Update the AWS credentials with your actual values for production use.

3. **Build and Run with Docker Compose**
```bash
docker compose build
```
```
docker compose up -d
```

The API will be available at:
- **API**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc

4. **Run Database Migrations**

Migrations are automatically applied on container startup via the `docker-entrypoint.sh` script, so you don't need to run them manually for the initial setup.

However, if you need to manually run migrations (for example, after pulling new changes or creating new migrations), follow these steps:

1. Access the backend container's bash shell:
```bash
docker compose exec backend bash
```

2. Activate the virtual environment:
```bash
shell
```

3. Run the migration command:
```bash
migrate
```

This `migrate` command is an alias configured in the container that executes `alembic upgrade head`, applying all pending database migrations.

## 🧪 Running Tests

To run tests, you need to access the backend container first:

```bash
docker compose exec backend bash
```

Activate the virtual environment:
```bash
shell
```

Once the environment is activated, you can run:

**All tests:**
```bash
pytest
```

**Specific test file with verbose output:**
```bash
pytest tests/test_orders_api.py -v
```


## 🔄 Idempotency Implementation

### How Idempotency Works in the Orders Endpoint

The `POST /api/v1/orders/` endpoint implements **idempotency** to prevent duplicate orders when the same request is submitted multiple times within a short time window.

**Implementation Details:**

1. **Request ID**: Each order creation request must include a unique `request_id` field in the payload.

2. **Duplicate Detection**: The system checks if an order with the same `request_id` has been processed recently (within a configurable time window).

3. **ProcessedRequest Model**: A `ProcessedRequest` table stores:
   - `request_id`: The unique identifier from the request
   - `created_at`: Timestamp of when the request was first processed
   - `response_data`: The original response data (order details)

4. **Flow**:
   - When a POST request arrives with a `request_id`, the system first queries the `ProcessedRequest` table
   - If found and still within the valid time window, it returns the previously created order (HTTP 200 with the original response)
   - If not found or expired, it creates a new order and stores the `request_id` with the response
   - This ensures that retries, network failures, or accidental duplicate submissions don't create multiple orders

5. **Benefits**:
   - Prevents duplicate orders from client-side retries
   - Safe for network failures and timeouts
   - RESTful API best practice implementation

**Example Request:**
```json
{
  "request_id": "unique-request-123",
  "items": [
    {
      "spare_part_id": 1,
      "quantity": 2
    }
  ]
}
```

If this request is sent twice within the time window, the second request will return the same order without creating a duplicate.

## 🎯 Technical Implementation Highlights

### 1. **Pythonic Code**
- Proper use of identity (`is`) vs equality (`==`) comparisons
- Custom `@measure_time` decorator to log execution time of endpoints
- Type hints throughout the codebase
- Clean code structure following PEP 8

### 2. **Database Optimization**
- **B-Tree Index** on `sku` column for fast lookups
- SQLAlchemy ORM with proper session management
- `try...except...finally` blocks for reliable connection handling
- Database migrations with Alembic

### 3. **AWS S3 Integration**
- `s3_service.py` module with boto3 integration
- Proper error handling for AWS operations
- Support for uploading service order images
- Environment-based configuration

### 4. **Performance Monitoring**
- Custom decorator `@measure_time` logs endpoint execution time
- Helps identify performance bottlenecks
- Console logging for development/debugging

### 5. **Testing**
- Comprehensive test suite with pytest
- Test coverage for all major endpoints
- Integration tests with test database
- Fixtures for reusable test data

## 🔧 Database Schema

### Main Models

- **Category**: Product categories (e.g., Electronics, Hardware)
- **SparePart**: Inventory items with SKU, price, and stock
- **ServiceOrder**: Maintenance service orders with client info
- **ServiceOrderItem**: Junction table linking orders to spare parts
- **ServiceOrderImage**: Images stored in S3 linked to orders
- **ProcessedRequest**: Idempotency tracking for order creation
- **Auditor**: Audit log for tracking changes

## 📝 Development

### Creating a New Migration

To create a new database migration after modifying models:

1. Access the backend container:
```bash
docker compose exec backend bash
```

2. Activate the virtual environment:
```bash
shell
```

3. Generate the migration:
```bash
makemigrations "Description of changes"
```

This will automatically detect model changes and create a new migration file in the `migrations/versions/` directory.
