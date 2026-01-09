"""
Tests for service orders API endpoints.
"""
import pytest
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from fastapi import status

from models.service_order import ServiceOrder, ServiceOrderStatus
from models.spare_part import SparePart
from models.category import Category


class TestCreateServiceOrder:
    """Tests for POST /orders/"""

    def test_create_service_order_success(self, client, db_session):
        """Test successful creation of a service order."""
        # Create spare parts
        spare_part1 = SparePart(
            name="Tornillo",
            sku="A-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
        )
        spare_part2 = SparePart(
            name="Tuerca",
            sku="B-STL-M10-20",
            price=Decimal("0.50"),
            stock=200,
        )
        db_session.add_all([spare_part1, spare_part2])
        db_session.commit()

        order_data = {
            "request_id": 12345,
            "items": [
                {"spare_part_id": spare_part1.id, "quantity": 10},
                {"spare_part_id": spare_part2.id, "quantity": 20},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["request_id"] == 12345
        assert data["status"] == ServiceOrderStatus.PENDING
        assert Decimal(data["total"]) == Decimal("20.00")  # (10 * 1.00) + (20 * 0.50)
        assert len(data["items"]) == 2
        assert "id" in data
        assert "date_created" in data

        # Verify stock was reduced
        db_session.refresh(spare_part1)
        db_session.refresh(spare_part2)
        assert spare_part1.stock == 90  # 100 - 10
        assert spare_part2.stock == 180  # 200 - 20

    def test_create_service_order_single_item(self, client, db_session):
        """Test creating an order with a single item."""
        spare_part = SparePart(
            name="Resistencia",
            sku="C-ELC-100R-1W",
            price=Decimal("0.25"),
            stock=500,
        )
        db_session.add(spare_part)
        db_session.commit()

        order_data = {
            "request_id": 11111,
            "items": [
                {"spare_part_id": spare_part.id, "quantity": 5},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert Decimal(data["total"]) == Decimal("1.25")  # 5 * 0.25
        assert len(data["items"]) == 1

    def test_create_service_order_idempotency(self, client, db_session):
        """Test idempotency - same request_id returns existing order."""
        spare_part = SparePart(
            name="Tornillo",
            sku="D-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
        )
        db_session.add(spare_part)
        db_session.commit()

        order_data = {
            "request_id": 99999,
            "items": [
                {"spare_part_id": spare_part.id, "quantity": 10},
            ],
        }

        # First request
        response1 = client.post("/orders/", json=order_data)
        assert response1.status_code == status.HTTP_201_CREATED
        order_id_1 = response1.json()["id"]
        
        # Check stock after first order
        db_session.refresh(spare_part)
        assert spare_part.stock == 90

        # Second request with same request_id (within idempotency window)
        response2 = client.post("/orders/", json=order_data)
        assert response2.status_code == status.HTTP_201_CREATED
        order_id_2 = response2.json()["id"]

        # Should return the same order
        assert order_id_1 == order_id_2
        
        # Stock should not be reduced again
        db_session.refresh(spare_part)
        assert spare_part.stock == 90  # Still 90, not 80

    def test_create_service_order_spare_part_not_found(self, client, db_session):
        """Test creating an order with non-existent spare part fails."""
        order_data = {
            "request_id": 22222,
            "items": [
                {"spare_part_id": 99999, "quantity": 10},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
        assert "99999" in response.json()["detail"]

    def test_create_service_order_multiple_missing_spare_parts(self, client, db_session):
        """Test creating an order with multiple non-existent spare parts."""
        spare_part = SparePart(
            name="Tornillo",
            sku="E-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
        )
        db_session.add(spare_part)
        db_session.commit()

        order_data = {
            "request_id": 33333,
            "items": [
                {"spare_part_id": spare_part.id, "quantity": 5},
                {"spare_part_id": 88888, "quantity": 10},
                {"spare_part_id": 77777, "quantity": 15},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_create_service_order_insufficient_stock(self, client, db_session):
        """Test creating an order with insufficient stock fails."""
        spare_part = SparePart(
            name="Tornillo",
            sku="F-STL-M10-50",
            price=Decimal("1.00"),
            stock=5,  # Only 5 in stock
        )
        db_session.add(spare_part)
        db_session.commit()

        order_data = {
            "request_id": 44444,
            "items": [
                {"spare_part_id": spare_part.id, "quantity": 10},  # Requesting 10
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient stock" in response.json()["detail"]
        assert "Available: 5" in response.json()["detail"]
        assert "Requested: 10" in response.json()["detail"]

        # Verify stock was not reduced
        db_session.refresh(spare_part)
        assert spare_part.stock == 5

    def test_create_service_order_exact_stock_available(self, client, db_session):
        """Test creating an order with exact stock available succeeds."""
        spare_part = SparePart(
            name="Tornillo",
            sku="G-STL-M10-50",
            price=Decimal("1.00"),
            stock=10,
        )
        db_session.add(spare_part)
        db_session.commit()

        order_data = {
            "request_id": 55555,
            "items": [
                {"spare_part_id": spare_part.id, "quantity": 10},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_201_CREATED
        
        # Stock should be zero now
        db_session.refresh(spare_part)
        assert spare_part.stock == 0

    def test_create_service_order_one_item_insufficient_stock(self, client, db_session):
        """Test order fails if any item has insufficient stock."""
        spare_part1 = SparePart(
            name="Tornillo",
            sku="H-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
        )
        spare_part2 = SparePart(
            name="Tuerca",
            sku="I-STL-M10-20",
            price=Decimal("0.50"),
            stock=5,  # Insufficient
        )
        db_session.add_all([spare_part1, spare_part2])
        db_session.commit()

        order_data = {
            "request_id": 66666,
            "items": [
                {"spare_part_id": spare_part1.id, "quantity": 10},
                {"spare_part_id": spare_part2.id, "quantity": 10},  # Not enough
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Insufficient stock" in response.json()["detail"]

        # Verify no stock was reduced (transaction rollback)
        db_session.refresh(spare_part1)
        db_session.refresh(spare_part2)
        assert spare_part1.stock == 100
        assert spare_part2.stock == 5

    def test_create_service_order_empty_items(self, client):
        """Test creating an order with empty items list fails validation."""
        order_data = {
            "request_id": 77777,
            "items": [],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_service_order_missing_items(self, client):
        """Test creating an order without items field fails validation."""
        order_data = {
            "request_id": 88888,
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_service_order_invalid_request_id(self, client):
        """Test creating an order with invalid request_id fails validation."""
        order_data = {
            "request_id": 0,  # Must be > 0
            "items": [
                {"spare_part_id": 1, "quantity": 10},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_service_order_negative_request_id(self, client):
        """Test creating an order with negative request_id fails validation."""
        order_data = {
            "request_id": -1,
            "items": [
                {"spare_part_id": 1, "quantity": 10},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_service_order_zero_quantity(self, client, db_session):
        """Test creating an order with zero quantity fails validation."""
        spare_part = SparePart(
            name="Tornillo",
            sku="J-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
        )
        db_session.add(spare_part)
        db_session.commit()

        order_data = {
            "request_id": 99000,
            "items": [
                {"spare_part_id": spare_part.id, "quantity": 0},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_service_order_negative_quantity(self, client, db_session):
        """Test creating an order with negative quantity fails validation."""
        spare_part = SparePart(
            name="Tornillo",
            sku="K-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
        )
        db_session.add(spare_part)
        db_session.commit()

        order_data = {
            "request_id": 99001,
            "items": [
                {"spare_part_id": spare_part.id, "quantity": -5},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_service_order_with_category(self, client, db_session):
        """Test creating an order with spare parts that have categories."""
        category = Category(name="Tornillería")
        db_session.add(category)
        db_session.commit()

        spare_part = SparePart(
            name="Tornillo",
            sku="L-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
            category_id=category.id,
        )
        db_session.add(spare_part)
        db_session.commit()

        order_data = {
            "request_id": 99002,
            "items": [
                {"spare_part_id": spare_part.id, "quantity": 10},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["items"][0]["spare_part"]["category"]["name"] == "Tornillería"

    def test_create_service_order_large_quantity(self, client, db_session):
        """Test creating an order with large quantity."""
        spare_part = SparePart(
            name="Tornillo",
            sku="M-STL-M10-50",
            price=Decimal("0.10"),
            stock=10000,
        )
        db_session.add(spare_part)
        db_session.commit()

        order_data = {
            "request_id": 99003,
            "items": [
                {"spare_part_id": spare_part.id, "quantity": 5000},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert Decimal(data["total"]) == Decimal("500.00")  # 5000 * 0.10

    def test_create_service_order_duplicate_spare_part_in_items(self, client, db_session):
        """Test creating an order with duplicate spare part entries."""
        spare_part = SparePart(
            name="Tornillo",
            sku="N-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
        )
        db_session.add(spare_part)
        db_session.commit()

        order_data = {
            "request_id": 99004,
            "items": [
                {"spare_part_id": spare_part.id, "quantity": 10},
                {"spare_part_id": spare_part.id, "quantity": 5},
            ],
        }

        response = client.post("/orders/", json=order_data)

        # Current implementation allows duplicates, creates separate line items
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["items"]) == 2
        assert Decimal(data["total"]) == Decimal("15.00")  # (10 + 5) * 1.00

        # Stock reduced by total quantity
        db_session.refresh(spare_part)
        assert spare_part.stock == 85  # 100 - 15

    def test_create_service_order_decimal_prices(self, client, db_session):
        """Test order total calculation with decimal prices."""
        spare_part = SparePart(
            name="Component",
            sku="O-ELC-RES-100",
            price=Decimal("0.33"),  # Price with decimals
            stock=100,
        )
        db_session.add(spare_part)
        db_session.commit()

        order_data = {
            "request_id": 99005,
            "items": [
                {"spare_part_id": spare_part.id, "quantity": 3},
            ],
        }

        response = client.post("/orders/", json=order_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert Decimal(data["total"]) == Decimal("0.99")  # 3 * 0.33
