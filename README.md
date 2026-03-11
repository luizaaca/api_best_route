# TSP Genetic Algorithm API

Esta API utiliza um Algoritmo Genético para otimizar rotas entre um ponto de origem e múltiplos destinos, considerando prioridades e estimativas de tempo de chegada (ETA) baseadas em dados do OpenStreetMap. A solução agora é distribuída entre `n` veículos, retornando explicitamente a rota de cada veículo e os totais agregados da frota.

A população inicial do algoritmo deixou de ser puramente aleatória: ela agora é gerada por uma estratégia híbrida que combina sementes heurísticas e indivíduos aleatórios. As sementes heurísticas usam `k-means` sobre as coordenadas projetadas (`RouteNode.coords`) para separar destinos por veículo e, em seguida, ordenam os pontos de cada cluster com heurísticas espaciais como nearest-neighbor e convex hull quando o formato do cluster justificar esse refinamento.

O código está organizado em pacotes sob `src/` (domínio, aplicação, infraestrutura), com a API em `api/` e uma entrada de console em `console/`. O algoritmo genético contém seus operadores internamente e aceita injeção de um plotter opcional para visualização.

## Instalação

1. Navegue até o diretório `api_best_route`:
   ```
   cd api_best_route
   ```

2. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```

## Executando a API

Execute o servidor com Uvicorn:
```
uvicorn api.main:app --reload
```

A API estará disponível em `http://127.0.0.1:8000`. Acesse `http://127.0.0.1:8000/docs` para a documentação interativa do Swagger.

## Executando o Console

O console é um ponto de entrada alternativo à API, útil para execuções locais e depuração:
```
python -m console.main
```

O script em `console/main.py` demonstra a injeção de dependências: é possível passar um `MatplotlibPlotter` via `optimizer_factory` para visualizar a evolução da melhor solução geração a geração. Edite o arquivo para configurar origem, destinos, número de veículos e parâmetros do algoritmo.

## Inicialização da população

O `TSPGeneticAlgorithm` agora inicializa a população em modo híbrido:

- uma fração da população nasce de sementes heurísticas baseadas em agrupamento espacial por veículo;
- a fração restante continua sendo gerada aleatoriamente para preservar diversidade genética.

O fluxo heurístico atual é:

1. separar a origem dos destinos;
2. aplicar `k-means` sobre `RouteNode.coords`, que já estão em coordenadas projetadas do grafo;
3. gerar um cluster por veículo, permitindo clusters vazios quando há mais veículos do que destinos;
4. ordenar os destinos de cada cluster com nearest-neighbor;
5. aplicar convex hull apenas em clusters maiores e geometricamente mais espalhados;
6. perturbar parte das sementes heurísticas com pequenas trocas locais para aumentar a diversidade inicial.

Essa estratégia acelera a busca inicial por boas soluções sem remover a capacidade exploratória do algoritmo genético.

## Endpoint

### POST /optimize_route

Otimiza a rota usando o algoritmo genético.

#### Parâmetros de Entrada (JSON)
- `origin` (string): Ponto de origem, como "Praça da Sé, São Paulo".
- `destinations` (array): Lista de destinos, cada um com:
  - `location` (string ou array): Nome do lugar (ex: "Edifício Copan, São Paulo") ou coordenadas [latitude, longitude].
  - `priority` (integer): Prioridade do destino (ex: 1 para alta prioridade).
- `max_generation` (integer, opcional): Número máximo de gerações (padrão: 50).
- `max_processing_time` (integer, opcional): Tempo máximo de processamento em milissegundos (padrão: 10000).
- `population_size` (integer, opcional): Tamanho da população inicial do algoritmo genético (padrão: 10).
- `vehicle_count` (integer, opcional): Número de veículos disponíveis para distribuir os destinos (padrão: 1).

#### Exemplo de Requisição
```json
{
  "origin": "Praça da Sé, São Paulo",
  "destinations": [
    {"location": "Edifício Copan, São Paulo", "priority": 1},
    {"location": "Mercado Municipal de São Paulo", "priority": 2},
    {"location": [-23.5465, -46.6367], "priority": 3}
  ],
  "max_generation": 50,
  "max_processing_time": 10000,
  "population_size": 20,
  "vehicle_count": 2
}
```

#### Resposta (JSON)
- `routes_by_vehicle` (array): Lista de veículos com sua rota otimizada, `vehicle_id` explícito e totais do veículo.
  - `route[0]`: sempre representa a origem do veículo.
  - `route[1:]`: destinos atribuídos ao veículo, na ordem otimizada.
- `totals` (objeto): Totais agregados da solução inteira.
- `best_fitness` (float): Valor do fitness da melhor rota (custo total).
- `population_size` (integer): Tamanho da população usada.
- `generations_run` (integer): Número de gerações executadas (aproximado).

#### Exemplo de Resposta
```json
{
  "routes_by_vehicle": [
    {
      "vehicle_id": 1,
      "route": [
        {
          "location": "Praça da Sé, São Paulo",
          "coords": [-23.5501, -46.6339],
          "length": 0.0,
          "eta": 0.0,
          "cost": 0.0,
          "path": []
        },
        {
          "location": "Edifício Copan, São Paulo",
          "coords": [-23.5489, -46.6388],
          "length": 1520.5,
          "eta": 420.0,
          "cost": 420.0,
          "path": [[-23.5501, -46.6339], [-23.5489, -46.6388]]
        }
      ],
      "totals": {
        "total_length": 1520.5,
        "total_eta": 420.0,
        "total_cost": 420.0
      }
    },
    {
      "vehicle_id": 2,
      "route": [
        {
          "location": "Praça da Sé, São Paulo",
          "coords": [-23.5501, -46.6339],
          "length": 0.0,
          "eta": 0.0,
          "cost": 0.0,
          "path": []
        },
        {
          "location": "Mercado Municipal de São Paulo",
          "coords": [-23.5416, -46.6291],
          "length": 980.2,
          "eta": 315.0,
          "cost": 378.0,
          "path": [[-23.5501, -46.6339], [-23.5416, -46.6291]]
        }
      ],
      "totals": {
        "total_length": 980.2,
        "total_eta": 315.0,
        "total_cost": 378.0
      }
    }
  ],
  "totals": {
    "total_length": 2500.7,
    "total_eta": 735.0,
    "total_cost": 798.0
  },
  "best_fitness": 798.0,
  "population_size": 20,
  "generations_run": 37
}
```

Veículos sem entregas continuam presentes na resposta com `vehicle_id`, rota contendo apenas o segmento nulo da origem e totais zerados:

```json
{
  "vehicle_id": 3,
  "route": [
    {
      "location": "Praça da Sé, São Paulo",
      "coords": [-23.5501, -46.6339],
      "length": 0.0,
      "eta": 0.0,
      "cost": 0.0,
      "path": []
    }
  ],
  "totals": {
    "total_length": 0.0,
    "total_eta": 0.0,
    "total_cost": 0.0
  }
}
```

## Notas
- O algoritmo considera prioridades ao calcular o fitness da rota.
- O fitness da solução é calculado a partir dos totais agregados de todos os veículos.
- O primeiro item de cada `route` é sempre a origem, mesmo quando o veículo também possui destinos atribuídos.
- A população pode distribuir zero destinos para um veículo quando isso fizer parte de uma solução candidata; nesse caso o veículo permanece apenas com a origem.
- O agrupamento espacial usa `RouteNode.coords` em coordenadas projetadas do grafo, e não latitude/longitude brutas.
- A inicialização híbrida combina indivíduos heurísticos e aleatórios para equilibrar qualidade inicial e diversidade da população.
- Certifique-se de que as localizações sejam válidas e acessíveis via OpenStreetMap.
- O tempo de processamento pode variar dependendo do número de destinos e parâmetros.

## Dependências
- FastAPI: framework para construção da API.
- Uvicorn: servidor ASGI para execução da aplicação.
- NumPy: pacote numérico usado na seleção de pais no algoritmo genético.
- NetworkX: estrutura de grafos utilizada para roteamento e cálculo de distâncias.
- OSMnx: construção e projeção de grafos de ruas a partir de OpenStreetMap.
- geopy: geocodificação e reverso-geocodificação de coordenadas, usado pelo `OSMnxGraphGenerator` para nomear pontos.
- scikit-learn: implementação do `KMeans` usada para agrupar destinos por veículo durante a geração heurística da população inicial.
- Shapely e PyProj: manipulação de geometrias e transformação entre CRS.
- Matplotlib: dependência opcional para implementações de `IPlotter`.

O arquivo `requirements.txt` contém todas as dependências necessárias e pode ser instalado com `pip install -r requirements.txt`.

## Configuração

### Cache do OSMnx

O `OSMnxGraphGenerator` aceita um parâmetro `cache_folder` que define onde os dados baixados do OpenStreetMap serão armazenados em disco. Isso evita requisições repetidas à API do OSM durante o desenvolvimento.

O valor é resolvido na seguinte ordem de precedência:
1. Parâmetro `cache_folder` passado explicitamente ao construtor.
2. Variável de ambiente `OSMNX_CACHE_FOLDER`.
3. Valor padrão: `"cache"` (diretório relativo à raiz do projeto).

Exemplo via variável de ambiente:
```bash
export OSMNX_CACHE_FOLDER=/tmp/osmnx_cache
uvicorn api.main:app --reload
```

Exemplo via parâmetro (em `api/dependencies.py` ou `console/main.py`):
```python
OSMnxGraphGenerator(cache_folder="/tmp/osmnx_cache")
```
