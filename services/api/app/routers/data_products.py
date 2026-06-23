"""Data product catalog API."""
from fastapi import APIRouter

from app.services.assessment_results_product import load_data_products_catalog

router = APIRouter(prefix="/data-products", tags=["data-products"])


@router.get("/catalog")
async def get_data_products_catalog():
    """Return the Information Layer Gold data product registry."""
    return load_data_products_catalog()
