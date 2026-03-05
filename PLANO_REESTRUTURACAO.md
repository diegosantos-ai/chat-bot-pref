Transformar um projeto interno em um produto SaaS "white-label" (uma casca personalizável) exige separar a lógica de negócio dos dados específicos do cliente. Como o código já é estruturado e modular, esse processo será bem direto.

Aqui está o mapa de execução, passo a passo, saindo do código até a estruturação da máquina de vendas pela Nexo Basis.

Fase 1: A Desvinculação (O White-Label)
O objetivo aqui é garantir que não exista a palavra "{bot_name}" ou "{client_name}" chumbada em nenhum lugar do código.

Varrer e Parametrizar Prompts: Localize todos os system prompts e substitua os nomes fixos por variáveis. Em vez de "Você é a {bot_name}, assistente de {client_name}", o prompt deve ser montado dinamicamente: "Você é {bot_name}, assistente virtual da {client_name}".

Abstração do Disclaimer: O disclaimer obrigatório ("Informações baseadas na base oficial...") já é excelente. Transforme-o em uma variável de ambiente ou configuração no banco de dados, permitindo que cada prefeitura ajuste o texto final conforme a exigência do próprio departamento jurídico.

Isolamento de Credenciais (Meta): O seu sistema já separa credenciais por plataforma (Instagram/Facebook). Agora, ele precisa aceitar um array ou tabela de credenciais. A API precisa identificar de qual página do Facebook o webhook está vindo para rotear para o cliente correto.

Fase 2: Arquitetura Multi-Tenant (O Motor)
Para rodar várias prefeituras no mesmo servidor sem misturar dados (vital para LGPD e compliance governamental).

Isolamento no PostgreSQL: Atualize seu schema. Toda tabela (logs de chat, auditoria, analitics) precisa ter uma coluna tenant_id. Para garantir segurança máxima na camada de dados, ative o Row-Level Security (RLS) do PostgreSQL, filtrando automaticamente as queries pelo tenant_id da requisição.

Segregação do RAG no ChromaDB: Cada cliente deve ter sua própria coleção (Collection) dentro do ChromaDB. Quando a requisição chegar na API, o Retriever deve buscar o contexto apenas na coleção vinculada ao tenant_id daquela prefeitura.

Injeção de Dependência no FastAPI: Crie um middleware ou dependência no FastAPI que intercepte a requisição (seja via header da API ou payload do webhook da Meta), identifique o tenant_id, e passe esse contexto para os serviços de RAG e Banco de Dados. Mantenha os type hints rigorosos aqui para evitar vazamento de contexto entre clientes.

Fase 3: Operação e Onboarding
Quando uma nova prefeitura assinar o contrato, o setup precisa ser rápido.

Pipeline de Ingestão Padronizado: O seu script de ingestão atual (app.rag.ingest) deve aceitar o tenant_id como parâmetro. O pipeline lerá o Diário Oficial ou base de conhecimento do cliente novo e populará a coleção correta no ChromaDB, guardando o metadado da fonte.

Dashboard de Configuração (Opcional no início): Antes de criar um front-end complexo, você pode gerenciar os clientes (cadastrar tokens do Meta, definir bot_name) diretamente via scripts SQL ou uma interface administrativa simples no n8n conectada ao PostgreSQL.

Fase 4: O "Showroom" e Go-To-Market
Governos não compram ideias, compram soluções que conseguem ver funcionando.

O Bot de Demonstração: Crie a "Prefeitura de Nova Esperança" (um tenant fictício no seu banco). Alimente o RAG com leis e FAQs genéricos. Conecte isso a uma página de Instagram e Facebook de teste.

Pacote de Compliance: Reúna a sua documentação atual (Fase 3.1: Protocolos de Crise, Fase 5.3: Anonimização e LGPD). Isso formará o seu PDF comercial. Secretários de Administração compram segurança jurídica; o fato de a IA não tomar decisões legais e blindar dados pessoais é o seu maior trunfo.

Estratégia de Dispensa de Licitação: Formate o preço (Setup de Implantação + Mensalidade de Manutenção/Cloud) para que o valor anual fique abaixo do teto de dispensa de licitação vigente (Art. 75 da Nova Lei de Licitações). Isso reduz o ciclo de vendas de meses para semanas.

Fase 5: A Máquina de Vendas
Mapeamento de Leads com Automação: Crie workflows no n8n que façam scraping ou consumam APIs de Diários Oficiais e Portais da Transparência da sua região. Busque por termos como "modernização administrativa", "déficit de atendimento" ou prefeituras que lançaram novos portais.

Outreach Direto: Com a lista em mãos, aborde Secretários de TI, Administração ou Comunicação. A mensagem deve ser direta: "Vi que a prefeitura está modernizando o atendimento. Desenvolvemos um chatbot com IA que se conecta à base de leis do município e zera a fila de dúvidas no Instagram em 24h, sem risco jurídico e via dispensa de licitação. Quer testar nossa demonstração?"