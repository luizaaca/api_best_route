from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    Destination,
    RouteItem,
    RouteTotals,
    OptimizeRouteRequest,
    OptimizeRouteResponse,
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
        destinations_formatted = [
            (dest.location, dest.priority) for dest in request.destinations
        ]

        result = service.optimize(
            origin=request.origin,
            destinations=destinations_formatted,
            max_generation=request.max_generation,
            max_processing_time=request.max_processing_time,
        )

        best_route = []
        for node in result.best_route.segments:
            location = node["name"]
            coords = list(node["coords"])
            path = node["path"]
            length = node["length"]
            eta = node["eta"]
            cost = node.get("cost")
            best_route.append(
                RouteItem(
                    location=location,
                    coords=coords,
                    length=length,
                    path=path,
                    eta=eta,
                    cost=cost,
                )
            )

        totals = RouteTotals(
            total_length=result.best_route.total_length,
            total_eta=result.best_route.total_eta,
            total_cost=result.best_route.total_cost,
        )

        return OptimizeRouteResponse(
            best_route=best_route,
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
