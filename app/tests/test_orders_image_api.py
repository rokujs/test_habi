"""
Tests for service order images API endpoints.
"""
import pytest
from io import BytesIO
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal
from fastapi import status

from models.service_order import ServiceOrder, ServiceOrderStatus
from models.service_order_image import ServiceOrderImage
from models.spare_part import SparePart
from services.s3_service import S3UploadError


@pytest.fixture
def sample_order(db_session):
    """Create a sample service order for testing."""
    spare_part = SparePart(
        name="Tornillo",
        sku="TEST-STL-M10-50",
        price=Decimal("1.00"),
        stock=100,
    )
    db_session.add(spare_part)
    db_session.commit()

    order = ServiceOrder(
        request_id=12345,
        status=ServiceOrderStatus.PENDING,
        total=Decimal("10.00"),
    )
    db_session.add(order)
    db_session.commit()
    
    return order


@pytest.fixture
def mock_s3_upload():
    """Mock S3 service upload to avoid actual S3 calls."""
    with patch('routers.orders_image_api_views.s3_service.upload_image') as mock:
        mock.return_value = "https://s3.amazonaws.com/bucket/orders/1/image.jpg"
        yield mock


class TestUploadOrderImage:
    """Tests for POST /orders/{order_id}/image/"""

    def test_upload_image_success_jpeg(self, client, db_session, sample_order, mock_s3_upload):
        """Test successful image upload with JPEG format."""
        # Create a fake image file
        file_content = b"fake image content"
        files = {
            "file": ("test_image.jpg", BytesIO(file_content), "image/jpeg")
        }

        response = client.post(f"/orders/{sample_order.id}/image/", files=files)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["order_id"] == sample_order.id
        assert data["file_name"] == "test_image.jpg"
        assert "https://s3.amazonaws.com" in data["image_url"]
        assert "id" in data
        assert "date_created" in data

        # Verify it was saved in database
        db_image = db_session.query(ServiceOrderImage).filter_by(order_id=sample_order.id).first()
        assert db_image is not None
        assert db_image.file_name == "test_image.jpg"

        # Verify S3 upload was called
        mock_s3_upload.assert_called_once()

    def test_upload_image_success_png(self, client, db_session, sample_order, mock_s3_upload):
        """Test successful image upload with PNG format."""
        file_content = b"fake png content"
        files = {
            "file": ("test_image.png", BytesIO(file_content), "image/png")
        }

        response = client.post(f"/orders/{sample_order.id}/image/", files=files)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["file_name"] == "test_image.png"

    def test_upload_image_success_webp(self, client, db_session, sample_order, mock_s3_upload):
        """Test successful image upload with WebP format."""
        file_content = b"fake webp content"
        files = {
            "file": ("test_image.webp", BytesIO(file_content), "image/webp")
        }

        response = client.post(f"/orders/{sample_order.id}/image/", files=files)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["file_name"] == "test_image.webp"

    def test_upload_image_order_not_found(self, client, mock_s3_upload):
        """Test uploading image to non-existent order fails."""
        file_content = b"fake image content"
        files = {
            "file": ("test_image.jpg", BytesIO(file_content), "image/jpeg")
        }

        response = client.post("/orders/99999/image/", files=files)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
        assert "99999" in response.json()["detail"]

        # Verify S3 upload was not called
        mock_s3_upload.assert_not_called()

    def test_upload_image_invalid_file_type(self, client, sample_order, mock_s3_upload):
        """Test uploading non-image file type fails."""
        file_content = b"fake pdf content"
        files = {
            "file": ("document.pdf", BytesIO(file_content), "application/pdf")
        }

        response = client.post(f"/orders/{sample_order.id}/image/", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid file type" in response.json()["detail"]

        # Verify S3 upload was not called
        mock_s3_upload.assert_not_called()

    def test_upload_image_invalid_file_type_text(self, client, sample_order, mock_s3_upload):
        """Test uploading text file fails."""
        file_content = b"just some text"
        files = {
            "file": ("file.txt", BytesIO(file_content), "text/plain")
        }

        response = client.post(f"/orders/{sample_order.id}/image/", files=files)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_image_s3_upload_error(self, client, sample_order):
        """Test handling S3 upload failure."""
        with patch('routers.orders_image_api_views.s3_service.upload_image') as mock_upload:
            mock_upload.side_effect = S3UploadError("S3 connection failed")

            file_content = b"fake image content"
            files = {
                "file": ("test_image.jpg", BytesIO(file_content), "image/jpeg")
            }

            response = client.post(f"/orders/{sample_order.id}/image/", files=files)

            assert response.status_code == status.HTTP_502_BAD_GATEWAY
            assert "Failed to upload image" in response.json()["detail"]

    def test_upload_multiple_images_to_same_order(self, client, db_session, sample_order, mock_s3_upload):
        """Test uploading multiple images to the same order."""
        # Upload first image
        files1 = {
            "file": ("image1.jpg", BytesIO(b"content1"), "image/jpeg")
        }
        response1 = client.post(f"/orders/{sample_order.id}/image/", files=files1)
        assert response1.status_code == status.HTTP_201_CREATED

        # Upload second image
        files2 = {
            "file": ("image2.jpg", BytesIO(b"content2"), "image/jpeg")
        }
        response2 = client.post(f"/orders/{sample_order.id}/image/", files=files2)
        assert response2.status_code == status.HTTP_201_CREATED

        # Verify both images were saved
        db_images = db_session.query(ServiceOrderImage).filter_by(order_id=sample_order.id).all()
        assert len(db_images) == 2

    def test_upload_image_no_file_provided(self, client, sample_order):
        """Test uploading without providing a file fails."""
        response = client.post(f"/orders/{sample_order.id}/image/")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_upload_image_filename_without_extension(self, client, sample_order, mock_s3_upload):
        """Test uploading image with filename without extension."""
        file_content = b"fake image content"
        files = {
            "file": ("noextension", BytesIO(file_content), "image/jpeg")
        }

        response = client.post(f"/orders/{sample_order.id}/image/", files=files)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["file_name"] == "noextension"

    def test_upload_image_generates_unique_filename(self, client, sample_order, mock_s3_upload):
        """Test that uploaded images get unique filenames in S3."""
        files = {
            "file": ("test.jpg", BytesIO(b"content"), "image/jpeg")
        }

        response = client.post(f"/orders/{sample_order.id}/image/", files=files)

        assert response.status_code == status.HTTP_201_CREATED
        
        # Check that S3 upload was called with a unique filename containing UUID
        call_args = mock_s3_upload.call_args
        s3_filename = call_args.kwargs['file_name']
        assert f"orders/{sample_order.id}/" in s3_filename
        assert ".jpg" in s3_filename


class TestListOrderImages:
    """Tests for GET /orders/{order_id}/images/"""

    def test_list_images_empty(self, client, sample_order):
        """Test listing images when order has no images."""
        response = client.get(f"/orders/{sample_order.id}/images/")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    def test_list_images_single(self, client, db_session, sample_order):
        """Test listing a single image."""
        image = ServiceOrderImage(
            order_id=sample_order.id,
            file_name="test_image.jpg",
            image_url="https://s3.amazonaws.com/bucket/image.jpg",
        )
        db_session.add(image)
        db_session.commit()

        response = client.get(f"/orders/{sample_order.id}/images/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["file_name"] == "test_image.jpg"
        assert data[0]["image_url"] == "https://s3.amazonaws.com/bucket/image.jpg"
        assert data[0]["order_id"] == sample_order.id

    def test_list_images_multiple(self, client, db_session, sample_order):
        """Test listing multiple images."""
        images = [
            ServiceOrderImage(
                order_id=sample_order.id,
                file_name=f"image_{i}.jpg",
                image_url=f"https://s3.amazonaws.com/bucket/image_{i}.jpg",
            )
            for i in range(3)
        ]
        db_session.add_all(images)
        db_session.commit()

        response = client.get(f"/orders/{sample_order.id}/images/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 3
        assert all("file_name" in img for img in data)
        assert all("image_url" in img for img in data)

    def test_list_images_order_not_found(self, client):
        """Test listing images for non-existent order fails."""
        response = client.get("/orders/99999/images/")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]
        assert "99999" in response.json()["detail"]

    def test_list_images_only_shows_order_images(self, client, db_session, sample_order):
        """Test that listing only shows images for the specific order."""
        # Create another order
        order2 = ServiceOrder(
            request_id=54321,
            status=ServiceOrderStatus.PENDING,
            total=Decimal("20.00"),
        )
        db_session.add(order2)
        db_session.commit()

        # Add images to both orders
        image1 = ServiceOrderImage(
            order_id=sample_order.id,
            file_name="order1_image.jpg",
            image_url="https://s3.amazonaws.com/bucket/order1.jpg",
        )
        image2 = ServiceOrderImage(
            order_id=order2.id,
            file_name="order2_image.jpg",
            image_url="https://s3.amazonaws.com/bucket/order2.jpg",
        )
        db_session.add_all([image1, image2])
        db_session.commit()

        # List images for first order
        response = client.get(f"/orders/{sample_order.id}/images/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        assert data[0]["file_name"] == "order1_image.jpg"
        assert data[0]["order_id"] == sample_order.id

    def test_list_images_includes_metadata(self, client, db_session, sample_order):
        """Test that listing includes all required metadata."""
        image = ServiceOrderImage(
            order_id=sample_order.id,
            file_name="test_image.jpg",
            image_url="https://s3.amazonaws.com/bucket/image.jpg",
        )
        db_session.add(image)
        db_session.commit()

        response = client.get(f"/orders/{sample_order.id}/images/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) == 1
        image_data = data[0]
        assert "id" in image_data
        assert "order_id" in image_data
        assert "file_name" in image_data
        assert "image_url" in image_data
        assert "date_created" in image_data
        assert "date_updated" in image_data
