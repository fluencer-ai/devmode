# Manual do devmode — programar de forma estruturada na era da IA

> Um guia prático, em português, para usar este conjunto de skills e agentes
> e desenvolver software com a IA sem cair na armadilha do "specs-to-code".

Este manual ensina **como usar** o processo que está nesta pasta. Se quiser
entender o *porquê* de cada peça, leia [`references/foundations.md`](references/foundations.md).
Se algo estiver dando errado e você não souber qual skill usar, vá direto para
[`references/failure-modes.md`](references/failure-modes.md).

---

## 1. A ideia central (leia isto primeiro)

Existe um mito de que, na era da IA, **"código é barato"**: bastaria escrever uma
especificação, gerar o código e nunca mais olhar para ele. Na prática isso
fracassa — você recompila e o código fica *pior* a cada rodada. A tese do devmode
é o oposto:

> **Código não é barato. Código ruim é a coisa mais cara que existe hoje.**
> Uma base de código difícil de mudar impede a IA de entregar seu valor.

A divisão de papéis que sustenta tudo:

- **A IA é a tática** — um excelente programador "no chão de fábrica", rápido e
  preciso, mas **sem estratégia**.
- **Você é a estratégia** — o conceito de design compartilhado, as fronteiras de
  módulo, as interfaces e o investimento contínuo no design.

O processo inteiro existe para fornecer à IA a estratégia que ela não tem.
**Nunca deixe a tática definir a direção.**

---

## 2. O mapa do conjunto

Dentro de `devmode/` você tem quatro tipos de peça:

| Peça | O que é | Onde fica |
|------|---------|-----------|
| **39 skills** | 20 de *processo* + 16 de *domínio* + 3 *meta* (`self-scorecard`, `discovery`, `goal-brief`) | `skills/<nome>/SKILL.md` |
| **8 agentes** | Subagentes que encarnam papéis do processo (inclui o painel de review) | `.agents/*.md` |
| **2 referências** | Fundamentos teóricos e guia de diagnóstico | `references/*.md` |
| **templates + script** | Modelos (PRD, glossário) + auditor da pack (`scripts/audit_skills.py`) | `skills/*/assets/`, `scripts/` |

E o [`CLAUDE.md`](CLAUDE.md) amarra tudo: é o manifesto + a tabela do fluxo.
Várias skills foram **adaptadas** de projetos MIT — créditos em
[`ATTRIBUTION.md`](ATTRIBUTION.md).

### As 20 skills de processo, agrupadas por fase

```
1. ALINHAR      grill-me ............... conceito de design compartilhado (+ taxonomia de falhas, opções A/B/C)
2. LINGUAGEM    ubiquitous-language .... vocabulário único + mapa de módulos (+ why por dependência)
3. ESPECIFICAR  write-prd .............. PRD explícito sobre módulos e interfaces
                design-critique ........ revisar o design/PRD por várias lentes antes de codar
4. ARQUITETAR   functional-core-imperative-shell . separar lógica pura de I/O (nível módulo)
                architecture-boundaries .......... fronteiras de sistema (regras vs. infraestrutura)
                design-interface-delegate-impl. .. desenhar interface, delegar implementação
                design-patterns .................. padrões GoF — só quando aprofundam o módulo
5. IMPLEMENTAR  confidence-check ....... gate de prontidão ANTES de codar
                feedback-loops ......... tipos, compilador, testes, browser + escada de gates
                tdd .................... passos pequenos test-first
                testing-principles ..... o que/como/quanto testar (+ anti-padrões)
                subagent-driven-dev .... delegar a subagentes c/ revisão em 2 estágios
                delegate-to-cli ........ delegar a uma CLI externa (gray box)
                systematic-debugging ... causa-raiz antes de qualquer correção
                verification-before-completion . evidência antes de dizer "pronto"
                code-review ............ painel de review → agir nos achados → re-verificar
6. REFATORAR    impact-analysis ........ raio de explosão (quem depende) antes de mexer
                improve-codebase-architecture .... consolidar módulos rasos em profundos

META            authoring-skills ....... escrever/auditar as próprias skills (scripts/audit_skills.py)
```

### Pares que se apoiam

O processo tem duplas projetadas para se reforçar:

- **`functional-core-imperative-shell` ↔ `testing-principles`** — a arquitetura
  (núcleo puro / casca) torna o código fácil de testar; os princípios dizem
  *onde* colocar o limite.
- **`functional-core-imperative-shell` ↔ `architecture-boundaries`** — o mesmo
  instinto em duas escalas: módulo e sistema.
- **`tdd` ↔ `feedback-loops`** — o ritmo (vermelho-verde-refatora) e a
  infraestrutura (tipos, testes, browser, escada de gates) que o sustenta.
- **`design-interface-delegate-implementation` ↔ `subagent-driven-development` /
  `delegate-to-cli`** — a *estratégia* e o *como* da delegação gray-box.
- **`systematic-debugging` ↔ `verification-before-completion`** — achar a
  causa-raiz e depois *provar* que a correção funcionou antes de concluir.
- **`confidence-check` ↔ `verification-before-completion`** — os dois portões:
  prontidão *antes* de começar e evidência *depois* de terminar.
- **`code-review` ↔ `verification-before-completion`** — o painel acha os
  buracos; cada correção é *re-verificada* antes de fechar (loop achar→corrigir→provar).

### As 16 skills de domínio (craft cross-cutting)

Não são fases — são *expertise* que os agentes puxam **durante** as fases:

- **Front-end & design:** `frontend-ui-engineering` (UI de produção, fuga da
  "estética de IA"), `ux-design` (tokens, hierarquia, estados), `accessibility`
  (WCAG 2.1 AA).
- **Interfaces & qualidade:** `api-design` (contratos, Hyrum, validar na
  fronteira), `security-hardening` (OWASP, Always/Ask/Never), `performance-optimization`
  (medir antes), `browser-testing` (verificar no browser; conteúdo = dado não-confiável).
- **Ops & entrega:** `ci-cd-automation` (gate automático), `git-workflow`,
  `migration` (strangler/expand-contract), `shipping` (rollout + rollback).
- **Práticas:** `documentation` (ADRs, o *porquê*), `doc-contracts` (árvore de
  AGENTS.md — contratos locais por área, lidos antes de editar e atualizados no
  mesmo commit), `prototyping` (spike descartável → captura → deleta),
  `context-engineering`, `source-of-truth` (checar versão/docs, não a memória).

Importadas de `addyosmani/agent-skills` (MIT), generalizadas para a base
tool-agnostic; `ux-design`/`accessibility` foram **escritas** para preencher a
lacuna de design; `doc-contracts` adaptada de `agent0ai/dox` (MIT); `prototyping`
adaptada de `mattpocock/skills` (MIT — o projeto-irmão do devmode). A meta de
cobertura cega foi reconciliada com a base.

---

## 3. Como invocar as skills na prática

Estas skills são "modos de trabalho". Há duas formas de usá-las:

1. **Deixe a IA disparar sozinha.** Cada skill tem uma `description` que diz
   *quando* ela deve ser usada. Quando você descreve uma tarefa que casa com
   isso ("quero construir X", "me entreviste sobre isso", "esses testes estão
   frágeis"), a IA reconhece e segue a skill.
2. **Peça explicitamente.** Diga, por exemplo: *"use a skill grill-me comigo"*,
   *"escreva o PRD desta feature"*, *"vamos fazer isso com TDD"*. Você também
   pode abrir o `SKILL.md` correspondente e ler o método para conduzir você
   mesmo.

> Dica: mantenha o glossário de linguagem ubíqua (`UBIQUITOUS_LANGUAGE.md`)
> **aberto** enquanto planeja. É o hábito que mais reduz verbosidade e desvio.

---

## 4. O fluxo de ponta a ponta

Vá de cima para baixo. **Nem toda mudança precisa de todas as fases** — uma
correção pequena pode pular direto para o TDD. Mas esta é a espinha do processo.

### Fase 1 — Alinhar (`grill-me`)
**Objetivo:** chegar a um *conceito de design compartilhado* antes de criar
qualquer documento ou código.

A IA vai te **entrevistar sem dó** — dezenas de perguntas — caminhando por cada
ramo da "árvore de design" e resolvendo as dependências entre decisões, uma a
uma. Ela vai te devolver resumos do entendimento para você corrigir. **Não deixe
ela escrever o PRD ainda.** O resultado desta fase é alinhamento, não documento.

> Por que importa: a maior fonte de retrabalho é a IA construir algo diferente do
> que estava na sua cabeça. Ninguém sabe exatamente o que quer até ser obrigado a
> articular.

### Fase 2 — Linguagem (`ubiquitous-language`)
**Objetivo:** um vocabulário único usado igual na conversa, no raciocínio da IA e
no código.

A IA escaneia a base de código, extrai os termos de domínio e monta um
`UBIQUITOUS_LANGUAGE.md` (a partir do
[`template`](skills/ubiquitous-language/assets/glossary-template.md)). A coluna
**"In code as"** é o que torna a linguagem *ubíqua*: cada termo aponta para o
tipo/módulo/função que o representa.

> O glossário **não é só de termos de domínio**: ele também carrega o **mapa de
> módulos** (os módulos profundos e suas interfaces públicas). Você e a IA
> precisam conhecer esse mapa bem — uma fronteira de módulo é um conceito de
> domínio, com nome, responsabilidade e contrato. É esse mapa que permite ao PRD
> ser específico sobre *quais módulos e interfaces mudam*.

### Fase 3 — Especificar (`write-prd`)
**Objetivo:** transformar o conceito alinhado num PRD escrito na linguagem ubíqua.

O coração do PRD **não** é a lista de funcionalidades — é a seção de **mudanças de
módulos e interfaces**: assinaturas, tipos, fronteiras reais. É aqui que você
*investe no design do sistema* (Kent Beck). Use o
[`template de PRD`](skills/write-prd/assets/prd-template.md).

### Fase 4 — Arquitetar
**Objetivo:** definir a estrutura antes de implementar.

- **`functional-core-imperative-shell`** — separe a *lógica de decisão pura* (o
  núcleo: sem I/O, determinístico) da *casca imperativa fina* (lê entradas, chama
  o núcleo, executa efeitos). Padrão: **a casca coleta → o núcleo decide → a casca
  age**. Isso torna o núcleo trivial de testar sem mocks.
- **`design-interface-delegate-implementation`** — desenhe **você** a interface
  (o "contrato"), com cuidado, e **delegue a implementação** à IA como uma
  *gray box* (caixa cinza): você verifica por fora, pelos testes, sem ler cada
  linha. Exceção: módulos **críticos** (dinheiro, autenticação, segurança) você
  revisa por completo.

### Fase 5 — Implementar
**Objetivo:** transformar contratos em código funcionando e testado.

- **`feedback-loops`** — garanta que existam e sejam *rápidos*: tipos estáticos,
  compilador/linter, testes automatizados rápidos e, para frontend, **acesso a um
  browser real** para a IA ver o resultado. *A taxa de feedback é seu limite de
  velocidade.*
- **`tdd`** — vermelho (escreva um teste que falha) → verde (faça passar com o
  mínimo) → refatora (melhore o design com o teste te protegendo). **Um
  comportamento por vez.**
- **`testing-principles`** — decida bem: testar no **limite estável mais
  profundo** (não cada função privada); **mockar só o que você não controla**
  (rede, relógio, disco, terceiros); asseverar **comportamento**, não
  implementação.

### Fase 6 — Refatorar (`improve-codebase-architecture`)
**Objetivo:** combater a entropia consolidando **módulos rasos** (muitos blocos
pequenos, interface complexa, vazando internals) em **módulos profundos** (muita
funcionalidade atrás de uma interface simples). Faça isso *antes* da complexidade
se acumular — e sempre com os testes verdes.

---

## 5. Os agentes (quando delegar a um subagente)

Quando uma fase é grande o bastante para merecer um contexto próprio, delegue ao
agente correspondente (em `.agents/`):

| Agente | Papel | Use quando |
|--------|-------|-----------|
| **`requirements-planner`** | Grila, monta a linguagem ubíqua e escreve o PRD | Início de uma feature não-trivial |
| **`design-architect`** | Dono das interfaces, fronteiras e do split núcleo/casca | Ao decidir *como* construir |
| **`tdd-implementer`** | O programador tático: testa primeiro, passos pequenos | Implementação atrás de um contrato fixo |
| **`architecture-refactorer`** | Consolida módulos rasos em profundos | Base espalhada/difícil de navegar |
| **`complexity-reviewer`** | Guarda da entropia: revisa o diff por complexidade e lidera o painel | Antes de fazer merge |
| **`code-quality-analyzer`** · **`security-scanner`** · **`test-coverage-analyzer`** | Painel de review: lanes especializadas (qualidade, segurança, lacunas de teste) em paralelo | Após implementar, antes do merge |

---

## 6. Guia rápido de diagnóstico

Está travado? Case o sintoma com a skill (versão resumida de
[`references/failure-modes.md`](references/failure-modes.md)):

| Sintoma | Skill |
|---------|-------|
| "A IA não fez o que eu queria" | `grill-me` |
| "A IA é verbosa demais / desvia do plano" | `ubiquitous-language` |
| "Construiu certo, mas não funciona" | `feedback-loops` + `tdd` |
| "Está quebrado / o teste falha / não sei por quê" | `systematic-debugging` |
| "Disse que estava pronto, mas não estava" | `verification-before-completion` |
| "A IA faz coisa demais de uma vez" | `tdd` |
| "Os testes são frágeis/lentos/sem sentido" | `testing-principles` |
| "Testar exige mock de tudo" | `functional-core-imperative-shell` |
| "A IA se perde no código / mudança quebra coisas distantes" | `improve-codebase-architecture` |
| "O que quebra se eu mexer aqui? / é seguro remover?" | `impact-analysis` |
| "Não sei se estou pronto pra começar a codar" | `confidence-check` |
| "Esse design tem buracos? / o que estamos esquecendo?" | `design-critique` |
| "Está pronto pra mergear? / o que eu (autor) não estou vendo?" | `code-review` |
| "Mudança espirra em arquivos não relacionados / lógica colada à infra" | `architecture-boundaries` |
| "Meu cérebro não acompanha o volume de código" | `design-interface-delegate-implementation` + `subagent-driven-development` |

> Regra de ouro do diagnóstico: se você briga sempre com um sintoma *tardio*,
> suspeite de uma causa *anterior* não resolvida. Teste frágil (5) costuma ser, na
> verdade, arquitetura emaranhada (6/7); "não funciona" (3) costuma ser falta de
> alinhamento (1/2).

---

## 7. Exemplo completo: renovar uma assinatura

Vamos do zero ao código numa feature pequena, mostrando o processo inteiro.

**1) Alinhar (`grill-me`).** A IA te entrevista: *"O que acontece se o cartão
falha? Quantas tentativas? Renova no vencimento ou antes? Cobra por assento? O que
acontece com assinatura cancelada?"* Você responde, ela reflete o conceito de
volta, vocês concordam.

**2) Linguagem (`ubiquitous-language`).** Vira glossário:

| Termo | Definição | In code as | Invariante |
|-------|-----------|-----------|-----------|
| Assinatura | Acesso pago contínuo a um plano | `Subscription` | Tem exatamente um `Plan` ativo |
| Assento | Uma licença atribuível na assinatura | `Seat` | É `assigned` ou `free`, nunca os dois |
| Renovação | Cobrança que estende o período | `decideRenewal` | Só ocorre após o vencimento |

**3) Especificar (`write-prd`).** Na seção de interfaces:
`decideRenewal(sub, currentTime) -> Decision` (núcleo puro), chamado só pela
casca; `BillingGateway.charge(...)` é I/O e fica na casca.

**4) Arquitetar (`functional-core-imperative-shell`).** A casca coleta → o núcleo
decide → a casca age:

```js
// NÚCLEO (puro): decide o que deve acontecer — testável sem mocks
function decideRenewal(sub, currentTime) {
  if (sub.status !== "active") return { kind: "noop" }
  if (currentTime <= sub.endsAt) return { kind: "noop" }
  return {
    kind: "renew",
    charge: { customer: sub.customer, amount: sub.plan.price * sub.seats },
    newEndsAt: addMonth(currentTime),
  }
}

// CASCA (imperativa): coleta entradas, roda o núcleo, executa a decisão
function renewSubscription(id) {
  const sub = db.load(id)
  const decision = decideRenewal(sub, now())
  if (decision.kind === "noop") return
  payments.charge(decision.charge.customer, decision.charge.amount)
  db.save({ ...sub, endsAt: decision.newEndsAt })
}
```

**5) Implementar (`tdd` + `testing-principles` + `feedback-loops`).** Cada caso de
borda do `decideRenewal` vira uma asserção de uma linha, **sem mock** (inativo,
ainda não venceu, venceu, múltiplos assentos). A casca ganha 1–2 testes de
integração. Tipos e testes rodam em segundos a cada passo.

**6) Decidir revisão (`design-interface-delegate-implementation`).** Como envolve
**dinheiro**, este módulo é crítico → você revisa a implementação por inteiro (não
é gray box).

**7) Refatorar / revisar.** Se a lógica de cobrança estiver espalhada, o
`architecture-refactorer` consolida; o `complexity-reviewer` confere o diff antes
do merge.

---

## 8. Hábitos e regras de ouro

- **Alinhe antes de escrever qualquer asset.** O conceito de design vem primeiro.
- **Mantenha o glossário aberto** e use os mesmos termos na conversa, no PRD, nos
  testes e no código.
- **Seja específico sobre interfaces no PRD** — assinaturas e tipos reais, não
  "criar um serviço para X".
- **Um teste que falha por vez.** Veja-o falhar antes de fazê-lo passar. Nunca
  deixe a suíte vermelha "para depois".
- **Mocke só o que você não controla.** Mockar a própria lógica é sinal de
  fronteira errada → aplique núcleo/casca.
- **Caixa cinza só com testes que a prendam.** Sem cobertura, você ainda não tem o
  direito de parar de ler o módulo. Módulos críticos nunca são caixas cinza.
- **Se um teste dói de escrever, é sinal de design** — refatore a arquitetura
  antes de empilhar mocks.
- **Invista no design todos os dias.** Cada mudança é chance de melhorar o design,
  não só de adicionar funcionalidade.
- **Você é a estratégia; a IA é a tática.**

---

## 9. Escalando para trabalho longo: Conductor-Beads

### Modos do `/devmode`, score e dashboard

- **`/devmode start <nome> <ideia>`** — cria `workspaces/<nome>` (base+camada+guardrails+Beads), `git init`, e começa pela Fase 1.
- **`/devmode adopt <pasta>`** — implanta o devmode num **projeto existente** e roda **discovery** (skill `discovery`, estilo reversa): varre o código, detecta stack, monta o **mapa de módulos** + glossário em `UBIQUITOUS_LANGUAGE.md` e um `DISCOVERY.md` (conceito de design provisório + arquitetura), com tags 🟢/🟡/🔴 — e a fase ALIGN ataca os 🔴 com você. Se a pasta já tem `CLAUDE.md`, ele é **preservado byte-a-byte** — o instalador só acrescenta um ponteiro idempotente `@CLAUDE.devmode.md` (composição via import nativo; suas instruções continuam o host e têm precedência). Nada de reescrever; merge num arquivo só é opcional, se você pedir.
- **`/devmode goal <objetivo>`** (opt-in) — gera um comando **`/goal` pronto** (≤3800 chars) que referencia o `spec.md` em detalhe (passo-a-passo + testes + critérios de aceite), com o limite **garantido por script** (`.devmode/goal_brief.py`). Use `plan <objetivo>` para um `/plan` (planejar o goal — a recursão `/plan ↔ /goal`). O devmode **não executa o `/goal` sozinho** (um agente não dispara slash-command); ele **te entrega o comando** para você rodar a cada iteração. Não fica embutido no fluxo normal — só quando você pede.
- **`/devmode <ideia>`** — guia/retoma no projeto atual.
- **`/devmode do <tarefa>`** — para **uma tarefa só** (não um projeto): roteia a
  frase para a(s) skill(s)+agente certos e roda um pipeline curto com gates de
  evidência (Entender → Planejar → Executar → Verificar → Entregar). É o irmão de
  tarefa única do `/devmode` (projeto inteiro) e do `/devmode c` (gates por turno);
  **todo comando começa com `/devmode`**, reusando as skills/agentes/gates
  existentes — sem máquina nova. (Conceito adaptado do `/do` do
  `notque/vexjoy-agent`, MIT.)

> **Retomada morna (SessionStart).** Com `--with-guardrails`, um hook
> `session_resume.py` injeta no início de cada sessão um resumo curto (última
> fase, score, track ativo, próxima ação) lido do `.devmode/scorecard.json` —
> read-only, fail-open. Assim uma sessão nova **continua de onde o loop parou**
> em vez de começar do zero (padrão do `notque/claude-code-starter-kit`, MIT).

Em **toda fase**, o orquestrador mostra um **score** (skill `self-scorecard`): resumo do que foi feito + nota 0–10 em 5 critérios (Correctness, Design, Testing, Safety, Clarity) com deltas (`.devmode/scorecard.py`), e atualiza um **dashboard visual** (`.devmode/dashboard.py` → `devmode-dashboard.html`, sem servidor nem registro). O dashboard traz uma **faixa de KPIs**, uma **esteira do workflow** (as fases Align→Refactor, alcançadas/atual), um **timeline por fase**, um **sparkline** da tendência de score, e um **painel de Gates** alimentado por `.devmode/gates.json` (emitido por um `ci/check.sh`). No fim, `--final` dá **recomendações por critério**. O dashboard é **zero-setup,
sem servidor nem registro** — basta abrir o `devmode-dashboard.html`.

Os 39 skills e 8 agentes são a **base agnóstica de ferramenta** — funcionam
sozinhos. Mas quando o trabalho dura muitas sessões, falta ao devmode uma espinha
de **orquestração** (tracks, status, dependências) e de **memória persistente**
(que sobrevive à compactação da conversa). É aí que entra a integração:

> **devmode é a base; Conductor é a camada por cima; Beads é a memória opcional.**

A hierarquia é deliberada — o Conductor **serve** o fluxo devmode, não o
substitui. Tire o Conductor e você ainda tem um projeto devmode completo; tire o
devmode e o Conductor vira um PM spec-first genérico. **Quando os defaults da
camada conflitam com a base, a base vence.** A fiação fica isolada em
`integrations/conductor-beads/` (a casca), sem tocar nos skills da base.

Para testar em um projeto real (a base devmode é instalada por padrão):

```bash
cd integrations/conductor-beads
./install.sh /caminho/do/projeto --beads-stealth
```

O fluxo combinado: `/conductor-setup` + `bd init` → **`grill-me` antes** do
`/conductor-newtrack` → spec com rigor de módulos/interfaces → `/conductor-implement`
seguindo o `workflow.md` devmode (TDD + FCIS + gray boxes + princípios de teste,
**sem** meta cega de cobertura) → handoff guarda o *conceito de design* nas notas
do Beads, não só o status. Detalhes:
[`integrations/conductor-beads/INTEGRATION.md`](integrations/conductor-beads/INTEGRATION.md).

> O Beads é **opcional**: sem ele o fluxo devmode + Conductor funciona igual, só
> sem o grafo persistente. Custo baixo no bd ≥ 1.0: usa **Dolt embutido** por
> padrão — `bd init` funciona sem servidor (verificado no bd 1.0.3).

### Modo guiado (`/devmode`) — ser levado pelo processo

Se você não quer pensar em *qual* skill usar e *quando*, use o orquestrador:

```bash
/devmode "o que você quer construir"
```

O agente **`devmode-orchestrator`** (instalado pelo `install.sh`) conduz todas as
fases — ALINHAR → LINGUAGEM → ESPECIFICAR → ARQUITETAR → IMPLEMENTAR → REVIEW →
REFATORAR — fazendo todo o trabalho mecânico e **pausando só nos seus gates de
decisão**, que ele apresenta como escolhas A/B/C com recomendação. A regra de
ouro: você é **levado pelo *processo*, mas continua decidindo a *estratégia*** (o
conceito de design, os trade-offs, aprovar a interface, dizer "pronto"). Ele é um
*condutor fino* — delega às skills profundas, nunca as reimplementa. Detalhes:
[`INTEGRATION.md`](integrations/conductor-beads/INTEGRATION.md) → "Guided mode".

## 10. Para aprofundar

- [`CLAUDE.md`](CLAUDE.md) — manifesto e tabela do fluxo.
- [`references/foundations.md`](references/foundations.md) — os princípios e a
  lista de leitura (Ousterhout, Brooks, Beck, Evans, Hunt & Thomas, Bernhardt).
- [`references/failure-modes.md`](references/failure-modes.md) — diagnóstico
  completo sintoma → skill.
- Os próprios `SKILL.md` em `skills/` — cada um explica o método e o porquê.
