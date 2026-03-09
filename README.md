# TSP Genetic Algorithm API

Esta API utiliza um Algoritmo Genético para otimizar rotas entre um ponto de origem e múltiplos destinos, considerando prioridades e estimativas de tempo de chegada (ETA) baseadas em dados do OpenStreetMap.

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

O script em `console/main.py` demonstra a injeção de dependências: é possível passar um `MatplotlibPlotter` via `optimizer_factory` para visualizar a evolução da rota geração a geração. Edite o arquivo para configurar origem, destinos e parâmetros do algoritmo.

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
  "max_processing_time": 10000
}
```

#### Resposta (JSON)
- `best_route` (array): Lista das localizações na ordem otimizada.
- `best_fitness` (float): Valor do fitness da melhor rota (custo total).
- `population_size` (integer): Tamanho da população usada.
- `generations_run` (integer): Número de gerações executadas (aproximado).

#### Exemplo de Resposta
```json
{
  "best_route": [
    "Praça da Sé, São Paulo",
    "Edifício Copan, São Paulo",
    "Mercado Municipal de São Paulo",
    [-23.5465, -46.6367]
  ],
  "best_fitness": 1234.56,
  "population_size": 10,
  "generations_run": 50
}
```

## Notas
- O algoritmo considera prioridades ao calcular o fitness da rota.
- Certifique-se de que as localizações sejam válidas e acessíveis via OpenStreetMap.
- O tempo de processamento pode variar dependendo do número de destinos e parâmetros.

## Dependências
- FastAPI: framework para construção da API.
- Uvicorn: servidor ASGI para execução da aplicação.
- NumPy: pacote numérico usado na seleção de pais no algoritmo genético.
- NetworkX: estrutura de grafos utilizada para roteamento e cálculo de distâncias.
- OSMnx: construção e projeção de grafos de ruas a partir de OpenStreetMap.
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
