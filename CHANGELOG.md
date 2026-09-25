# 📋 Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [3.1.0] - 2026-09-25

### 🐛 Corrigido
- **Bug crítico:** buscas sem resultado eram contadas como *erro* e falhas de API como *"sem resultados"*. Agora há status explícitos (`FOUND`, `EMPTY`, `ERROR`, `QUOTA`).
- Base de dorks agora é carregada pelo caminho absoluto do script (funcionava só a partir da pasta do projeto).
- `except:` genéricos substituídos por exceções específicas com mensagem.
- Normalização de domínio via regex (o `replace('www.','')` removia "www." do meio do texto).
- Máscara da API Key mostra apenas os últimos 4 caracteres.
- Suporte a Windows (`cls`/`clear`).

### ✨ Adicionado
- **Interface com `rich`** (tabelas, barra de progresso, painéis) com fallback em texto puro.
- **Modo linha de comando** (`argparse`): `-d`, `--api`, `--api-key`, `-f`, `-o`, `-w`, `--gl`, `--hl`, `--open`.
- **API Key** via env `SERPER_API_KEY` ou argumento, além da config salva.
- **Relatórios em HTML, JSON, CSV e TXT** (antes só TXT).
- **HTML clicável** no modo manual.
- **Severidade por categoria** (crítico → baixo); resultados ordenados por severidade.
- **Seleção de categorias** no modo interativo (economiza créditos da API).
- **Busca paralela** (`ThreadPoolExecutor`) com parada automática ao esgotar a cota.
- **Testes** (`pytest`) e lint (`ruff`); `requirements.txt` e `pyproject.toml`.

### 🔄 Alterado
- Base de dorks: 8 duplicatas removidas (178 → **170 dorks**).

---

## [3.0.0] - 2025-01-02

### 🎉 Lançamento Major - Totalmente Remodelado

### ✨ Adicionado
- **Modo Manual** com links clicáveis no terminal
- **Modo Serper.dev API** com busca automática
- **Dashboard com KPIs** para visualização de resultados
- **Salvamento automático da API Key** em `~/.dork_scanner_config.json`
- **Relatórios inteligentes** que salvam apenas resultados válidos
- **167 dorks** organizados em 20 categorias
- **Interface colorida** com suporte ANSI
- **Barra de progresso** visual durante scans
- **Agrupamento por categoria** nos resultados

### 🔄 Alterado
- Simplificação para apenas 2 modos de operação
- Interface completamente redesenhada
- Melhor organização do código em classes

### 🗑️ Removido
- Modos antigos complexos
- Dependências externas desnecessárias
- Código legado

### 🔒 Segurança
- API Key salva com permissões 600
- Aviso legal obrigatório antes do scan

---

## [2.0.0] - 2024-XX-XX

### ✨ Adicionado
- Múltiplos modos de operação
- Suporte a diferentes APIs

### 🐛 Corrigido
- Problemas de encoding
- Erros de conexão

---

## [1.0.0] - 2024-XX-XX

### 🎉 Lançamento Inicial
- Scanner básico de dorks
- Interface de linha de comando
- Lista inicial de dorks

---

## Tipos de Mudanças

- `✨ Adicionado` para novas funcionalidades
- `🔄 Alterado` para mudanças em funcionalidades existentes
- `⚠️ Deprecado` para funcionalidades que serão removidas
- `🗑️ Removido` para funcionalidades removidas
- `🐛 Corrigido` para correções de bugs
- `🔒 Segurança` para vulnerabilidades corrigidas

---

## Links

- [Comparar versões](https://github.com/ademakin3051/google-dork-scanner/compare)
- [Releases](https://github.com/ademakin3051/google-dork-scanner/releases)
