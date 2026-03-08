from route_calculator_utils import RouteCalculator
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Union, Optional
import sys
import os
from osmnx_graph_utils import initialize_graph
from tsp_genetic_algorithm import TSPGeneticAlgorithm

app = FastAPI(
    title="TSP Genetic Algorithm API",
    description="API para otimização de rotas usando Algoritmo Genético, considerando prioridades e ETA via OpenStreetMap.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ou especifique ["http://localhost:5500"] por exemplo
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Destination(BaseModel):
    location: Union[str, List[float]]
    priority: int


class RouteItem(BaseModel):
    location: Union[str, List[float]]
    coords: List[float]
    length: float
    eta: float
    cost: Optional[float] = None
    path: List[List[float]]


class RouteTotals(BaseModel):
    total_length: float
    total_eta: float
    total_cost: Optional[float] = None


class OptimizeRouteRequest(BaseModel):
    origin: Union[str, List[float]]
    destinations: List[Destination]
    max_generation: int = 50
    max_processing_time: int = 10000


class OptimizeRouteResponse(BaseModel):
    best_route: List[RouteItem]
    totals: RouteTotals
    best_fitness: float
    population_size: int
    generations_run: int


@app.post("/optimize_route", response_model=OptimizeRouteResponse)
async def optimize_route(request: OptimizeRouteRequest):
    """
    Otimiza a rota entre o ponto de origem e os destinos usando Algoritmo Genético.

    - **origin**: Ponto de origem como string (ex: "Praça da Sé, São Paulo").
    - **destinations**: Lista de destinos, cada um com localização e prioridade.
    - **max_generation**: Número máximo de gerações (padrão: 50).
    - **max_processing_time**: Tempo máximo de processamento em ms (padrão: 10000).

    Retorna a melhor rota encontrada, o fitness e informações adicionais.
    """
    try:
        # Converte destinations para o formato esperado: lista de tuplas (location, priority)
        destinations_formatted = [
            (dest.location, dest.priority) for dest in request.destinations
        ]

        graph, route_nodes = initialize_graph(
            origin=request.origin,
            destinations=destinations_formatted,
        )

        # Instancia o RouteCalculator (supondo que ele esteja implementado e disponível)
        route_calculator = RouteCalculator(graph=graph)
        # Instancia o algoritmo genético
        ga = TSPGeneticAlgorithm(route_calculator=route_calculator)

        # Executa a otimização
        result = ga.solve(
            max_generation=request.max_generation,
            route_nodes=route_nodes,
            max_processing_time=request.max_processing_time,
        )

        # Extrai a melhor rota: inclui o origin seguido das locations dos destinos na ordem otimizada
        best_route = []
        for node in result["best_individual"].segments:
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
            total_length=result["best_individual"].total_length,
            total_eta=result["best_individual"].total_eta,
            total_cost=result["best_individual"].total_cost,
        )

        return OptimizeRouteResponse(
            best_route=best_route,
            totals=totals,
            best_fitness=result["best_fitness"],
            population_size=len(result["population"]),
            generations_run=request.max_generation,  # Aproximado, pois o algoritmo para quando atinge o limite
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
