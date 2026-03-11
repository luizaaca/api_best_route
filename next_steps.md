# 1. Criar matrix de adjacência [X]
- criar função para calcular distâncias entre os pontos usando a API do networkx com `eta, segment = nx.single_source_dijkstra(grafo, origem, destino, funcao_custo_eta)` e construir a matrix de adjacência a partir das distâncias calculadas, aplicando os modificadores de prioridade e horário conforme necessário.

# 2. Adicionar mais de um veículo [X]
- criar função para otimizar rotas para múltiplos veículos
- dividir os destinos entre 0/1 e 0,5/0,5 aleatoriamente entre os veículos
- aplicar a função de fitness para cada um e somar os custos para obter o custo total da solução

# 3. Aplicar heurísticas de inicialização [X]
- implementar heurísticas como Nearest Neighbor, K-means e Convex Hull para gerar soluções iniciais mais próximas do ótimo, melhorando a eficiência do algoritmo genético e a qualidade das soluções geradas, em comparação com a geração aleatória de soluções iniciais.

# 3.1 Permitir uso de distância/custo da rede em vez de distância Euclidiana
- permitir que a ordenação intra-cluster das heurísticas use o custo real da rede (por exemplo, tempo estimado de viagem) em vez da distância Euclidiana projetada, para gerar rotas mais realistas e eficientes desde a fase de inicialização.
- parametrizar a função de custo usada na ordenação intra-cluster, permitindo escolher entre distância Euclidiana e custo de rede, para avaliar o impacto dessa escolha na qualidade das soluções geradas.

# 4. Corrigir somatório final de tempo da frota [X]
- remover o cálculo do tempo total da frota e substituir por tempos mínimo e maximo, pois são vários veículos.

# 4.1 Parametrizar função de peso e custo [X]
- expor `weight_type` e `cost_type` no contrato da API/console, com resolução por string na infraestrutura. Atualmente `weight_type="eta"` e `cost_type="priority"`.

# 4.2 Desacoplar construção da matrix do GA [X]
- remover do `TSPGeneticAlgorithm` a responsabilidade de montar a matrix de adjacência. A matrix passa a ser construída na composição da infraestrutura e injetada no otimizador.

# 5. Estudar mudanças na seleção dos pais
- implementar seleção por torneio, onde um grupo de indivíduos é selecionado aleatoriamente e o melhor entre eles é escolhido como pai, para aumentar a pressão seletiva e melhorar a qualidade das soluções geradas, em comparação com a seleção por roleta.
- estruturar a seleção como estratégia configurável, permitindo comparar roleta, torneio e futuras abordagens sem alterar o fluxo principal do GA.

# 5.1 Estudar novas estratégias de cruzamento
- implementar novas estratégias de cruzamento além do order crossover atual do cenário multi-veículo, permitindo comparar abordagens mais conservadoras ou mais exploratórias para redistribuição de destinos entre veículos.

# 6. Melhorar mutação
- implementar mutação de swap com intensidade aleatória, onde dois destinos são trocados de posição na rota, além da mutação de inversão já existente, para aumentar a diversidade das soluções geradas e evitar convergência prematura.
- permitir múltiplas estratégias de mutação configuráveis, com seleção por parâmetro para facilitar benchmark e experimentação.

# 7. Permitir injeção de plotter [X]
- criar função para injetar um plotter personalizado, permitindo a visualização das rotas geradas de forma mais flexível e adaptada às necessidades do usuário, em vez de depender de uma implementação fixa. O método 'plot' deverá receber uma instancia do objeto `RouteSegmentsInfo`. Usar uma interface.

# 8. Verificar aquisição de nomes de locais [X]
- a função de busca de locais é bidirecional e deve encontrar coordenadas para nomes e nomes para coordenadas, usando a API do Nominatim. Verificar se a função está funcionando corretamente.

# 8.1 Cache persistente de geocoding
- cachear persistentemente a recuperação de nomes e coordenadas de ruas (geocoding direto e reverso), evitando recomputação e chamadas externas repetidas entre execuções.

# 8.2 Cache de matriz de adjacência
- implementar cache específico para a matriz de adjacência, evitando reconstrução completa a cada requisição e melhorando a performance do serviço, especialmente para rotas com destinos recorrentes.

# 9. Melhorar testes unitários
- criar testes unitários para as funções principais do código, como a função de cálculo de distância.

# 9.1 Criar modo benchmark/lab
- adicionar um modo de benchmark que execute duas rodadas comparativas, uma sem heurísticas e outra com heurísticas, com resultado exibido apenas no console.
- esse modo deve ser habilitado por algum parâmetro explícito de laboratório, por exemplo `lab_mode`, para não interferir no fluxo normal da API/console.

# 10. Verificar possibilidade de capacidade de veículos e lista de entregas
- implementar lógica para considerar a capacidade dos veículos e a lista de entregas, garantindo que as rotas geradas sejam viáveis em termos de carga e demanda, e que os veículos não sejam sobrecarregados.