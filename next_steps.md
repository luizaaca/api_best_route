# 1. Criar matrix de adjacência [X]
- criar função para calcular distâncias entre os pontos usando a API do networkx com `eta, segment = nx.single_source_dijkstra(grafo, origem, destino, funcao_custo_eta)` e construir a matrix de adjacência a partir das distâncias calculadas, aplicando os modificadores de prioridade e horário conforme necessário.

# 2. Adicionar mais de um veículo
- criar função para otimizar rotas para múltiplos veículos
- dividir os destinos entre 0,5/0,5 e 0,3/0,7 aleatoriamente entre os veículos
- aplicar a função de fitness para cada um e somar os custos para obter o custo total da solução

# 3. Estudar mudanças na seleção dos pais
- implementar seleção por torneio, onde um grupo de indivíduos é selecionado aleatoriamente e o melhor entre eles é escolhido como pai, para aumentar a pressão seletiva e melhorar a qualidade das soluções geradas, em comparação com a seleção por roleta.

# 4. Melhorar mutação
- implementar mutação de swap com intensidade aleatória, onde dois destinos são trocados de posição na rota, além da mutação de inversão já existente, para aumentar a diversidade das soluções geradas e evitar convergência prematura.

# 5. Permitir injeção de plotter [X]
- criar função para injetar um plotter personalizado, permitindo a visualização das rotas geradas de forma mais flexível e adaptada às necessidades do usuário, em vez de depender de uma implementação fixa. O método 'plot' deverá receber uma instancia do objeto `RouteSegmentsInfo`. Usar uma interface.

# 6. Verificar aquisição de nomes de locais
- a função de busca de locais é bidirecional e deve encontrar coordenadas para nomes e nomes para coordenadas, usando a API do Nominatim. Verificar se a função está funcionando corretamente.

# 7. Implementar testes unitários
- criar testes unitários para as funções principais do código, como a função de cálculo de distância.

# 8. Verificar possibilidade de capacidade de veículos e lista de entregas
- implementar lógica para considerar a capacidade dos veículos e a lista de entregas, garantindo que as rotas geradas sejam viáveis em termos de carga e demanda, e que os veículos não sejam sobrecarregados.