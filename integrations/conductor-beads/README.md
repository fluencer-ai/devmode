# Integração devmode × Conductor-Beads

**devmode é a base; Conductor é a camada por cima; Beads é memória opcional.**

```
   Beads        ← memória opcional atrás do Conductor (sobrevive à compactação)
 ┌──────────┐
 │Conductor │   ← CAMADA: organiza e persiste o trabalho (tracks, spec/plan, ciclo)
 ├──────────┤
 │ devmode  │   ← BASE: como pensar, desenhar e testar (fonte de verdade)
 └──────────┘
```

- **devmode** (base) responde *"como pensar e desenhar para a IA produzir código bom"*.
- **Conductor** (camada) responde *"como organizar o trabalho em tracks/spec/plan"*.
- **Beads** (memória) responde *"como lembrar tudo entre sessões"*.

Tire o Conductor e você ainda tem um projeto devmode completo. Tire o devmode e o
Conductor vira só um PM spec-first genérico. **Quando os defaults da camada
conflitam com a base, a base vence** — e os skills do devmode **não foram
modificados** (continuam o núcleo agnóstico de ferramenta). Toda a fiação vive
aqui, na casca.

## O que tem aqui

| Arquivo | Para quê |
|---------|----------|
| `INTEGRATION.md` | O **mapa**: cada skill do devmode → fase do Conductor → ação do Beads. Leia primeiro. |
| `agents/devmode-orchestrator.md` | O **orquestrador**: conduz todo o processo fase a fase, pausando só nos gates de decisão. |
| `commands/devmode.md` | O slash-command **`/devmode`** — a porta de entrada do modo guiado. |
| `hooks/guardrails.py` (+ teste) | **Guardrails (gates-as-code)**: hook PreToolUse determinístico que bloqueia operações perigosas. Opcional (`--with-guardrails`). |
| `install.sh` | Bootstrap: estabelece a **base devmode** e monta a **camada Conductor** num projeto real. |
| `templates/CLAUDE.md` | O **CLAUDE.md de projeto**: declara devmode como base e Conductor como camada. É o que torna o devmode a fundação. |
| `templates/workflow.md` | Adaptador do ciclo de tarefa (defere aos skills do devmode): TDD + FCIS + gray boxes + princípios de teste (substitui a meta de ">80% cobertura"). |
| `templates/track/spec.md` | Spec do track com o rigor de módulos/interfaces do `write-prd`. |
| `templates/track/plan.md` | Plano em fases (núcleo → casca → críticos), anotável p/ Beads e execução paralela. |
| `templates/track/learnings.md` | Diário de aprendizados do track (flywheel Ralph); deltas de domínio voltam p/ a linguagem ubíqua. |
| `templates/product.md`, `tech-stack.md`, `tracks.md`, `patterns.md` | Contexto do projeto, devmode-aware. |
| `templates/UBIQUITOUS_LANGUAGE.md` | Glossário + **mapa de módulos** (o devmode trata o mapa como parte da linguagem). |
| `templates/beads.json` | Config do Beads. |

## Como testar em um projeto real

Por padrão o instalador **estabelece a base devmode** (CLAUDE.md + skills +
agentes + referências + linguagem ubíqua) e depois **monta a camada Conductor**.

### Opção A — base + camada + comandos + memória (completa)
```bash
cd /Users/gabrielsorrentino/Projects/devmode/integrations/conductor-beads
./install.sh /caminho/do/projeto --with-conductor --beads-stealth
```

### Opção B — base devmode local + camada Conductor (sem Beads)
```bash
./install.sh /caminho/do/projeto
```

### Opção C — base global (não copia skills) + camada Conductor + memória
```bash
./install.sh /caminho/do/projeto --no-skills --beads-stealth
```

Flags:

| Flag | Efeito |
|------|--------|
| *(padrão)* | Copia a base devmode (CLAUDE.md, skills, agentes, referências) para `<projeto>/.claude/` + raiz. |
| `--no-skills` | **Não** copia skills/agentes/referências (usa um devmode instalado globalmente). O CLAUDE.md base ainda é escrito. |
| `--with-conductor` | Clona o Conductor-Beads e copia seus slash-commands + skills `conductor`/`beads`. Pule se já estiverem globais. |
| `--with-guardrails` | Instala o hook determinístico de guardrails (gates-as-code) e o liga no `.claude/settings.json`. |
| `--beads` / `--beads-stealth` | Roda `bd init` (normal / local-only). |
| `--force` | Sobrescreve arquivos escritos por este instalador. |

O script é **idempotente**: não sobrescreve nada sem `--force`. Se o projeto já
tem um `CLAUDE.md`, a base é escrita em `CLAUDE.devmode.md` para você mesclar
(ou adicionar `@CLAUDE.devmode.md`).

## Pré-requisitos e custos honestos

- **Beads é opcional.** Sem ele, todo o fluxo devmode + Conductor funciona — você
  perde só o grafo persistente e a sobrevivência à compactação. (`enabled:false`
  em `beads.json` ou simplesmente não rode `bd init`.)
- **Beads CLI:** `npm i -g @beads/bd` (ou brew/go). O bd ≥ 1.0 usa **Dolt embutido**
  por padrão — `bd init` funciona sozinho, sem servidor para subir. (Só o modo
  opcional `--server` precisa de um `dolt sql-server` externo.) Verificado no bd
  1.0.3: `bd init --stealth` inicializou limpo, sem servidor separado.
- Os skills `conductor`/`beads`/`conductor-*` podem **já existir globalmente** no
  seu ambiente; nesse caso não use `--with-conductor`.

## O jeito mais fácil: modo guiado

```bash
/devmode "o que você quer construir"
```
O agente **`devmode-orchestrator`** conduz todas as fases (ALINHAR → LINGUAGEM →
ESPECIFICAR → ARQUITETAR → IMPLEMENTAR → REVIEW → REFATORAR), faz todo o trabalho
mecânico e **pausa só nos seus gates de decisão** (como escolhas A/B/C com
recomendação). Você é *levado pelo processo*, mas continua decidindo a estratégia.

## O fluxo combinado (o que o orquestrador faz por baixo)

1. `/conductor-setup` + `bd init` → contexto + memória.
2. **`grill-me` ANTES** de criar o track (alinhar o conceito de design).
3. `/conductor-newtrack` → `spec.md` com rigor de módulos/interfaces (`write-prd`).
4. `/conductor-implement` → loop TDD do `workflow.md` (FCIS, gray boxes,
   princípios de teste, feedback loops).
5. Verificação de fase → `feedback-loops` + agente `complexity-reviewer`.
6. `/conductor-handoff` → o Beads guarda **o conceito de design + deltas da
   linguagem ubíqua**, não só o status.
7. `improve-codebase-architecture` no `refresh`/`archive` para conter entropia.

Detalhes completos: [`INTEGRATION.md`](INTEGRATION.md).
