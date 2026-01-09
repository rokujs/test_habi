"""
Tests for spare parts API endpoints.
"""

import pytest
from decimal import Decimal
from fastapi import status

from models.category import Category
from models.spare_part import SparePart


class TestCreateSparePart:
    """Tests for POST /items/"""

    def test_create_spare_part_success(self, client, db_session):
        """Test successful creation of a spare part."""
        spare_part_data = {
            "name": "Tornillo hexagonal",
            "sku": "A-STL-M10-50",
            "price": 0.75,
            "stock": 100,
        }

        response = client.post("/items/", json=spare_part_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == spare_part_data["name"]
        assert data["sku"] == spare_part_data["sku"]
        assert Decimal(data["price"]) == Decimal("0.75")
        assert data["stock"] == spare_part_data["stock"]
        assert data["category_id"] is None
        assert "id" in data
        assert "date_created" in data

        # Verify it was saved in database
        db_spare_part = (
            db_session.query(SparePart).filter_by(sku="A-STL-M10-50").first()
        )
        assert db_spare_part is not None
        assert db_spare_part.name == spare_part_data["name"]

    def test_create_spare_part_with_category(self, client, db_session):
        """Test creating a spare part with a category."""
        # Create category first
        category = Category(name="Tornillería", description="Tornillos y tuercas")
        db_session.add(category)
        db_session.commit()

        spare_part_data = {
            "name": "Tuerca hexagonal",
            "sku": "B-STL-M8-20",
            "price": 0.50,
            "stock": 200,
            "category_id": category.id,
        }

        response = client.post("/items/", json=spare_part_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["category_id"] == category.id
        assert data["category"]["name"] == "Tornillería"

    def test_create_spare_part_duplicate_sku(self, client, db_session):
        """Test creating a spare part with duplicate SKU fails."""
        spare_part = SparePart(
            name="Tornillo original",
            sku="C-STL-M12-40",
            price=Decimal("1.00"),
            stock=50,
        )
        db_session.add(spare_part)
        db_session.commit()

        spare_part_data = {
            "name": "Tornillo duplicado",
            "sku": "C-STL-M12-40",
            "price": 2.00,
            "stock": 30,
        }

        response = client.post("/items/", json=spare_part_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]

    def test_create_spare_part_invalid_sku_format(self, client, db_session):
        """Test creating a spare part with invalid SKU format fails."""
        spare_part_data = {
            "name": "Tornillo",
            "sku": "INVALID-FORMAT",
            "price": 1.00,
            "stock": 10,
        }

        response = client.post("/items/", json=spare_part_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid SKU format" in response.json()["detail"]

    def test_create_spare_part_empty_sku_component(self, client, db_session):
        """Test creating a spare part with empty SKU component fails."""
        spare_part_data = {
            "name": "Tornillo",
            "sku": "A--M10-50",
            "price": 1.00,
            "stock": 10,
        }

        response = client.post("/items/", json=spare_part_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "non-empty" in response.json()["detail"]

    def test_create_spare_part_negative_price(self, client):
        """Test creating a spare part with negative price fails validation."""
        spare_part_data = {
            "name": "Tornillo",
            "sku": "A-STL-M10-50",
            "price": -1.00,
            "stock": 10,
        }

        response = client.post("/items/", json=spare_part_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_spare_part_negative_stock(self, client):
        """Test creating a spare part with negative stock fails validation."""
        spare_part_data = {
            "name": "Tornillo",
            "sku": "A-STL-M10-50",
            "price": 1.00,
            "stock": -5,
        }

        response = client.post("/items/", json=spare_part_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_spare_part_missing_required_fields(self, client):
        """Test creating a spare part without required fields fails."""
        spare_part_data = {
            "name": "Tornillo",
            # Missing sku and price
        }

        response = client.post("/items/", json=spare_part_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestUpdateSparePart:
    """Tests for PATCH /items/{sku}"""

    def test_update_spare_part_price(self, client, db_session):
        """Test updating spare part price."""
        spare_part = SparePart(
            name="Tornillo",
            sku="D-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
        )
        db_session.add(spare_part)
        db_session.commit()

        update_data = {"price": 1.50}

        response = client.patch("/items/D-STL-M10-50", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert Decimal(data["price"]) == Decimal("1.50")
        assert data["stock"] == 100  # Stock unchanged

        # Verify in database
        db_session.refresh(spare_part)
        assert spare_part.price == Decimal("1.50")

    def test_update_spare_part_stock(self, client, db_session):
        """Test updating spare part stock."""
        spare_part = SparePart(
            name="Tuerca",
            sku="E-STL-M8-20",
            price=Decimal("0.50"),
            stock=50,
        )
        db_session.add(spare_part)
        db_session.commit()

        update_data = {"stock": 150}

        response = client.patch("/items/E-STL-M8-20", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["stock"] == 150
        assert Decimal(data["price"]) == Decimal("0.50")  # Price unchanged

    def test_update_spare_part_both_fields(self, client, db_session):
        """Test updating both price and stock."""
        spare_part = SparePart(
            name="Arandela",
            sku="F-STL-M6-10",
            price=Decimal("0.25"),
            stock=200,
        )
        db_session.add(spare_part)
        db_session.commit()

        update_data = {"price": 0.30, "stock": 250}

        response = client.patch("/items/F-STL-M6-10", json=update_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert Decimal(data["price"]) == Decimal("0.30")
        assert data["stock"] == 250

    def test_update_spare_part_not_found(self, client):
        """Test updating a non-existent spare part."""
        update_data = {"price": 1.00}

        response = client.patch("/items/NONEXISTENT-SKU", json=update_data)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]

    def test_update_spare_part_no_fields(self, client, db_session):
        """Test updating without providing any fields fails."""
        spare_part = SparePart(
            name="Tornillo",
            sku="G-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
        )
        db_session.add(spare_part)
        db_session.commit()

        update_data = {}

        response = client.patch("/items/G-STL-M10-50", json=update_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "No fields to update" in response.json()["detail"]

    def test_update_spare_part_negative_price(self, client, db_session):
        """Test updating with negative price fails validation."""
        spare_part = SparePart(
            name="Tornillo",
            sku="H-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
        )
        db_session.add(spare_part)
        db_session.commit()

        update_data = {"price": -1.00}

        response = client.patch("/items/H-STL-M10-50", json=update_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_update_spare_part_negative_stock(self, client, db_session):
        """Test updating with negative stock fails validation."""
        spare_part = SparePart(
            name="Tornillo",
            sku="I-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
        )
        db_session.add(spare_part)
        db_session.commit()

        update_data = {"stock": -10}

        response = client.patch("/items/I-STL-M10-50", json=update_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestListSpareParts:
    """Tests for GET /items/"""

    def test_list_spare_parts_empty(self, client):
        """Test listing spare parts when database is empty."""
        response = client.get("/items/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_spare_parts(self, client, db_session):
        """Test listing multiple spare parts."""
        spare_parts = [
            SparePart(
                name="Tornillo A",
                sku="J-STL-M10-50",
                price=Decimal("1.00"),
                stock=100,
            ),
            SparePart(
                name="Tornillo B",
                sku="K-STL-M8-40",
                price=Decimal("0.80"),
                stock=150,
            ),
            SparePart(
                name="Tuerca A",
                sku="L-STL-M10-20",
                price=Decimal("0.50"),
                stock=200,
            ),
        ]
        db_session.add_all(spare_parts)
        db_session.commit()

        response = client.get("/items/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert data[0]["name"] == "Tornillo A"
        assert data[1]["name"] == "Tornillo B"
        assert data[2]["name"] == "Tuerca A"

    def test_list_spare_parts_with_categories(self, client, db_session):
        """Test listing spare parts with their categories."""
        category = Category(name="Tornillería", description="Tornillos y tuercas")
        db_session.add(category)
        db_session.commit()

        spare_part = SparePart(
            name="Tornillo con categoría",
            sku="M-STL-M10-50",
            price=Decimal("1.00"),
            stock=100,
            category_id=category.id,
        )
        db_session.add(spare_part)
        db_session.commit()

        response = client.get("/items/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["category"]["id"] == category.id

    def test_list_spare_parts_pagination_skip(self, client, db_session):
        """Test pagination with skip parameter."""
        spare_parts = [
            SparePart(
                name=f"Tornillo {i}",
                sku=f"N{i}-STL-M10-50",
                price=Decimal("1.00"),
                stock=100,
            )
            for i in range(5)
        ]
        db_session.add_all(spare_parts)
        db_session.commit()

        response = client.get("/items/?skip=2")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3  # 5 total - 2 skipped
        assert data[0]["name"] == "Tornillo 2"

    def test_list_spare_parts_pagination_limit(self, client, db_session):
        """Test pagination with limit parameter."""
        spare_parts = [
            SparePart(
                name=f"Tornillo {i}",
                sku=f"O{i}-STL-M10-50",
                price=Decimal("1.00"),
                stock=100,
            )
            for i in range(10)
        ]
        db_session.add_all(spare_parts)
        db_session.commit()

        response = client.get("/items/?limit=5")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 5

    def test_list_spare_parts_pagination_skip_and_limit(self, client, db_session):
        """Test pagination with both skip and limit parameters."""
        spare_parts = [
            SparePart(
                name=f"Tornillo {i}",
                sku=f"P{i}-STL-M10-50",
                price=Decimal("1.00"),
                stock=100,
            )
            for i in range(10)
        ]
        db_session.add_all(spare_parts)
        db_session.commit()

        response = client.get("/items/?skip=3&limit=4")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 4
        assert data[0]["name"] == "Tornillo 3"
        assert data[3]["name"] == "Tornillo 6"

    def test_list_spare_parts_with_and_without_category(self, client, db_session):
        """Test listing spare parts where some have categories and some don't."""
        category = Category(name="Electrónica")
        db_session.add(category)
        db_session.commit()

        spare_parts = [
            SparePart(
                name="Con categoría",
                sku="Q-STL-M10-50",
                price=Decimal("1.00"),
                stock=100,
                category_id=category.id,
            ),
            SparePart(
                name="Sin categoría",
                sku="R-STL-M8-40",
                price=Decimal("0.80"),
                stock=150,
            ),
        ]
        db_session.add_all(spare_parts)
        db_session.commit()

        response = client.get("/items/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 2
        assert data[0]["category"] is not None
        assert data[1]["category"] is None
