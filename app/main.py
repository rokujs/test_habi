import logging

from fastapi import FastAPI

from routers import categories_router, spare_parts_router, orders_router, orders_image_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

app = FastAPI(
    title="Maintenance Service API",
    description="API for managing spare parts and service orders",
    version="1.0.0",
)

# Register routers
app.include_router(categories_router)
app.include_router(spare_parts_router)
app.include_router(orders_router)
app.include_router(orders_image_router)


@app.get("/", tags=["Health"])
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "message": "Maintenance Service API is running"}

