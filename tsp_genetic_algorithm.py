import random
import time
import traceback
import numpy as np
from genetic_algorithm_utils import (
    mutate,
    order_crossover,
    generate_random_population,
)
from osmnx_graph_utils import convert_from_UTM_to_lat_lon, initialize_graph
from route_calculator_utils import IRouteCalculator


class TSPGeneticAlgorithm:
    """
    Classe que implementa um Algoritmo Genético para resolver o Problema do Caixeiro Viajante (TSP)
    usando um grafo de ruas obtido via OpenStreetMap. O algoritmo otimiza a rota considerando
    prioridades dos destinos.
    """

    def __init__(
        self,
        route_calculator: IRouteCalculator,
        population_size=10,
        mutation_probability=0.5,
    ):
        """
        Inicializa os parâmetros do algoritmo genético.

        :param route_calculator: Objeto que implementa a interface IRouteCalculator.
        :param population_size: Tamanho da população (número de indivíduos).
        :param mutation_probability: Probabilidade de mutação para cada filho gerado.
        """
        self.route_calculator = route_calculator
        self.population_size = population_size
        self.mutation_probability = mutation_probability

    def solve(self, route_nodes, max_generation=50, max_processing_time=10000):
        """
        Executa o algoritmo genético para encontrar a melhor rota.

        :param route_nodes: Lista de nós da rota (origin + destinos).
        :param max_generation: Número máximo de gerações a executar.
        :param max_processing_time: Tempo máximo de processamento em milissegundos.
        :return: Dicionário contendo a população ordenada por fitness, o melhor fitness e o melhor indivíduo.
        """
        # Cria a população inicial: permutações aleatórias dos nós da rota
        population = generate_random_population(route_nodes, self.population_size)

        # Usa o route_calculator passado na inicialização
        weight_function = self.route_calculator.get_weight_function()

        # Variáveis para rastrear o melhor resultado
        best_fitness = float("inf")
        best_individual = (None, None)  # (rota, RouteSegmentsInfo)
        generation = 0
        start_time = time.time() * 1000  # Tempo em ms

        while generation < max_generation:
            # Verifica se o tempo limite foi atingido
            current_time = time.time() * 1000
            if current_time - start_time > max_processing_time:
                print(
                    f"Tempo limite de {max_processing_time} ms atingido. Parando o algoritmo."
                )
                break

            generation += 1

            # Calcula o fitness para cada indivíduo na população
            # Fitness é baseado no custo total da rota, considerando prioridades
            population_calculated = [
                self.route_calculator.compute_route_segments_info(
                    individual, weight_function, "priority"
                )
                for individual in population
            ]

            # Ordena a população pelo custo total (fitness: menor custo é melhor)
            population, population_calculated = zip(
                *sorted(
                    zip(population, population_calculated),
                    key=lambda x: x[1].total_cost,
                )
            )
            population = list(population)
            population_calculated = list(population_calculated)

            # Atualiza o melhor fitness e indivíduo encontrado
            current_best_fitness = population_calculated[0].total_cost
            if current_best_fitness < best_fitness:
                best_fitness = current_best_fitness
                best_individual = (population[0], population_calculated[0])

            print(f"Geração {generation}: Melhor fitness = {best_fitness}")

            # Cria nova população com elitismo: mantém o melhor indivíduo
            new_population = [population[0]]  # Elitismo

            # Gera o resto da população através de seleção, crossover e mutação
            while len(new_population) < self.population_size:
                # Seleção proporcional ao fitness: indivíduos com menor custo têm maior probabilidade
                fitness_values = [ind.total_cost for ind in population_calculated]

                probability = 1 / np.array(fitness_values)
                parent1, parent2 = random.choices(
                    population, weights=probability.tolist(), k=2
                )

                # Crossover: Order Crossover
                child = order_crossover(parent1, parent2)

                # Mutação: Aplica mutação com probabilidade definida
                child = mutate(child, self.mutation_probability)

                new_population.append(child)

            # Atualiza a população para a próxima geração
            population = new_population

        def remove_duplicates(seq):
            seen = set()
            result = []
            for item in seq:
                if tuple(item) not in seen:
                    seen.add(tuple(item))
                    result.append(item)
            return result

        print("Recuperando CRS do grafo para conversão de coordenadas...")
        try:
            crs = self.route_calculator.get_graph_crs()
            print(f"CRS do grafo: {crs}")
        except Exception as e:
            # exibir erro completo com stack trace
            print(f"Erro ao obter CRS do grafo: {e}")
            traceback.print_exc()
            crs = None
        best_route = best_individual[1]
        # converter todos as coordenadas dos segmentos para lat/lon usando o metodo convert_from_UTM_to_lat_lon
        for segment in best_route.segments:
            segment["coords"] = convert_from_UTM_to_lat_lon(
                segment["coords"][0], segment["coords"][1], crs
            )
            segment["path"] = [
                convert_from_UTM_to_lat_lon(x, y, crs)
                for x, y in remove_duplicates(segment["path"])
            ]

        # print os nomes dos destinos na ordem da melhor rota encontrada
        print(
            "Melhor rota encontrada: ",
            " -> ".join([segment["name"] for segment in best_route.segments]),
        )

        # Retorna os resultados
        return {
            "population": population,  # População final ordenada
            "best_fitness": best_fitness,  # Melhor fitness encontrado
            "best_individual": best_route,  # Melhor indivíduo (rota)
        }
