"""
Tests for categories API endpoints.
"""

import pytest
from fastapi import status

from models.category import Category


class TestCreateCategory:
    """Tests for POST /categories/"""

    def test_create_category_success(self, client, db_session):
        """Test successful creation of a category."""
        category_data = {
            "name": "Electrónica",
            "description": "Componentes electrónicos y accesorios",
        }

        response = client.post("/categories/", json=category_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == category_data["name"]
        assert data["description"] == category_data["description"]
        assert "id" in data
        assert "date_created" in data
        assert data["date_updated"] is None

        # Verify it was saved in database
        db_category = db_session.query(Category).filter_by(name="Electrónica").first()
        assert db_category is not None
        assert db_category.description == category_data["description"]

    def test_create_category_without_description(self, client, db_session):
        """Test creating a category without description."""
        category_data = {
            "name": "Tornillería",
        }

        response = client.post("/categories/", json=category_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Tornillería"
        assert data["description"] is None

        # Verify in database
        db_category = db_session.query(Category).filter_by(name="Tornillería").first()
        assert db_category is not None
        assert db_category.description is None

    def test_create_category_duplicate_name(self, client, db_session):
        """Test creating a category with duplicate name fails."""
        # Create first category
        category = Category(
            name="Herramientas", description="Herramientas de uso general"
        )
        db_session.add(category)
        db_session.commit()

        # Try to create another with same name
        category_data = {
            "name": "Herramientas",
            "description": "Otra descripción",
        }

        response = client.post("/categories/", json=category_data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "already exists" in response.json()["detail"]
        assert "Herramientas" in response.json()["detail"]

    def test_create_category_missing_name(self, client):
        """Test creating a category without name fails."""
        category_data = {
            "description": "Descripción sin nombre",
        }

        response = client.post("/categories/", json=category_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_category_empty_name(self, client):
        """Test creating a category with empty name fails validation."""
        category_data = {
            "name": "",
            "description": "Descripción",
        }

        response = client.post("/categories/", json=category_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_create_category_null_description(self, client, db_session):
        """Test creating a category with explicit null description."""
        category_data = {
            "name": "Categoría sin descripción",
            "description": None,
        }

        response = client.post("/categories/", json=category_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["description"] is None

    def test_create_multiple_categories(self, client, db_session):
        """Test creating multiple different categories."""
        categories_data = [
            {"name": "Categoría 1", "description": "Primera categoría"},
            {"name": "Categoría 2", "description": "Segunda categoría"},
            {"name": "Categoría 3", "description": "Tercera categoría"},
        ]

        for category_data in categories_data:
            response = client.post("/categories/", json=category_data)
            assert response.status_code == status.HTTP_201_CREATED

        # Verify all were created
        db_categories = db_session.query(Category).all()
        assert len(db_categories) == 3

    def test_create_category_with_long_description(self, client):
        """Test creating a category with a long description."""
        category_data = {
            "name": "Categoría Test",
            "description": "A" * 255,  # Max length from model is 255
        }

        response = client.post("/categories/", json=category_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert len(data["description"]) == 255

    def test_create_category_with_special_characters(self, client, db_session):
        """Test creating a category with special characters in name."""
        category_data = {
            "name": "Categoría & Símbolos #1",
            "description": "Descripción con símbolos: @#$%",
        }

        response = client.post("/categories/", json=category_data)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == category_data["name"]
        assert data["description"] == category_data["description"]

    def test_create_category_case_sensitive_names(self, client, db_session):
        """Test that category names are case sensitive."""
        # Create first category
        category_data_1 = {
            "name": "electrónica",
            "description": "Minúsculas",
        }
        response_1 = client.post("/categories/", json=category_data_1)
        assert response_1.status_code == status.HTTP_201_CREATED

        # Try to create with different case
        category_data_2 = {
            "name": "Electrónica",
            "description": "Mayúscula inicial",
        }
        response_2 = client.post("/categories/", json=category_data_2)

        # Depending on your business logic, this might succeed or fail
        # Current implementation checks exact name match, so different case should succeed
        assert response_2.status_code == status.HTTP_201_CREATED

    def test_create_category_whitespace_in_name(self, client):
        """Test creating a category with leading/trailing whitespace."""
        category_data = {
            "name": "  Espacios  ",
            "description": "Con espacios",
        }

        response = client.post("/categories/", json=category_data)

        # Current implementation doesn't trim whitespace
        # You might want to add .strip() in the business logic
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "  Espacios  "
