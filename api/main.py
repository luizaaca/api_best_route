from typing import cast
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    FleetTotals,
    RouteItem,
    RouteTotals,
    OptimizeRouteRequest,
    OptimizeRouteResponse,
    VehicleRouteResponse,
)
from api.dependencies import get_route_optimization_service
from src.application.route_optimization_service import RouteOptimizationService

app = FastAPI(
    title="TSP Genetic Algorithm API",
    description="API para otimização de rotas usando Algoritmo Genético, considerando prioridades e ETA via OpenStreetMap.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/optimize_route", response_model=OptimizeRouteResponse)
async def optimize_route(
    request: OptimizeRouteRequest,
    service: RouteOptimizationService = Depends(get_route_optimization_service),
):
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
            detail=f"Erro na otimização: {str(e)}",
        )


@app.get("/")
async def root():
    return {
        "message": "API TSP Genetic Algorithm está rodando. Acesse /docs para a documentação interativa."
    }
