# Relatório Técnico de Implementação e

# Estratégia de Atendimento Digital

# Automatizado: Projeto {bot_name}

## 1. Introdução e Contextualização Estratégica

A transformação digital no setor público transcendeu a categoria de inovação desejável para
se tornar um imperativo de eficiência administrativa e democratização do acesso aos serviços
estatais. No contexto do Município de {client_name}, Paraná, a iniciativa de
implementação de um sistema de atendimento automatizado — denominado neste estudo
como **{bot_name}** — representa um marco estratégico na modernização da interface entre a
Administração Pública e o cidadão. Este documento constitui um estudo técnico exaustivo,
desenhado para orientar a implementação, a governança e a operação do assistente virtual,
em estrita conformidade com a minuta contratual fornecida e as especificações técnicas do
projeto piloto.

A análise aqui empreendida parte da premissa de que a tecnologia, por si só, não resolve
gargalos de atendimento; é a sua aplicação orientada por processos bem definidos,
segurança jurídica e design centrado no cidadão que gera valor público. O cenário atual,
caracterizado pela onipresença das redes sociais — especificamente Facebook e Instagram,
conforme delimitado no escopo do projeto — exige que o poder público ocupe esses espaços
não apenas como emissor de comunicados, mas como um agente responsivo e solucionador
de dúvidas.

O estudo baseia-se em uma análise documental profunda da **Minuta de Contrato nº
001/2026** 1 , que estabelece as bases legais da relação entre o Município (Contratante) e a

empresa de tecnologia (Contratada), bem como do arquivo técnico **README.md** 1 , que
descreve a arquitetura do sistema. Adicionalmente, foram considerados dados institucionais
extraídos do portal oficial da Prefeitura 2 e de diversas fontes legislativas e normativas que
regem o serviço público municipal.

A complexidade deste projeto reside na necessidade de equilibrar a automação com a
humanização e a legalidade. A inteligência artificial (IA) generativa, embora poderosa, carrega
riscos inerentes de "alucinação" (geração de informações falsas) e viés. No ambiente público,
um erro informacional não é apenas uma falha técnica; é um ato administrativo com
potenciais repercussões legais. Portanto, este relatório não apenas sugere "o que fazer", mas
detalha rigorosamente "como fazer" com segurança, estabelecendo protocolos de
redirecionamento para departamentos humanos sempre que a complexidade da demanda
ultrapassar a capacidade informativa do sistema, conforme preconizado na Cláusula Primeira,


item 1.2 do contrato.^1

A abrangência deste estudo cobre desde a arquitetura de dados e privacidade (LGPD) até a
definição granular de fluxos de conversação para saúde, educação, tributação e serviços
urbanos. O objetivo final é entregar um roteiro que permita ao Município de {client_name} do
Oeste inaugurar um canal de atendimento que seja, ao mesmo tempo, uma ferramenta de
transparência ativa e um facilitador da vida cotidiana dos seus munícipes.

## 2. Análise Jurídica e Alinhamento com o Escopo

## Contratual

A fundação de qualquer projeto de GovTech (Tecnologia para Governo) deve ser a segurança
jurídica. A análise da minuta contratual 1 revela diretrizes que moldam não apenas a relação
comercial, mas a própria lógica de funcionamento do algoritmo do chatbot.

### 2.1. Natureza Estritamente Informativa e Limitações Operacionais

O contrato define explicitamente, em sua Cláusula Primeira, que o sistema terá caráter
"estritamente informativo e institucional", vedando a substituição do atendimento humano, a
execução de serviços administrativos, o registro de protocolos e, crucialmente, a realização
de decisões automatizadas.^1 Esta delimitação é vital para a configuração da IA.

Diferentemente de chatbots no setor privado, que buscam fechar vendas ou alterar cadastros
autonomamente, a {bot_name} deve operar como um **triador qualificado e um repositório de
conhecimento ativo**. O sistema não pode, por exemplo, deferir um pedido de isenção de
IPTU ou agendar uma consulta médica de forma autônoma sem supervisão humana, pois tais
atos requerem competência administrativa delegada por lei a servidores públicos.

A implicação técnica desta cláusula é a necessidade de um design de fluxo que privilegie o
**Redirecionamento Assistido**. Quando o cidadão solicitar um serviço transacional (ex:
"Quero parcelar minha dívida"), o bot não deve tentar processar o parcelamento, mas sim
explicar as regras (informativo) e fornecer o link direto para o sistema tributário ou o
endereço do balcão de atendimento (direcionamento), cumprindo o disposto na Cláusula
Terceira, item 3.1.^1

### 2.2. O Papel do Operador de Dados e a Conformidade com a LGPD

A Cláusula Décima Segunda do contrato aborda a Proteção de Dados Pessoais (LGPD - Lei nº
13.709/2018). O contrato tipifica a empresa contratada como "operadora" dos dados, agindo
sob as instruções do Município, que é o "controlador".^1

No contexto de atendimento via redes sociais (Facebook e Instagram), a privacidade enfrenta


desafios específicos. As interações ocorrem em dois ambientes distintos:

1. **Ambiente Público (Comentários em Posts):** Aqui, a exposição de dados é máxima. O
    cidadão, muitas vezes por desconhecimento, pode publicar dados sensíveis (CPF,
    telefone, detalhes de saúde) em comentários públicos. O protocolo do chatbot deve
    incluir a detecção imediata desses dados e a ocultação do comentário (via API da rede
    social), seguida de uma mensagem instruindo o cidadão a migrar para o canal privado.
2. **Ambiente Privado (Inbox/Direct):** Embora privado, o canal é gerido por terceiros
    (Meta). A coleta de dados deve observar o princípio da minimização. O chatbot só deve
    solicitar os dados estritamente necessários para identificar a demanda e direcionar o
    cidadão. Não se deve, por exemplo, solicitar fotos de documentos ou laudos médicos via
    chat, a menos que haja um ambiente seguro e criptografado end-to-end integrado, o
    que não parece ser o escopo inicial do projeto piloto.

O sistema de "Policy Guard" (Guarda de Políticas) descrito na arquitetura técnica 1 é a
resposta tecnológica a esta exigência legal. A implementação de filtros _PRE_ (antes do
processamento) e _POST_ (antes da resposta) garante que a IA não solicite nem armazene
dados sensíveis (PII - Personally Identifiable Information) de forma inadvertida, protegendo o
município de incidentes de segurança da informação.

### 2.3. Níveis de Serviço (SLA) e Continuidade Administrativa

A Cláusula Décima estabelece uma disponibilidade mínima de 90% e tempos de resposta
para suporte técnico.^1 Para a administração pública, isso sinaliza que o chatbot é considerado
um serviço essencial de comunicação. A indisponibilidade do sistema em momentos críticos
(ex: prazos finais de REFIS ou campanhas de vacinação) pode gerar danos à imagem
institucional e prejuízos ao erário.

Além disso, a natureza de "projeto piloto" e a vigência por prazo indeterminado exigem um
plano de transição. Caso o contrato seja rescindido, a Cláusula Nona define que a "base de
conhecimento" e os "dados de uso" pertencem à Contratante (Município), enquanto o
código-fonte pertence à Contratada. Isso reforça a necessidade de manter a base de
conhecimento (o conteúdo das perguntas e respostas) em formatos abertos e exportáveis,
garantindo que a inteligência acumulada sobre as dúvidas dos cidadãos não seja perdida.

## 3. Arquitetura Técnica e Segurança da Informação

A eficácia do atendimento digital depende intrinsecamente da robustez da solução técnica
adotada. A análise do arquivo README 1 indica uma abordagem moderna, baseada em
arquitetura RAG (Retrieval-Augmented Generation), que é o padrão-ouro atual para chatbots
que requerem alta precisão factual e baixa alucinação.


### 3.1. O Pipeline RAG e a Prevenção de Alucinações

A "alucinação" em IA refere-se à geração de respostas plausíveis, porém factualmente
incorretas. Em um contexto governamental, uma alucinação pode significar informar uma data
errada de vencimento de imposto ou um local inexistente de vacinação. Para mitigar esse
risco, o sistema {bot_name} utiliza o seguinte fluxo:

1. **Input do Cidadão:** A mensagem chega via API do Facebook/Instagram.
2. **Classificação de Intenção:** Um modelo intermediário identifica o tema (ex: "Saúde",
    "Educação", "Tributos"). Isso permite aplicar regras de negócio específicas antes mesmo
    de consultar a base de dados.
3. **Recuperação (Retriever):** O sistema não "pensa" a resposta imediatamente. Ele busca
    em um banco de dados vetorial (ChromaDB) os fragmentos de documentos oficiais que
    contêm a resposta. Por exemplo, se a pergunta é sobre "horário do posto de saúde", ele
    recupera o snippet exato do documento 3 que contém essa informação.
4. **Geração Aumentada:** O modelo de linguagem (LLM) recebe a pergunta do cidadão
    _junto com_ o fragmento oficial recuperado e uma instrução rígida: "Responda usando
    _apenas_ o contexto fornecido".
5. **Validação (Policy Guard):** Antes de enviar, a resposta passa por um filtro de segurança
    para garantir que não contém linguagem ofensiva, promessas administrativas ou dados
    sensíveis.

Esta arquitetura garante que a {bot_name} atue como um bibliotecário extremamente eficiente,
que consulta os livros oficiais antes de responder, em vez de um autor criativo que inventa
histórias.

### 3.2. Integração Omni-Channel (Meta API)

O contrato especifica o atendimento via Instagram e Facebook (inbox e publicações). A
integração técnica deve utilizar a API Oficial (Graph API). O uso de ferramentas não oficiais ou
"wrappers" de navegador representa um risco de bloqueio das contas institucionais da
Prefeitura.

A distinção técnica entre **Comentários** e **Inbox** é crucial:

```
● Webhooks de Comentários: Devem ser configurados para monitorar palavras-chave de
crise e dúvidas simples. A resposta padrão em comentários deve ser curta e diretiva
("Olá, para essa dúvida, por favor nos chame no Inbox para protegermos seus dados").
● Webhooks de Inbox: Permitem o fluxo conversacional completo. É aqui que o motor RAG
deve operar com sua capacidade total.
```
### 3.3. Auditoria e Rastreabilidade

O README menciona o uso de PostgreSQL para auditoria.^1 Isso é fundamental para a
transparência. Cada interação do chatbot deve gerar um log contendo:


```
● Timestamp (Data/Hora).
● Canal (FB/IG).
● Input do Usuário (anonimizado se possível).
● Intenção Identificada.
● Documentos Recuperados (quais fontes foram usadas).
● Resposta Gerada.
```
Esses dados não servem apenas para depuração técnica, mas são insumos valiosos para a
gestão pública. Eles revelam quais são as reais dúvidas da população, permitindo que a
Prefeitura ajuste sua comunicação e políticas públicas baseada em dados reais de demanda
(Data-Driven Policy Making).

## 4. Estudo de Boas Práticas em Chatbots para Gestão

## Pública

A implementação da {bot_name} deve espelhar as melhores práticas observadas em casos de
sucesso nacionais e diretrizes federais de governo digital. A análise de documentos sobre
inovação no setor público 4 e manuais de redes sociais 8 aponta para três pilares
fundamentais: Linguagem Simples, Empatia Digital e Integração de Canais.

### 4.1. Linguagem Simples (Plain Language) e Acessibilidade

A administração pública é historicamente associada a uma linguagem burocrática e
hermética ("juridiquês"). O chatbot tem a missão de atuar como um tradutor, convertendo
termos técnicos em linguagem cidadã.

```
● Diretriz: Substituir termos como "o munícipe deve protocolar requerimento" por "você
precisa entregar o pedido".
● Justificativa: A Lei de Governo Digital (Lei nº 14.129/2021) e manuais de redação oficial
```
(^10) incentivam o uso de linguagem simples para garantir que a informação seja
compreensível por qualquer pessoa, independentemente do seu grau de instrução.
● **Aplicação na {bot_name}:** As respostas do FAQ (Seção 7) foram redigidas seguindo esse
princípio: frases curtas, ordem direta, voz ativa e vocabulário acessível.

### 4.2. Gestão de Expectativas e Humanização

Embora seja um sistema automatizado, a interação deve ser humanizada, mas honesta. A
"persona" da {bot_name} deve ser cordial, paciente e institucional.

```
● Transparência: É imperativo que o chatbot se identifique como uma inteligência artificial
logo na saudação inicial. Isso ajusta a expectativa do cidadão e reduz a frustração em
caso de falhas de compreensão.
○ Exemplo de Saudação: "Olá! Sou a {bot_name}, a assistente virtual da Prefeitura de Santa
```

```
Tereza do Oeste. Sou uma inteligência artificial em treinamento. Como posso te
ajudar hoje?"
● Empatia em Falhas: Quando o bot não entender a pergunta (fallback), a resposta não
deve ser um erro genérico, mas um pedido educado de reformulação ou a oferta de
canais alternativos.
```
### 4.3. Omnicanalidade e Continuidade do Atendimento

O chatbot não deve ser um "beco sem saída". Uma das maiores frustrações do cidadão é
receber uma resposta vaga sem indicação de como prosseguir. As melhores práticas 5
indicam que, se o chatbot não pode resolver o problema (por ser um serviço administrativo
complexo), ele deve fornecer a "ponte" exata para a solução:

```
● Link direto para o sistema específico (ex: emissão de boleto).
● Número de telefone do setor responsável.
● Endereço físico com ponto de referência.
● Horário de funcionamento atualizado.
```
Esta prática transforma o chatbot em um "balcão de triagem" eficiente, desafogando o
atendimento telefônico de dúvidas simples e permitindo que os servidores humanos foquem
nos casos complexos.

## 5. Protocolos Operacionais para Casos Sensíveis e

## Crises

A automação do atendimento traz riscos quando confrontada com situações humanas
extremas ou crises institucionais. O sistema deve possuir "gatilhos de segurança" que
interrompem o fluxo de inteligência artificial generativa e acionam respostas estáticas,
pré-aprovadas e seguras.

### 5.1. Protocolo de Saúde Mental e Risco à Vida

Palavras-chave como "suicídio", "matar", "morrer", "depressão", "ajuda", "desespero" devem
acionar um protocolo de emergência imediato.

```
● Ação do Sistema: Interrupção imediata da tentativa de "conversar" ou buscar
informações gerais.
● Resposta Obrigatória: Deve ser empática, direta e fornecer canais de ajuda
profissional.
○ Script: "Sinto muito que você esteja passando por isso. Você não está sozinho. A
Prefeitura se importa com você. Se precisar de apoio emocional imediato, ligue para
o CVV no número 188 (ligação gratuita e sigilosa). Em caso de emergência médica,
```

```
ligue 192 (SAMU). Procure também nossas unidades de saúde para acolhimento."
```
### 5.2. Protocolo de Violência Doméstica e Abuso

Diante de relatos de violência contra mulher, criança, idoso ou vulnerável, o chatbot não deve
tentar "investigar" o caso.

```
● Ação do Sistema: Fornecer canais de denúncia e proteção.
● Resposta Obrigatória:
○ Script: "A violência não pode ser tolerada. Para denúncias de violência contra a
mulher, ligue 180. Para violação de direitos humanos, ligue 100. Em caso de perigo
imediato, chame a Polícia Militar no 190. Você também pode procurar o Conselho
Tutelar de {client_name} no telefone (45) 3124-1035 ou o CREAS."
```
### 5.3. Protocolo de Crise Institucional e Desinformação

Em momentos de crise (ex: desastres naturais, escândalos políticos, falhas graves de serviço),
as redes sociais são inundadas de comentários. O "Policy Guard" deve ser ajustado para
detectar picos anômalos de interações sobre determinados temas.

```
● Gestão de Comentários Ofensivos: O chatbot não deve responder a insultos,
xingamentos ou provocações ("trolls"). A melhor prática é o silêncio automatizado e a
notificação à equipe de comunicação para moderação humana (ocultação/banimento
conforme termos de uso). Responder a um "troll" automatizadamente pode gerar prints
vexatórios para a administração.
● Desinformação (Fake News): Se houver uma onda de boatos (ex: "a vacina acabou"), a
base de conhecimento deve ser atualizada imediatamente com um tópico "Verdade
sobre a vacina", e o bot deve priorizar essa resposta quando o tema for mencionado.
```
## 6. FAQ Completo e Base de Conhecimento

## Estruturada

Esta seção constitui o "cérebro" da {bot_name}. As informações foram rigorosamente extraídas e
consolidadas a partir dos dados brutos coletados do site da Prefeitura, contratos e notícias
locais. Elas estão organizadas por eixos temáticos para facilitar a ingestão no banco de dados
vetorial.

### 6.1. Eixo Institucional e Contatos Gerais

Este módulo cobre as dúvidas mais frequentes sobre localização e contato básico da
administração municipal.


```
Tópico Pergunta
Frequente
```
```
Resposta
Padronizada
(Base de
Conhecimento)
```
```
Fonte
```
```
Localização Qual o endereço da
Prefeitura?
```
```
A Prefeitura de
{client_name} do
Oeste fica na
Avenida Paraná,
61 – Centro. O CEP
é 85825-000.
```
```
2
```
```
Contato Qual o telefone da
Prefeitura?
```
```
O telefone geral é
(45) 3124-1000. O
atendimento
funciona de
segunda a
sexta-feira.
```
```
2
```
```
Horário Qual o horário de
atendimento?
```
```
O expediente é de
segunda a sexta,
das 8h às 12h e
das 13h às 17h.
```
```
2
```
```
E-mail Qual o e-mail
oficial?
```
```
O e-mail geral para
contato é
prefeitura@santat
ereza.pr.gov.br.
```
```
2
```
```
Ouvidoria Como faço uma
reclamação?
```
```
Para reclamações,
denúncias ou
elogios, use a
Ouvidoria.
Telefone: (45)
3124-1028 ou
acesse o site oficial
da prefeitura.
```
```
2
```
### 6.2. Eixo Saúde Pública (USF, Emergências e Especialidades)

_Atenção Crítica:_ Este eixo exige precisão absoluta. Erros aqui podem ter consequências


graves. O sistema deve sempre diferenciar "Atendimento Básico" de "Emergência".

```
Unidade de
Saúde
```
```
Endereço Telefone /
Contato
```
```
Serviços
Principais
```
```
Fonte
```
```
PSF Central
João Mulitor
```
```
Av. Brasília,
525 - Centro
```
```
Recepção:
(45) 3124-
```
```
Exames:
3124-1022/
```
```
PA 24h:
3124-
```
```
Unidade
central,
exames
laboratoriais e
Pronto
Atendimento
24 horas.
```
```
3
```
##### SAMU

```
(Emergência)
```
- **192** Atendimento
    móvel de
    urgência para
    casos de risco
    à vida.

```
14
```
```
PSF Clínica
da Mulher
```
```
Rua Castro
Alves, 162
```
```
(45) 3124-1045 Saúde da
mulher,
pré-natal,
preventivos.
```
```
3
```
```
PSF Vila
Operária
```
```
Rua José
Calazans, 97
```
##### (45)

##### 3124-

```
Consultas
médicas e de
enfermagem
(Atenção
Básica).
```
```
3
```
```
PSF Santa
Maria
```
```
Av. Manoel
José de
Carvalho
```
```
(45) 3124-1098 Consultas
médicas e de
enfermagem
(Atenção
Básica).
```
```
3
```
```
PSF Malucelli Rua Castro
Alves
```
```
(45) 3124-1082 Consultas
médicas e de
enfermagem
```
```
3
```

```
(Atenção
Básica).
```
```
PSF - NASF Rua Rincão
Cumprido, 15
```
```
(45) 3124-1080 Núcleo de
Apoio à Saúde
da Família
(Multidisciplina
r).
```
```
3
```
```
Fisioterapia
Municipal
```
```
Rua Duque de
Caxias
```
```
(45) 3124-1081 Sessões de
fisioterapia e
reabilitação.
```
```
3
```
```
Vigilância
Sanitária
```
- (45) 3124-1093 Fiscalização e
    denúncias
    sanitárias.

```
13
```
**Nota de Implementação:** Se o usuário mencionar sintomas como "dor no peito", "falta de ar"
ou "acidente", o bot deve ignorar a tabela de PSFs e exibir imediatamente o contato do **SAMU
(192)** e do **Pronto Atendimento 24h (PSF Central)**.

### 6.3. Eixo Educação e Transporte Escolar

Informações sobre matrículas, transporte e estrutura escolar. É vital observar a sazonalidade
das matrículas.

```
Serviço / Tema Informação Chave Contato / Local Fonte
```
```
Secretaria de
Educação
```
```
Gestão de escolas
e CMEIs.
```
```
Rua Internacional,
1597 – Centro. Tel:
(45) 3124-1010.
```
```
15
```
```
Matrículas
(Infantil V)
```
```
Obrigatório para
crianças de 4 anos.
Período geralmente
em novembro.
```
```
Presencial na
Secretaria ou
Escolas. Levar Docs
Pessoais + Vacina.
```
```
15
```
```
Lista de Espera
CMEI
```
```
Consulta de vagas
em creches.
```
```
Disponível no site
oficial ("Lista
espera Cmei") ou
```
```
2
```

```
na Secretaria.
```
```
Escola Mun. Hélio
Balarotti
```
```
Ensino
Fundamental.
```
```
R. Buenos Aires,
```
488. Tel: (45)
3124-1050.

```
16
```
```
Transporte
Universitário
```
```
Apoio a estudantes
de nível
superior/técnico em
cidades vizinhas.
```
```
Gerido via
Associações de
Estudantes com
apoio da Prefeitura.
Verificar editais
anuais.
```
```
17
```
Tabela de Horários de Ônibus (Transporte Intermunicipal - Expresso {client_name}):
Ref.: Linha {client_name} x Cascavel (Vigência Ref. 2024/2025) 19

```
Saída de {client_name} Saída de Cascavel Observações
```
```
06:00 06:40 Segunda a Sexta
```
```
07:00 07:50 Segunda a Sexta
```
```
08:05 08:45 Segunda a Sexta
```
```
12:20 13:15 Segunda a Sexta
```
```
17:00 17:40 Segunda a Sexta
```
```
18:00 18:50 Segunda a Sexta
```
_Aviso:_ O bot deve informar que "Os horários de ônibus são de responsabilidade da
concessionária e podem sofrer alterações. Consulte a rodoviária ou a empresa Expresso


{client_name} para confirmação exata."

### 6.4. Eixo Assistência Social e Cidadania

Focado na população vulnerável. O tom deve ser acolhedor e direto.

```
Unidade Endereço Telefone Finalidade Fonte
```
```
Secretaria
Ação Social
```
```
Av. Brasília,
1050 - Centro
```
```
(45) 3124-1030 Gestão geral e
benefícios
eventuais.
```
```
20
```
```
CRAS R. Gov.
Roberto
Silveira, 829
```
```
(45) 3124-1075 Cadastro
Único
(CadÚnico),
Bolsa Família,
Idosos.
```
```
20
```
```
Conselho
Tutelar
```
```
Av. Brasília,
1048 - Centro
```
```
(45) 3124-1035 Violação de
direitos da
criança.
```
```
20
```
```
Agência do
Trabalhador
```
##### - (45)

##### 3124-1000*

```
Vagas de
emprego e
Carteira de
Trabalho.
(*Confirmar
ramal).
```
```
21
```
**Protocolo Conselho Tutelar:** O número listado é administrativo. Para plantões noturnos ou
fins de semana, se não houver atendimento no fixo, o bot deve orientar o contato via **Polícia
Militar (190)** que possui o contato do conselheiro de plantão.

### 6.5. Eixo Tributação e Desenvolvimento Econômico

Área de alta demanda por serviços digitais (boletos, certidões). O foco é o _autoatendimento_.

```
Serviço Descrição Ação
Recomendada
```
```
Fonte
```

```
IPTU 2025 Imposto Predial e
Territorial Urbano.
```
```
Acesse o "Portal do
Cidadão" no site
para emitir a guia
ou vá ao setor de
Tributação.
```
```
2
```
```
REFIS 2025 Programa de
parcelamento de
dívidas (até
31/12/24) com
desconto.
```
```
Atendimento
Presencial
obrigatório no setor
de Tributação para
negociação.
```
```
22
```
```
Nota Fiscal
(NFS-e)
```
```
Emissão de notas
para prestadores
de serviço.
```
```
Acesso exclusivo
via sistema web
("Nota Eletrônica")
no site da
Prefeitura.
```
```
2
```
```
Sala do
Empreendedor
```
```
Apoio ao MEI
(abertura,
declaração,
boletos).
```
```
Av. Paraná - Centro.
Tel: (45)
3124-.
```
```
24
```
```
Alvará Licença de
funcionamento.
```
```
Processo digital ou
presencial na
Tributação.
Necessita vistoria
(Bombeiros/Vigilân
cia).
```
```
25
```
### 6.6. Eixo Serviços Urbanos e Infraestrutura

Informações sobre o dia a dia da cidade.

```
Serviço Informação /
Procedimento
```
```
Contato Fonte
```
```
Coleta de Lixo A coleta segue
cronograma por
bairros (Orgânico e
```
```
Como o
cronograma exato
varia, consulte a
```
```
20
```

```
Reciclável). Secretaria de Meio
Ambiente: (45)
3124-.
```
```
Iluminação
Pública
```
```
Lâmpada queimada
ou piscando.
```
```
Abrir chamado na
Ouvidoria ou
Protocolo Online.
```
```
2
```
```
Secretaria de
Obras
```
```
Manutenção de
estradas e vias.
```
```
Contato via
Prefeitura Geral:
(45) 3124-1000.
```
```
27
```
```
Cultura e Turismo Eventos e
calendário oficial.
```
```
Secretaria de
Cultura e Turismo
(Acesso Rápido no
site).
```
```
2
```
**Nota sobre Coleta de Lixo:** Os dados encontrados nos snippets sobre dias específicos ([28],
[29]) referem-se a homônimos ({client_name}-RS ou TO). **Não utilizar esses dados**. O bot
deve informar o telefone da Secretaria de Meio Ambiente para essa consulta específica para
evitar desinformação.

## 7. Matriz de Encaminhamento e Protocolos de

## Redirecionamento

Para operacionalizar a Cláusula de "Redirecionamento para o departamento correto", o
sistema deve utilizar uma **Matriz de Decisão**. O chatbot não resolve o problema
administrativo, mas entrega o cidadão ao canal resolutivo correto.

### 7.1. Fluxograma de Decisão

1. **Entrada:** Cidadão pergunta "Como faço para podar uma árvore na minha calçada?"
2. **Classificação:** Tema = "Meio Ambiente/Serviços Urbanos".
3. **Verificação de Base:** O bot consulta o FAQ -> poda requer autorização.
4. **Resposta (Informação):** "Para podar árvores em via pública, você precisa de
    autorização da Secretaria de Meio Ambiente."
5. **Redirecionamento (Ação):** "Você pode solicitar isso ligando para **(45) 3124-1095** ou
    indo pessoalmente na Rua João Calazans, 301."

### 7.2. Tabela Mestra de Telefones para Redirecionamento


Esta tabela deve ser carregada no sistema para ser puxada dinamicamente quando o bot não
souber a resposta (fallback) ou identificar a necessidade de atendimento humano.

```
Departamento Telefone Endereço (Referência)
```
**Geral / Prefeitura** (45) 3124-1000 (^) Av. Paraná, 61 2
**Saúde
(Central/Agendamento)**
(45) 3124-1020 (^) Av. Brasília, 525 3
**Saúde (Ouvidoria)** (45) 3124-1028 (^) Av. Brasília, 525 3
**Saúde (Emergência/PA)** (45) 3124-1026 (^) Av. Brasília, 525 3
**Educação** (45) 3124-1010 (^) R. Internacional, 1597 16
**Assistência Social** (45) 3124-1030 (^) Av. Brasília, 1050 20
**CRAS** (45) 3124-1075 R. Gov. Roberto Silveira,
829 20
**Conselho Tutelar** (45) 3124-1035 (^) Av. Brasília, 1048 20
**Meio Ambiente** (45) 3124-1095 (^) R. João Calazans, 301 20
**Agricultura** (45) 3124-1090 (^) Av. Paraná 20
**DETRAN** (45) 3124-1016 (^) R. João Calazans, 213 20
**Sala do Empreendedor** (45) 3124-1004 (^) Av. Paraná 24
**Vigilância Sanitária** (45) 3124-1093 (^) - 13

## 8. Roteiro de Implementação e Manutenção

A implementação da {bot_name} não termina no lançamento (Go-Live). A sustentabilidade do
projeto depende de processos contínuos de curadoria e monitoramento.


### 8.1. Fase 1: Ingestão e Testes (Setup)

```
● Carregamento de Dados: Inserir os FAQs estruturados na Seção 6 no banco de dados
vetorial (ChromaDB) conforme especificado no README.^1
● Configuração de Guardrails: Implementar as palavras-chave de bloqueio (suicídio,
violência) nos filtros de entrada.
● Testes de Estresse: Realizar simulações com perguntas ambíguas para garantir que o
bot não invente dados (ex: perguntar sobre coleta de lixo em um bairro inexistente).
```
### 8.2. Fase 2: Lançamento e Comunicação

```
● Campanha Educativa: Publicar posts no Facebook e Instagram explicando: "A {bot_name}
chegou. Sou uma IA em treinamento. Posso te ajudar com informações, telefones e
endereços."
● Gestão de Comentários: Monitorar intensivamente os comentários nas primeiras 48
horas para ajustar respostas que possam parecer robóticas ou insensíveis.
```
### 8.3. Fase 3: Manutenção Mensal e Evolução

```
● Revisão de Logs: Analisar semanalmente as perguntas que o bot não soube responder.
Isso indicará quais novas informações devem ser adicionadas à base de conhecimento.
● Atualização Sazonal: Criar um calendário para atualizar o bot sobre eventos
recorrentes: Vencimento IPTU (Março/Abril), Matrículas Escolares (Novembro),
Campanhas de Vacinação.
● Auditoria de Links: Verificar mensalmente se os links para o Portal do Cidadão e
sistemas de Nota Fiscal continuam ativos e funcionais.
```
## 9. Conclusão

A implementação do projeto {bot_name}, conforme delineado neste estudo, oferece ao Município
de {client_name} a oportunidade de elevar o patamar do seu atendimento público.
Ao respeitar rigorosamente as limitações contratuais de "caráter informativo" e integrar
protocolos robustos de segurança para casos sensíveis, a administração municipal
protege-se legalmente enquanto oferece um serviço de alto valor agregado ao cidadão.

A chave para o sucesso desta iniciativa não reside na sofisticação tecnológica da IA, mas na
qualidade da **Base de Conhecimento** e na eficiência dos **Protocolos de Redirecionamento**.
O chatbot deve ser visto como um organismo vivo, alimentado constantemente pelas
demandas reais da população e supervisionado por servidores comprometidos com a ética e
a transparência pública. Com a adoção deste plano, {client_name} se posiciona na
vanguarda das cidades inteligentes de pequeno e médio porte, utilizando a tecnologia como
vetor de cidadania e inclusão.

#### Referências citadas


#### 1. MINUTA DE CONTRATO - Instagram e Facebook.pdf

#### 2. Prefeitura de {client_name} do oeste, acessado em janeiro 12, 2026,

#### https://www.santatereza.pr.gov.br/site/

#### 3. Unidades de Saúde - Prefeitura de {client_name} do oeste, acessado em janeiro

#### 12, 2026, https://www.santatereza.pr.gov.br/pagina/519_Unidades-de-Saude.html

#### 4. BOAS PRÁTICAS EM INTELIGÊNCIA ARTIFICIAL NA GESTÃO PÚBLICA, acessado

#### em janeiro 12, 2026,

#### https://conteudo.clp.org.br/primeiros-passos-ia-na-gestao-publica

#### 5. Chatbots inteligentes para atendimento ao cidadão: o novo canal de

#### comunicação nas prefeituras - Essencial Gestão Pública, acessado em janeiro 12,

#### 2026,

#### https://essencialgestaopublica.com.br/chatbots-inteligentes-para-atendimento-a

#### o-cidadao-o-novo-canal-de-comunicacao-nas-prefeituras/

#### 6. Chatbots Municipais: Implementação Prática para Atendimento 24/7 -

#### Unicidades, acessado em janeiro 12, 2026,

#### https://www.unicidades.com.br/chatbots-municipais/

#### 7. Chatbots nas prefeituras: como IA resolve 80% das demandas e economiza

#### milhões, acessado em janeiro 12, 2026,

#### https://blogdoaftm.com.br/chatbots-nas-prefeituras-como-ia-resolve-80-das-de

#### mandas-e-economiza-milhoes/

#### 8. Guia de Atendimento ao Cidadão, Ouvidoria e Controle Interno de SMADS -

#### Prefeitura, acessado em janeiro 12, 2026,

#### https://prefeitura.sp.gov.br/documents/d/assistencia_social/guia-naci-versao-01-

#### 025-pdf

#### 9. Manual orienta uso das Redes Sociais Institucionais - Prefeitura Municipal de

#### Catanduva, acessado em janeiro 12, 2026,

#### https://www.catanduva.sp.gov.br/portal/noticias/0/3/3146/manual-orienta-uso-da

#### s-redes-sociais-institucionais/

#### 10. Linguagem Simples — Portal do Servidor, acessado em janeiro 12, 2026,

#### https://www.gov.br/servidor/pt-br/assuntos/laboragov/curadoria-tematica/linguag

#### em-simples

#### 11. Manual de linguagem simples - Portal Gov.br, acessado em janeiro 12, 2026,

#### https://www.gov.br/servicoscompartilhados/pt-br/acesso-a-informacao/acoes-e-

#### programas/governanca/arquivos_figuras/linguagem_simples_roedel.pdf

#### 12. Transformação Digital: Como o chatbot facilitou a rotina de empresas públicas?,

#### acessado em janeiro 12, 2026,

#### https://www.lumis.com.br/a-lumis/blog/transformacao-digital-como-o-chatbot-f

#### acilitou-a-rotina-de-empresas-publicas.htm

#### 13. Informações COVID - Prefeitura de {client_name} do oeste, acessado em janeiro

#### 12, 2026, https://www.santatereza.pr.gov.br/pagina/518_Covid.html

#### 14. Sobre o SAMU - Central de Regulação, acessado em janeiro 12, 2026,

#### https://www.samunoroestepr.com.br/samu/central-de-regulacao

#### 15. Matriculas NOVAS da Rede Municipal de Ensino - Prefeitura de ..., acessado em

#### janeiro 12, 2026,

#### https://www.santatereza.pr.gov.br/noticiasView/1841_Matriculas-NOVAS-da-Rede


#### -Municipal-de-Ensino-.html

#### 16. PLANO DE AÇÃO DA EDUCAÇÃO MUNICIPAL - Prefeitura de {client_name} do

#### oeste, acessado em janeiro 12, 2026,

#### https://www.santatereza.pr.gov.br/uploads/pagina/arquivos/PLANOACAO2022.pd

#### f

#### 17. Programa Municipal de Auxílio Transporte aos Estudantes Universitários e Nível,

#### acessado em janeiro 12, 2026,

#### https://formosadooeste.pr.gov.br/uploads/pagina/arquivos/Edital-no-11-de-02-de

#### -outubro-de-2025-Prestacao-de-Contas-SETEMBRO.pdf

#### 18. Novos ônibus transportam alunos com mais segurança - Secretaria da Educação,

#### acessado em janeiro 12, 2026,

#### https://www.educacao.pr.gov.br/Noticia/Novos-onibus-transportam-alunos-com-

#### mais-seguranca

#### 19. Linha SANTA TEREZA x CASCAVEL Tabela de Horários, acessado em janeiro 12,

#### 2026,

#### https://expressosantatereza.com.br/wp-content/uploads/TABELAS-SANTA-TEREZ

#### A-01-07-2024.pdf

#### 20. Lista Fones Secretarias - Prefeitura de {client_name} do oeste, acessado em

#### janeiro 12, 2026,

#### https://www.santatereza.pr.gov.br/pagina/530_Lista-Fones-Secretarias.html

#### 21. Confira as vagas de emprego disponíveis na Agência do Trabalhador nesta

#### quinta-Feira(21) - Acontece Na Fronteira, acessado em janeiro 12, 2026,

#### https://acontecenafronteira.com.br/index.php/2024/11/21/confira-as-vagas-de-e

#### mprego-disponiveis-na-agencia-do-trabalhador-nesta-quinta-feira21/

#### 22. refis 2025 - Prefeitura de {client_name} do oeste, acessado em janeiro 12, 2026,

#### https://www.santatereza.pr.gov.br/noticiasView/?id=

#### 23. Emissor de Nota Fiscal {client_name} - GestãoClick, acessado em

#### janeiro 12, 2026,

#### https://gestaoclick.com.br/nota-fiscal-eletronica-santa-tereza-do-oeste/

#### 24. Sala do Empreendedor - Prefeitura de {client_name} do oeste, acessado em

#### janeiro 12, 2026,

#### https://www.santatereza.pr.gov.br/pagina/556_Sala-do-Empreendedor.html

#### 25. ENVELOPE N.º 2 (HABILITAÇÃO) MUNICíPIO DE MERCEDES - ESTADO DO

#### PARANÁ, acessado em janeiro 12, 2026,

#### https://www.mercedes.pr.gov.br/arquivos/licitacoes_anexos/2021/10/HABILITACA

#### O_PREGAO_124_2021.pdf

#### 26. Prefeitura de {client_name} do oeste, acessado em janeiro 12, 2026,

#### https://www.santatereza.pr.gov.br/

#### 27. estado do paraná - Prefeitura Municipal de Bandeirantes, acessado em janeiro 12,

#### 2026,

#### https://www.bandeirantes.pr.gov.br/public/admin/globalarq/licitacao/arquivo/cda

#### 976d226986c7813138b7fe6fa4e5.pdf


