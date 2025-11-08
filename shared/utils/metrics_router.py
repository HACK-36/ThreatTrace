"""
Prometheus Metrics Router for FastAPI
Exposes /metrics endpoint for all Cerberus services
"""
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

router = APIRouter()


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint
    
    Returns all registered metrics in Prometheus text format
    """
    data = generate_latest()
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
