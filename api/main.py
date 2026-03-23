"""FastAPI application exposing a route optimization endpoint.

This application serves a single endpoint that accepts origins and
destinations and returns an optimized route plan using a genetic algorithm.
"""

from typing import Any, cast
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from api.schemas import (
    FleetTotals,
    RouteItem,
    RouteTotals,
    OptimizeRouteRequest,
    OptimizeRouteResponse,
    VehicleRouteResponse,
)
from api.dependencies import get_adaptive_ga_config, get_route_optimization_service
from src.application.route_optimization_service import RouteOptimizationService

logger = logging.getLogger("api.main")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="TSP Genetic Algorithm API",
    description="API for route optimization using Genetic Algorithm, considering priorities and ETA via OpenStreetMap.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_request_payload(request: Request, call_next):
    body = await request.body()
    if body:
        logger.info("REQUEST PAYLOAD: %s", body.decode("utf-8"))
    return await call_next(request)


@app.on_event("startup")
async def validate_adaptive_ga_config() -> None:
    """Validate that the API adaptive GA configuration is available at startup.

    Raises:
        FileNotFoundError: If the required repository-root `config.json` file is
            missing.
        ValueError: If the config file contents are invalid.
    """
    get_adaptive_ga_config()


@app.post("/optimize_route", response_model=OptimizeRouteResponse)
async def optimize_route(
    request: OptimizeRouteRequest,
    service: RouteOptimizationService = Depends(get_route_optimization_service),
    adaptive_config: dict[str, Any] = Depends(get_adaptive_ga_config),
):
    """Handle route optimization requests.

    The endpoint accepts an origin plus a list of destinations and returns a
    recommended set of routes per vehicle along with aggregated metrics.

    Args:
        request: The optimized route request payload.
        service: The injected route optimization service.
        adaptive_config: Cached adaptive GA state-graph configuration.

    Returns:
        An OptimizeRouteResponse containing routes per vehicle and totals.
    """
    try:
        destinations_formatted: list[tuple[str | tuple[float, float], int]] = [
            (
                (
                    cast(tuple[float, float], (dest.location[0], dest.location[1]))
                    if isinstance(dest.location, list)
                    else dest.location
                ),
                dest.priority,
            )
            for dest in request.destinations
        ]

        origin_converted: str | tuple[float, float]
        if isinstance(request.origin, list):
            origin_converted = (request.origin[0], request.origin[1])
        else:
            origin_converted = request.origin

        result = service.optimize(
            origin=origin_converted,
            destinations=destinations_formatted,
            max_generation=request.max_generation,
            max_processing_time=request.max_processing_time,
            vehicle_count=request.vehicle_count,
            population_size=request.population_size,
            weight_type=request.weight_type,
            cost_type=request.cost_type,
            adaptive_config=adaptive_config,
        )

        routes_by_vehicle = []
        for vehicle_route in result.best_route.routes_by_vehicle:
            route_items = []
            for node in vehicle_route.segments:
                route_items.append(
                    RouteItem(
                        location=node.name,
                        coords=list(node.coords),
                        length=node.length,
                        path=[list(point) for point in node.path],
                        eta=node.eta,
                        cost=node.cost,
                    )
                )
            routes_by_vehicle.append(
                VehicleRouteResponse(
                    vehicle_id=vehicle_route.vehicle_id,
                    route=route_items,
                    totals=RouteTotals(
                        total_length=vehicle_route.total_length,
                        total_eta=vehicle_route.total_eta,
                        total_cost=vehicle_route.total_cost,
                    ),
                )
            )

        totals = FleetTotals(
            total_length=result.best_route.total_length,
            min_vehicle_eta=result.best_route.min_vehicle_eta,
            max_vehicle_eta=result.best_route.max_vehicle_eta,
            total_cost=result.best_route.total_cost,
        )

        return OptimizeRouteResponse(
            routes_by_vehicle=routes_by_vehicle,
            totals=totals,
            best_fitness=result.best_fitness,
            population_size=result.population_size,
            generations_run=result.generations_run,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error in optimization: {str(e)}",
        )


@app.get("/")
async def root():
    return {
        "message": "TSP Genetic Algorithm API is running. Access /docs for interactive documentation."
    }
