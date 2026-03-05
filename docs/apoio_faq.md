Abaixo está o conteúdo completo do seu documento "FAQ para TerezIA com RAG" reformatado em estrutura Markdown estilo arquivo `.md`. Você pode copiar e colar este texto para criar o seu arquivo.

``` markdown
# Relatório Técnico de Implementação e Governança da TerezIA: Arquitetura de Conhecimento, Protocolos Humanizados e Infraestrutura Computacional Soberana

## 1. Introdução e Contextualização Estratégica do Projeto Piloto

A implementação da **TerezIA**, o sistema de atendimento digital institucional do Município de Santa Tereza do Oeste (PR), transcende a simples adoção de uma ferramenta tecnológica; trata-se de um movimento estratégico de modernização administrativa regido por parâmetros contratuais e legislativos rigorosos. A análise detalhada do **Contrato nº 001/2026** estabelece que o sistema deve operar como um "projeto piloto controlado", com a finalidade precípua de ampliar o acesso à informação pública sem, contudo, substituir o juízo humano ou expandir a estrutura burocrática interna. Este relatório delineia a arquitetura técnica, semântica e operacional necessária para cumprir tais desígnios, mitigando riscos de responsabilidade civil e assegurando a conformidade com a Lei Geral de Proteção de Dados (LGPD).

O cenário atual da administração pública exige uma dualidade funcional: a eficiência da automação e a empatia do serviço público. O contrato estipula que a TerezIA não deve executar atos administrativos, registrar protocolos formais ou realizar decisões automatizadas, limitando-se a um escopo "estritamente informativo e institucional". Consequentemente, a construção da Base de Conhecimento (Knowledge Base - KB) para o sistema de *Retrieval-Augmented Generation* (RAG) não deve ser apenas um repositório de dados estáticos, mas uma estrutura dinâmica de triagem e roteamento qualificado. A inteligência artificial deve atuar como uma primeira linha de defesa contra a desinformação, guiando o cidadão para os canais oficiais competentes — sejam eles físicos, telefônicos ou digitais — garantindo que nenhuma solicitação complexa permaneça num limbo algorítmico.

A complexidade deste projeto reside na necessidade de harmonizar a "humanização" do atendimento — um requisito para a aceitação popular e a confiança no serviço — com a transparência algorítmica exigida por um ente estatal. A TerezIA deve ser, simultaneamente, acolhedora e explícita sobre sua natureza robótica, evitando a criação de "alucinações" ou falsas promessas de prazos, práticas expressamente vedadas pelo instrumento contratual. Para tal, este documento propõe uma infraestrutura baseada em Modelos de Linguagem Grande (LLMs) soberanos ou de código aberto, otimizados para o português brasileiro e para a realidade jurídica nacional, apoiados por bibliotecas de orquestração que impõem "guardrails" (barreiras de segurança) intransponíveis para temas sensíveis.

A seguir, apresenta-se o detalhamento da Engenharia da Base de Conhecimento, estruturada em clusters temáticos para otimizar a recuperação de informações via RAG, diferenciando as abordagens para interações públicas (comentários em redes sociais) e privadas (inbox/direct). Paralelamente, desenvolve-se uma análise técnica profunda sobre as ferramentas de IA generativa mais adequadas ao contexto orçamentário e regulatório de Santa Tereza do Oeste, culminando em um roteiro de governança que assegura a perenidade e a legalidade do projeto piloto.

## 2. Engenharia da Base de Conhecimento (Knowledge Base Engineering) para RAG

A eficácia de um sistema RAG depende diretamente da qualidade e da estruturação dos dados que o alimentam. No contexto da TerezIA, a base de conhecimento não é monolítica; ela é segmentada em "clusters" de intenção que refletem as competências das secretarias municipais. Esta segmentação permite que o vetor de busca recupere fragmentos (*chunks*) de informação com alta precisão semântica, reduzindo a latência e o custo computacional, além de minimizar o risco de o modelo confundir, por exemplo, prazos fiscais com prazos escolares.

A estruturação a seguir foi desenhada para responder às demandas mais frequentes dos cidadãos de Santa Tereza do Oeste, baseando-se em dados extraídos de portais oficiais, editais e da legislação municipal disponível.

### 2.1. Cluster A: Fundamentos Institucionais e Roteamento de Contatos

Este cluster constitui a espinha dorsal do sistema, resolvendo consultas de baixa complexidade e alto volume relacionadas à localização e funcionamento dos órgãos públicos. O contrato exige o fornecimento de "horários, contatos e localizações oficiais", o que demanda precisão absoluta para evitar o deslocamento desnecessário do cidadão.

A tabela abaixo consolida os dados fundamentais que devem ser "hard-coded" ou priorizados na recuperação vetorial:

| Dado Institucional | Informação Oficial | Fonte de Validação |
| :---: | :---: | :---: |
| **Telefone Geral (Paço)** | (45) 3124-1000 | 4 |
| **Endereço Sede** | Av. Paraná, 61 - Centro, CEP 85825-000 | 4 |
| **Horário de Atendimento** | Seg-Sex: 08h-12h e 13h-17h | 4 |
| **E-mail Oficial** | prefeitura@santatereza.pr.gov.br | 4 |
| **CNPJ** | 80.882.095/0001-53 | 1 |
| **Ouvidoria** | Canal para sugestões e reclamações | 4 |

#### FAQ Personalizado: Roteamento Institucional

**Intenção do Usuário:** Localizacao\_Prefeitura

*   **Contexto:** O cidadão pergunta onde fica a prefeitura ou qual o horário de funcionamento.
*   **Resposta Padrão (Inbox/Público):** "A sede administrativa da Prefeitura de Santa Tereza do Oeste está localizada na **Avenida Paraná, 61, no Centro**. O atendimento ao público ocorre de segunda a sexta-feira, das **08h às 12h** e das **13h às 17h** [4]. Caso precise de um departamento específico, como Saúde ou Tributação, posso fornecer o contato direto."

**Intenção do Usuário:** Contato\_Geral

*   **Contexto:** Busca por telefone ou e-mail sem especificar o setor.
*   **Resposta Padrão (Inbox/Público):** "O telefone geral do Paço Municipal é **(45) 3124-1000**. Você também pode enviar solicitações formais através do e-mail **prefeitura@santatereza.pr.gov.br** [4]. Lembro que, para protocolos oficiais, o ideal é utilizar o sistema de Protocolo Online no nosso site."

**Intenção do Usuário:** Lista\_Telefones\_Secretarias

*   **Contexto:** O cidadão pede uma lista de ramais. O sistema deve evitar listar todos de uma vez para não poluir a tela (especialmente no Instagram), mas sim perguntar qual setor é desejado.
*   **Resposta Padrão (Inbox):** "Possuímos uma lista de contatos para Saúde, Educação, Assistência Social, entre outros. Qual secretaria você deseja contatar? Posso te passar o número direto e o endereço." [6]

### 2.2. Cluster B: Educação, Matrículas e Transporte Escolar

A área de educação apresenta sazonalidade crítica e alta sensibilidade, envolvendo prazos legais que, se perdidos, podem gerar litígios. A TerezIA deve ser capaz de informar com exatidão as datas de matrícula e as regras para transporte, diferenciando claramente as responsabilidades municipais das estaduais.

#### FAQ Personalizado: Ciclo Escolar e Matrículas 2026

**Intenção do Usuário:** Datas\_Matricula\_2026

*   **Contexto:** Pais buscando prazos para novas matrículas na rede municipal.
*   **Resposta Padrão (Inbox/Público):** "As novas matrículas para a Rede Municipal de Ensino (especialmente Infantil V) para o ano letivo de 2026 estão programadas para ocorrer entre **24 e 28 de novembro de 2025** [5]. É fundamental não perder este prazo para garantir a vaga na escola mais próxima."

**Intenção do Usuário:** Documentacao\_Escolar

*   **Contexto:** Quais documentos levar. A falha nesta informação gera retrabalho no atendimento presencial.
*   **Resposta Padrão (Inbox):** "Para efetivar a matrícula, é obrigatório comparecer à Secretaria de Educação levando **originais e cópias** dos seguintes documentos [5]:
    1. Certidão de Nascimento da criança;
    2. RG e CPF (da criança e dos pais/responsáveis);
    3. Cartão SUS e Carteira de Vacinação atualizada (com declaração);
    4. Comprovante de residência atualizado (últimos 3 meses);
    5. Comprovante do Bolsa Família (caso seja beneficiário).
    A Secretaria fica na Rua Internacional, nº 1597 – Centro, ao lado da Fisioterapia."

#### FAQ Personalizado: Transporte Universitário

Este é um tópico complexo. Embora existam programas estaduais como o "Cartão Transporte Universitário" [7], Santa Tereza do Oeste possui legislação e costumes locais específicos, muitas vezes custeando integralmente o transporte ou subsidiando associações [9]. A resposta deve ser cautelosa para não confundir regras estaduais com municipais.

**Intenção do Usuário:** Transporte\_Universitario\_Regras

*   **Contexto:** Estudante perguntando sobre ônibus para faculdade em Cascavel ou Foz.
*   **Resposta Padrão (Inbox):** "O transporte universitário em Santa Tereza do Oeste é regido por legislação municipal específica e editais anuais que definem as rotas e os subsídios. Historicamente, o município oferece suporte significativo aos acadêmicos [9]. Para confirmar o edital vigente para 2026 e realizar seu cadastro, recomendo entrar em contato diretamente com a Secretaria de Educação no (45) 3124-1000 ou acompanhar as publicações no Diário Oficial, pois as regras de contrapartida podem sofrer alterações."

### 2.3. Cluster C: Saúde Pública, Farmácia e Emergências

O cluster de saúde é onde o risco de responsabilidade civil é mais elevado. A distinção entre "serviço administrativo" e "emergência médica" deve ser absoluta. O chatbot deve ser programado para detectar palavras-chave de risco e acionar protocolos de interrupção imediata.

| Unidade | Horário de Funcionamento | Observação |
| :---: | :---: | :---: |
| **Farmácia Básica I** | 13h às 19h | 11 |
| **Farmácia Básica II** | 07h às 13h | 11 |
| **Farmácia Básica III** | 13h às 19h | 11 |
| **UBS/USF** | Seg-Sex (Horário Comercial) | Fechadas em feriados [12] |
| **UPA/Pronto Atendimento** | 24 horas | Atendimento ininterrupto [12] |

#### FAQ Personalizado: Serviços de Saúde

**Intenção do Usuário:** Horario\_Farmacia

*   **Contexto:** Cidadão precisa retirar medicamentos.
*   **Resposta Padrão (Inbox/Público):** "As Farmácias Básicas do município operam em horários escalonados para melhor atender a população: a **Farmácia Básica II** atende das 07h às 13h, enquanto as **Farmácias Básicas I e III** funcionam das 13h às 19h [11]. Lembre-se de levar seu cartão SUS, documento com foto e a receita médica atualizada."

**Intenção do Usuário:** Dengue\_Boletim

*   **Contexto:** Informações sobre surtos ou sintomas.
*   **Resposta Padrão (Inbox):** "A Secretaria de Saúde divulga periodicamente os Boletins da Dengue e o Plano Municipal de Saúde 2022-2025 para transparência [4]. Para denúncias de focos de mosquito ou agendamento de visitas, contate a Vigilância Epidemiológica pelo telefone (45) 3124-1000."

**Intenção do Usuário:** Emergencia\_Medica (Protocolo Crítico)

*   **Contexto:** Palavras-chave como "dor no peito", "acidente", "sangramento", "infarto".
*   **Resposta Automática (Interrupção de Fluxo):** "⚠️ **ATENÇÃO:** Eu sou uma inteligência artificial e não posso prestar socorro médico. Se você ou alguém próximo está em situação de emergência, **ligue imediatamente para o SAMU (192) ou SIATE (193)**. Para emergências policiais, disque **190** [13]. Não aguarde resposta por aqui."

### 2.4. Cluster D: Gestão Fiscal, Tributos e REFIS

A arrecadação municipal depende da clareza nas informações sobre tributos. O sistema deve promover ativamente o programa de recuperação fiscal (REFIS) quando questionado sobre dívidas, atuando como um facilitador da regularização tributária.

#### FAQ Personalizado: IPTU e Recuperação Fiscal

**Intenção do Usuário:** REFIS\_Informacao

*   **Contexto:** Contribuinte quer saber como pagar dívidas atrasadas.
*   **Resposta Padrão (Inbox):** "A Prefeitura instituiu o **REFIS 2025** (Lei nº 2433/2025), que permite a regularização de débitos inscritos em Dívida Ativa até 31/12/2024, como IPTU, ISS e Taxas de Lixo [15]. O programa oferece descontos em juros e multas, além de parcelamento facilitado. É uma excelente oportunidade para ficar em dia com o município."

**Intenção do Usuário:** Como\_Aderir\_REFIS

*   **Contexto:** Onde ir para negociar.
*   **Resposta Padrão (Inbox):** "Para aderir ao REFIS, é necessário comparecer presencialmente ao **Setor de Tributação** na Prefeitura (Av. Paraná, 61), de segunda a sexta, das 08h às 12h ou das 13h às 17h. Não é possível realizar a negociação final pelas redes sociais devido ao sigilo fiscal."

**Intenção do Usuário:** Emissao\_IPTU

*   **Contexto:** Segunda via de boleto.
*   **Resposta Padrão (Inbox):** "Você pode emitir a guia do IPTU 2026 e a Certidão Negativa de Débitos diretamente pelo **Portal do Contribuinte** no nosso site oficial [4]. Basta acessar a área 'Tributos' e ter em mãos o número do cadastro imobiliário ou CPF/CNPJ."

### 2.5. Cluster E: Serviços Urbanos, Emprego e Assistência Social

Este cluster abrange serviços essenciais do cotidiano, como coleta de lixo, vagas de emprego e apoio social. A precisão aqui evita reclamações na Ouvidoria.

#### FAQ Personalizado: Serviços ao Cidadão

**Intenção do Usuário:** Coleta\_Lixo

*   **Contexto:** Dias de coleta nos bairros.
*   **Resposta Padrão (Inbox):** "A coleta de lixo em Santa Tereza do Oeste segue um cronograma setorizado. Geralmente, a coleta orgânica e seletiva ocorre em dias alternados conforme o bairro [17]. Para saber o dia exato da sua rua, consulte a Secretaria de Meio Ambiente ou a tabela no site oficial. Lembre-se de colocar o lixo ensacado próximo ao horário de passagem para evitar sujeira nas vias."

**Intenção do Usuário:** Agencia\_Trabalhador\_Vagas

*   **Contexto:** Busca por emprego.
*   **Resposta Padrão (Inbox):** "A Agência do Trabalhador atualiza as vagas semanalmente. O atendimento presencial ocorre na Rua Paraná (anexo à Prefeitura) ou na Rua Xavier da Silva, dependendo do serviço específico. O horário é das 07h30 às 13h30 ou horário comercial padrão [18]. Recomendamos levar Carteira de Trabalho e currículo atualizado. Você também pode verificar vagas pelo aplicativo Sine Fácil."

**Intenção do Usuário:** Contato\_CRAS

*   **Contexto:** Busca por auxílio social ou Cadastro Único.
*   **Resposta Padrão (Inbox):** "O Centro de Referência de Assistência Social (CRAS) está localizado na **Rua Governador Roberto Silveira, 829**. O telefone de contato é **(45) 3124-1075** [19]. Lá você pode tratar de Cadastro Único, Bolsa Família e outros programas sociais."

## 3. Arquitetura de Diálogo: Estratégias para Inbox vs. Público

A distinção entre o atendimento público (comentários em posts) e privado (Direct/Messenger) é vital para a proteção de dados (LGPD) e para a eficiência do fluxo conversacional. O contrato veda a exposição de dados sensíveis e a tomada de decisões públicas sobre casos individuais.

### 3.1. Estratégia para Atendimento Público (Comentários)

No ambiente público, a TerezIA deve atuar como um "balcão de triagem". As respostas devem ser curtas, objetivas e, invariavelmente, direcionar para canais privados quando houver qualquer complexidade ou necessidade de dados pessoais.

*   **Objetivo:** Sanitização do ambiente público e proteção da privacidade.
*   **Estilo:** "Call-to-Action" para o canal privado.
*   **Exemplo Prático:**
    *   *Comentário do Usuário:* "Meu IPTU veio errado, o valor está absurdo! Meu CPF é 123.456..."
    *   *Resposta TerezIA:* "Olá! Por favor, **apague seu comentário** para proteger seus dados pessoais (CPF). Para questões de valores de IPTU e revisão cadastral, pedimos que nos chame no **Inbox (Mensagem Privada)** ou procure o Setor de Tributação. Estamos prontos para analisar seu caso com segurança e sigilo."

### 3.2. Estratégia para Atendimento Privado (Inbox)

No ambiente privado, a TerezIA pode desdobrar menus de navegação, enviar links diretos para o Portal da Transparência e fornecer detalhamentos processuais.

*   **Objetivo:** Resolução informativa ou encaminhamento qualificado.
*   **Estilo:** Conversacional, detalhado e guiado por menus.
*   **Exemplo Prático:**
    *   *Mensagem do Usuário:* "Queria saber das vagas de emprego."
    *   *Resposta TerezIA:* "Olá! A Agência do Trabalhador de Santa Tereza do Oeste possui novas oportunidades.
        1. **Endereço:** Rua Xavier da Silva, 834 - Centro [18].
        2. **Horário:** Seg-Sex, 07h30 às 13h30 (sem fechar para almoço).
        3. Telefone: (45) 3545-5450.
        Gostaria que eu enviasse o link para as vagas online no sistema estadual?"

## 4. Protocolos de Segurança, Humanização e "Guardrails"

Para cumprir a exigência contratual de um atendimento "humanizado" mas que respeite os "limites institucionais", a TerezIA deve operar sob uma *persona* bem definida e protocolos de segurança rígidos. A humanização não significa fingir ser humano, mas sim demonstrar empatia e clareza, admitindo as limitações tecnológicas (transparência).

### 4.1. Definição da Persona "TerezIA"

A persona deve ser construída como uma **"Servidora Pública Digital Eficiente e Empática"**.

*   **Tom de Voz:** Formal, porém acessível; respeitoso, paciente e direto. Evita gírias, mas não usa "juridiquês" excessivo.
*   **Transparência Radical:** A cada início de sessão (ou a cada 24h), o bot deve se identificar.
    *   *Script de Saudação:* "Olá! Sou a TerezIA, a assistente virtual da Prefeitura. Sou uma inteligência artificial em treinamento para te ajudar com informações oficiais. Não registro protocolos nem atendo emergências médicas. Como posso ser útil hoje?" [20]

### 4.2. Protocolos de Crise (Guardrails de Segurança)

Existem cenários onde a resposta padrão da IA pode ser perigosa ou ilegal. Nestes casos, "Guardrails" (trilhos de segurança) devem interceptar a interação e forçar um script predefinido.

**Protocolo 1: Prevenção ao Suicídio e Saúde Mental**

*   **Gatilhos (Keywords):** "matar", "suicídio", "acabar com tudo", "desespero", "tristeza profunda", "não aguento mais".
*   **Ação do Sistema:** Interrupção imediata do fluxo de LLM. Acionamento de resposta estática (hard-coded).
*   **Script Obrigatório:** "Sinto muito que você esteja passando por um momento tão difícil. Eu sou uma inteligência artificial e não tenho capacidade para oferecer o acolhimento emocional que você merece. Por favor, saiba que você não está sozinho(a). Entre em contato agora com o **CVV (Centro de Valorização da Vida)** pelo telefone **188** (ligação gratuita 24h, sigilosa) ou acesse [cvv.org.br](https://cvv.org.br) [22]. Sua vida é muito importante."

**Protocolo 2: Violência Doméstica e Contra a Mulher**

*   **Gatilhos:** "agressão", "marido bateu", "medo dele", "ameaça", "violência doméstica", "Maria da Penha".
*   **Ação do Sistema:** Fornecimento imediato de canais de denúncia e proteção, sem julgamento.
*   **Script Obrigatório:** "Violência contra a mulher é crime grave e você tem direitos garantidos por lei. Não se cale. Para ajuda imediata ou denúncia, ligue **180 (Central de Atendimento à Mulher)** ou **190 (Polícia Militar)** em caso de emergência. Em Santa Tereza do Oeste, você pode procurar o **CREAS** ou a Assistência Social para acolhimento sigiloso e apoio jurídico. Estamos aqui para te apoiar." [24]

**Protocolo 3: Proteção à Criança e Adolescente (Conselho Tutelar)**

*   **Gatilhos:** "abuso infantil", "criança abandonada", "espancamento", "conselho tutelar".
*   **Ação do Sistema:** Informar o contato do plantão.
*   **Script Obrigatório:** "Situações envolvendo risco a crianças e adolescentes exigem ação rápida. Acione o **Conselho Tutelar**. O telefone de plantão em Santa Tereza do Oeste é **(45) 3124-1035** (horário comercial) ou verifique o celular de plantão na portaria da Prefeitura/Polícia Militar [19]. Você também pode denunciar anonimamente pelo **Disque 100** (Direitos Humanos)."

## 5. Pesquisa Técnica: Ferramentas, Bibliotecas e Modelos LLM

A escolha da infraestrutura tecnológica é determinante para a viabilidade econômica e a soberania dos dados do projeto. O mercado atual oferece desde modelos proprietários de alto custo até soluções de código aberto ("Open Weights") que podem ser hospedadas localmente ou em nuvens privadas, garantindo maior conformidade com a soberania digital brasileira.

### 5.1. Modelos de Linguagem Grande (LLMs) para o Contexto Brasileiro

#### Opção A: Sabiá-3 (Maritaca AI) — A Soberania Linguística

O modelo **Sabiá-3**, desenvolvido pela brasileira Maritaca AI, destaca-se como a opção mais alinhada culturalmente [29].

*   **Diferenciais Técnicos:** Treinado especificamente em *corpus* brasileiro, o modelo compreende nuances da legislação nacional (diferença entre "fúria" e "dolo", funcionamento do SUS, burocracia do DETRAN) que modelos globais frequentemente perdem. Benchmarks indicam desempenho superior ou equivalente ao GPT-4 em tarefas de redação jurídica e administrativa em PT-BR [31].
*   **Soberania de Dados:** O processamento pode ocorrer em servidores nacionais (dependendo da modalidade de contratação), mitigando riscos de transferência internacional de dados sensíveis de cidadãos [33].
*   **Custo:** Competitivo em relação ao GPT-4o, com a vantagem de ser cobrado em Reais (BRL) em alguns casos, evitando exposição cambial direta [34].
*   **Recomendação:** Ideal para a camada de **geração de respostas**, onde a naturalidade e a precisão terminológica são críticas.

#### Opção B: Llama 3.1 / 3.3 (Meta) — Eficiência e Código Aberto

A família Llama 3 (especificamente as versões 70B Instruct) representa o estado da arte em modelos abertos [35].

*   **Diferenciais Técnicos:** O Llama 3.3 70B oferece capacidades de raciocínio lógico comparáveis a modelos proprietários, mas com uma eficiência de inferência muito maior. É altamente customizável (*fine-tuning*) com dados municipais.
*   **Infraestrutura e Custo:** Pode ser hospedado em provedores de inferência de baixíssima latência como **Groq** (focada em velocidade extrema) ou **DeepInfra**, com custos variando entre **$0.59 a $0.90 por milhão de tokens** [38]. Isso representa uma economia drástica comparada aos modelos da OpenAI.
*   **Recomendação:** Excelente para o motor de **raciocínio do RAG** (processar os documentos recuperados e extrair a resposta), devido à sua velocidade e baixo custo.

#### Opção C: GPT-4o-mini (OpenAI) — O Padrão de Mercado

*   **Visão Geral:** Modelo proprietário de baixo custo ($0.15/1M tokens de entrada) [41].
*   **Prós/Contras:** Fácil integração e alta confiabilidade. Porém, os dados trafegam necessariamente por servidores nos EUA, o que pode gerar atrito com interpretações mais rigorosas da soberania digital no setor público.
*   **Recomendação:** Backup ou solução para prototipagem rápida.

### 5.2. Ferramentas de Orquestração e "Guardrails"

Para transformar um LLM em um "agente institucional", é necessário um software intermediário que controle o fluxo da conversa.

#### NVIDIA NeMo Guardrails

Ferramenta de código aberto essencial para limitar o escopo do bot [43].

*   **Aplicação na TerezIA:** Permite definir "trilhos" temáticos. Se o usuário perguntar sobre "Política Partidária" ou "Eleições Federais", o NeMo intercepta a intenção antes mesmo de chegar ao LLM e devolve uma resposta padrão: *"Sou uma assistente institucional municipal e não discuto política partidária."* Isso protege a administração de acusações de viés político.
*   **Verificação de Fatos:** Pode ser configurado para checar se a resposta gerada pelo LLM está contida nos documentos recuperados, reduzindo alucinações.

#### LangChain & Constitutional AI

*   **Constitutional AI:** Um conceito onde se define uma "constituição" para o bot (ex: "Sempre cite a fonte oficial", "Nunca seja rude", "Se não souber, admita e dê o telefone"). O LangChain implementa cadeias de *self-critique* onde o bot revisa sua própria resposta antes de enviar, garantindo conformidade com esses princípios [46].
*   **Integração RAG:** Facilita a conexão entre o banco de dados vetorial (onde estão os PDFs da prefeitura) e o modelo de linguagem.

## 6. Transparência Algorítmica e Conformidade Legal

A transparência não é apenas ética, é uma exigência legal para o uso de IA no setor público. O sistema deve ser auditável e claro quanto às suas limitações.

### 6.1. Aviso de Isenção de Responsabilidade (Disclaimer)

Todo início de interação deve conter um *disclaimer* visível:

*"Esta é uma mensagem gerada automaticamente por inteligência artificial (Sistema TerezIA - Projeto Piloto). As informações são baseadas na base de dados oficial do município, mas podem conter imprecisões. Para decisões legais ou financeiras, consulte sempre o Diário Oficial ou o atendimento presencial."* [20]

### 6.2. Retenção e Anonimização de Dados

Conforme o contrato e a LGPD, o sistema não deve armazenar dados sensíveis dos cidadãos (como CPF, diagnósticos de saúde) em seus logs de treinamento. Devem ser implementados filtros de "Data Masking" (mascaramento de dados) que substituem CPFs e telefones por *tokens* (ex:) antes que o texto seja processado ou armazenado para auditoria.

## 7. Roteiro de Implementação e Manutenção

Para garantir o sucesso do projeto piloto, sugere-se um cronograma faseado:

1.  **Fase 1: Estruturação e Ingestão (Semanas 1-2):** Digitalização e fragmentação (*chunking*) dos documentos municipais (Minuta de Contrato, Leis de Transporte, Tabelas de IPTU) em um banco vetorial (ex: Qdrant ou ChromaDB).
2.  **Fase 2: Configuração do RAG e Persona (Semanas 3-4):** Configuração do *System Prompt* com a persona "TerezIA" e integração com o modelo Sabiá-3 ou Llama 3.3. Implementação dos *Guardrails* (NeMo) para bloquear temas sensíveis.
3.  **Fase 3: Testes de Estresse (Semana 5):** "Red Teaming" — uma equipe tenta quebrar as regras do bot (ex: tentar fazê-lo ser rude, dar opiniões políticas ou inventar leis). Ajuste fino dos bloqueios.
4.  **Fase 4: Lançamento Piloto e Monitoramento (Semana 6+):** Disponibilização controlada no Facebook/Instagram. Monitoramento diário por um humano ("Human-in-the-loop") para corrigir respostas imprecisas e atualizar a base de conhecimento.

## 8. Conclusão

A TerezIA representa um avanço significativo na gestão pública de Santa Tereza do Oeste. Ao adotar uma arquitetura **RAG (Retrieval-Augmented Generation)** fundamentada em documentos oficiais e protegida por camadas de **Guardrails** e **IA Constitucional**, o município mitiga os riscos inerentes à inteligência artificial generativa. A escolha de modelos soberanos ou abertos eficientes, aliada a protocolos de crise humanizados para saúde mental e violência doméstica, demonstra um compromisso com a responsabilidade social e a inovação segura. Este projeto piloto, se executado conforme este relatório, servirá não apenas como ferramenta de eficiência, mas como modelo de governança digital ética para pequenos e médios municípios brasileiros.

---

## Referências

1.  MINUTA DE CONTRATO - Instagram e Facebook.pdf
2.  [The Hidden Metric That Determines AI Product Success](https://blog.langchain.com/the-hidden-metric-that-determines-ai-product-success/) - LangChain Blog, acessado em janeiro 12, 2026
3.  [Quais as melhores práticas para se construir um bot humanizado?](https://blog.tactium.com.br/quais-as-melhores-praticas-para-se-construir-um-bot-humanizado/) - Blog da Tactium, acessado em janeiro 12, 2026
4.  [Prefeitura de Santa Tereza do oeste](https://www.santatereza.pr.gov.br/site/), acessado em janeiro 12, 2026
5.  [Matriculas NOVAS da Rede Municipal de Ensino](https://www.santatereza.pr.gov.br/noticiasView/1841_Matriculas-NOVAS-da-Rede-Municipal-de-Ensino-.html) - Prefeitura de Santa Tereza do oeste, acessado em janeiro 12, 2026
6.  [Lista Telefones](https://www.santatereza.pr.gov.br/pagina/528_Telefones-Contato.html) - Prefeitura de Santa Tereza do oeste, acessado em janeiro 12, 2026
7.  [Estão abertas as inscrições para o Programa Cartão Transporte Universitário 2023.2 do Governo do Estado](https://www.uema.br/2023/08/estao-abertas-as-inscricoes-para-o-programa-cartao-transporte-universitario-2023-2-do-governo-do-estado/) - UEMA, acessado em janeiro 12, 2026
8.  [Lançado edital 2025.1 do programa Cartão Transporte Universitário](https://www.ma.gov.br/noticias/lancado-edital-2025.1-do-programa-cartao-transporte-universitario) | Estado do Maranhão, acessado em janeiro 12, 2026
9.  [Senado vota impeachment hoje](https://impresso.oparana.com.br/wp-content/uploads/2024/09/impresso.oparana.com.br-edicao-12299-binder1.pdf) - O Paraná Impresso, acessado em janeiro 12, 2026
10. [E-PROTOCOLO N.º 22.392.766-1 DATA: 01/07/2024 PARECER CEE/CP N.º 246/2024 APROVADO EM 17/10/2024 CONSELHO PLENO INTERESSADA: S](https://www.cee.pr.gov.br/sites/cee/arquivos_restritos/files/documento/2024-10/pa_cp_246_24.pdf) - CEE/PR, acessado em janeiro 12, 2026
11. [Abre e fecha: Confira o funcionamento dos serviços no feriado da](https://cgn.inf.br/noticia/505929/abre-e-fecha-confira-o-funcionamento-dos-servicos-no-feriado-da-independencia), acessado em janeiro 12, 2026
12. [Confira como ficam os serviços públicos no feriado de Consciência Negra](https://taroba.com.br/noticias/cidade/confira-como-ficam-os-servicos-publicos-no-feriado-de-consciencia-negra) - Tarobá, acessado em janeiro 12, 2026
13. [Destacamento - Santa Tereza do Oeste](https://www.pmpr.pr.gov.br/Pagina/Destacamento-Santa-Tereza-do-Oeste) - POLÍCIA MILITAR DO PARANÁ, acessado em janeiro 12, 2026
14. [Acionar serviços de emergência - Samu e Siate](https://www.pmpr.pr.gov.br/servicos/Servicos/Emergencia/Acionar-servicos-de-emergencia-Samu-e-Siate-JGoMvN0e) - POLÍCIA MILITAR DO PARANÁ, acessado em janeiro 12, 2026
15. [refis 2025](https://www.santatereza.pr.gov.br/noticiasView/?id=1844) - Prefeitura de Santa Tereza do oeste, acessado em janeiro 12, 2026
16. [Santa Tereza do Oeste - Governo Digital](https://santaterezadooeste.oxy.elotech.com.br/governo-digital/) - Elotech, acessado em janeiro 12, 2026
17. [Coleta de Lixo em Santa Tereza: Faça Sua Parte!](https://santaterezadotocantins.to.gov.br/coleta-de-lixo-em-santa-tereza-faca-sua-parte/), acessado em janeiro 12, 2026
18. [Confira as vagas de emprego disponíveis na Agência do Trabalhador nesta quinta-Feira(21)](https://acontecenafronteira.com.br/index.php/2024/11/21/confira-as-vagas-de-emprego-disponiveis-na-agencia-do-trabalhador-nesta-quinta-feira21/) - Acontece Na Fronteira, acessado em janeiro 12, 2026
19. [Lista Fones Secretarias](https://www.santatereza.pr.gov.br/pagina/530_Lista-Fones-Secretarias.html) - Prefeitura de Santa Tereza do oeste, acessado em janeiro 12, 2026
20. [Chatbot Disclaimer](https://www.trade.gov/chatbot-disclaimer) - International Trade Administration, acessado em janeiro 12, 2026
21. [A galera tá falando que tá com 'psicose de IA' e tá implorando por ajuda pro FTC… Que que tá rolando?](https://www.reddit.com/r/ArtificialInteligence/comments/1od8s5b/people_are_saying_theyve_got_ai_psychosis_and_are/?tl=p...) : r/ArtificialInteligence - Reddit, acessado em janeiro 12, 2026

```
