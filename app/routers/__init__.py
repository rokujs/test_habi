from routers.categories_api_view import router as categories_router
from routers.spare_parts_api_views import router as spare_parts_router
from routers.orders_api_view import router as orders_router

__all__ = [
    "categories_router",
    "spare_parts_router",
    "orders_router",
]
