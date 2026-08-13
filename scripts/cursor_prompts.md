# 🤖 Prompts Prontos para o Cursor
# Cole cada bloco diretamente no Chat ou Composer do Cursor IDE

---

## PROMPT 1 — Setup inicial completo (Composer, Ctrl+I)

```
Preciso configurar o projeto "Centro de Comando Familiar" do zero.
Leia o .cursorrules e analise todos os arquivos existentes em:
- app.py
- modules/financeiro.py
- modules/administrativo.py
- modules/familiar.py
- config.py

Depois:
1. Verifique se há algum import faltando nos módulos
2. Garanta que todos os blueprints estão registrados no app.py
3. Adicione um endpoint GET /dashboard que retorna dados agregados
   de todas as tabelas para alimentar o frontend
4. Certifique que o Dockerfile está otimizado para produção
Faça todas as alterações necessárias.
```

---

## PROMPT 2 — Testar todas as rotas localmente (Chat)

```
Gere um arquivo tests/test_all_routes.py completo com:
- Testes para TODAS as rotas do projeto (use o endpoint /rotas para listá-las)
- Mock do Airtable (não fazer chamadas reais)
- Mock da API Anthropic (não gastar créditos)
- Mock do QR Code (sem PIL real)
- Fixtures reutilizáveis para dados de teste
- Cobertura mínima de: sucesso, erro de auth, payload inválido
Use pytest e pytest-mock. Inclua conftest.py separado.
```

---

## PROMPT 3 — Adicionar nova funcionalidade (Composer)

```
Adicione ao módulo familiar um sistema de "Missão Especial Semanal":
- Nova tabela Airtable: Missoes_Especiais (campos: Titulo, Descricao_Detalhada,
  Pontos_Bonus, Data_Inicio, Data_Fim, Status, Membros_Participantes, Premio_Final)
- Rota POST /familiar/criar-missao — cria missão com IA gerando descrição lúdica
- Rota GET /familiar/missao-ativa — retorna missão da semana com progresso
- Rota POST /familiar/concluir-missao — finaliza e distribui XP bônus
- Integra com o briefing diário (adiciona status da missão na mensagem)
Siga estritamente os padrões do .cursorrules.
```

---

## PROMPT 4 — Debug de erro específico (Chat)

```
Estou recebendo este erro ao chamar /financeiro/extrair-fatura:
[COLE O ERRO AQUI]

Analise:
1. O módulo modules/financeiro.py
2. A config de autenticação em config.py
3. O payload que está sendo enviado
Identifique a causa raiz e corrija sem quebrar os outros endpoints.
```

---

## PROMPT 5 — Otimizar para produção (Composer)

```
Prepare o projeto para deploy em produção no Railway:
1. Adicione rate limiting real (flask-limiter) nas rotas mais pesadas
2. Adicione health check que testa conexão com Airtable e retorna latência
3. Adicione endpoint /metrics com: total de faturas, emails processados hoje, XP total família
4. Configure logging estruturado em JSON para o Railway consumir
5. Adicione CORS configurável via variável de ambiente ALLOWED_ORIGINS
6. Crie railway.toml com as configurações de deploy
Não altere a lógica de negócio existente.
```

---

## PROMPT 6 — Gerar documentação automática (Chat)

```
Gere um arquivo docs/API.md com documentação completa de todas as rotas:
- Liste todas as rotas usando app.url_map
- Para cada rota: método, URL, headers obrigatórios, body de exemplo,
  resposta de sucesso e resposta de erro
- Adicione exemplos de curl para cada rota
- Adicione uma seção de configuração das variáveis de ambiente
- Formato: Markdown bem estruturado, pronto para GitHub
```

---

## PROMPT 7 — Criar novo workflow n8n via código (Chat)

```
Preciso de um 5º workflow n8n em JSON chamado:
"🔔 Fluxo 5 — Confirmação de Pagamento via WhatsApp"

Lógica:
- Trigger: Webhook do n8n (URL pública que o usuário envia mensagem)
- Quando adulto responde "PAGO [nome da fatura]" no WhatsApp
- n8n chama GET /financeiro/fluxo-de-caixa para buscar fatura pelo nome
- Se encontrar: chama PATCH /financeiro/marcar-pago/{id}
- Responde no WhatsApp: confirmação com saldo atualizado
- Se não encontrar: responde listando as faturas pendentes

Siga o padrão dos outros 4 workflows em n8n-workflows/.
```

---

## PROMPT 8 — MCP Airtable no Cursor (Chat)

```
Quero configurar o MCP do Airtable no Cursor para que você veja
meu schema em tempo real.

1. Mostre o conteúdo exato do arquivo ~/.cursor/mcp.json que devo criar
2. Confirme os nomes exatos das tabelas do projeto
3. Depois que eu configurar, gere uma rota /financeiro/dashboard-mensal
   que usa os campos EXATOS do Airtable sem eu precisar especificar
```
