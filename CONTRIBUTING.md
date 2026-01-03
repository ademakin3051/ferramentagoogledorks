# 🤝 Guia de Contribuição

Obrigado por considerar contribuir com o **Google Dork Scanner**! Este documento fornece diretrizes para contribuir com o projeto.

## 📋 Índice

- [Código de Conduta](#código-de-conduta)
- [Como Contribuir](#como-contribuir)
- [Sugerindo Melhorias](#sugerindo-melhorias)
- [Pull Requests](#pull-requests)
- [Padrões de Código](#padrões-de-código)
- [Adicionando Dorks](#adicionando-dorks)

---

## 📜 Código de Conduta

Este projeto segue um código de conduta simples:

- ✅ Seja respeitoso com outros contribuidores
- ✅ Use linguagem inclusiva
- ✅ Aceite críticas construtivas
- ✅ Foque no que é melhor para a comunidade
- ❌ Não use a ferramenta para fins maliciosos
- ❌ Não compartilhe resultados de scans não autorizados

---

## 🚀 Como Contribuir

### 1. Fork o Repositório

```bash
# Clone seu fork
git clone https://github.com/ademakin3051/google-dork-scanner.git
cd google-dork-scanner
```

### 2. Crie uma Branch

```bash
# Para features
git checkout -b feature/minha-feature

# Para bugfixes
git checkout -b fix/meu-bugfix

# Para documentação
git checkout -b docs/minha-doc
```

### 3. Faça suas Alterações

```bash
# Edite os arquivos necessários
# Teste suas alterações
python3 dork_scanner_v3.py
```

### 4. Commit suas Mudanças

```bash
git add .
git commit -m "feat: adiciona nova funcionalidade X"
```

**Padrão de commits:**
- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `style:` Formatação
- `refactor:` Refatoração
- `test:` Testes
- `chore:` Manutenção

### 5. Push e Pull Request

```bash
git push origin feature/minha-feature
```

Depois, abra um Pull Request no GitHub.


## 💡 Sugerindo Melhorias

Para sugerir melhorias:

1. Verifique se já não foi sugerido
2. Descreva claramente a melhoria
3. Explique por que seria útil

### Template de Feature Request

```markdown
**Descrição da Feature**
Uma descrição clara da funcionalidade.

**Problema que Resolve**
Qual problema esta feature resolve?

**Solução Proposta**
Como você imagina que deveria funcionar?

**Alternativas Consideradas**
Outras soluções que você considerou.

**Contexto Adicional**
Qualquer outra informação relevante.
```

---

## 🔄 Pull Requests

### Checklist antes de submeter:

- [ ] Código testado localmente
- [ ] Código segue os padrões do projeto
- [ ] Documentação atualizada (se necessário)
- [ ] Commits com mensagens descritivas
- [ ] Branch atualizada com a main

### Template de Pull Request

```markdown
**Descrição**
O que este PR faz?

**Tipo de Mudança**
- [ ] Bug fix
- [ ] Nova feature
- [ ] Documentação
- [ ] Refatoração

**Testes Realizados**
Como você testou?

**Screenshots**
Se aplicável.

**Checklist**
- [ ] Testei localmente
- [ ] Atualizei a documentação
- [ ] Meus commits seguem o padrão
```

---

## 📝 Padrões de Código

### Python

```python
# Use docstrings em funções
def minha_funcao(parametro):
    """
    Descrição breve da função.
    
    Args:
        parametro: Descrição do parâmetro
        
    Returns:
        Descrição do retorno
    """
    pass

# Use type hints quando possível
def soma(a: int, b: int) -> int:
    return a + b

# Nomes descritivos em português ou inglês (consistente)
nome_da_variavel = "valor"  # snake_case

# Constantes em maiúsculas
MAX_TENTATIVAS = 3

# Classes em PascalCase
class MinhaClasse:
    pass
```

### Formatação

- Indentação: 4 espaços
- Linha máxima: 100 caracteres
- Encoding: UTF-8

---

## 🔍 Adicionando Dorks

Para adicionar novos dorks ao banco de dados:

### 1. Edite o arquivo `dorks_database.json`

```json
{
  "dork_categories": {
    "nova_categoria": {
      "description": "Descrição da categoria",
      "dorks": [
        "site:{domain} seu_novo_dork",
        "site:{domain} outro_dork"
      ]
    }
  }
}
```

### 2. Regras para Dorks

- ✅ Sempre use `site:{domain}` no início
- ✅ Teste o dork manualmente antes
- ✅ Evite dorks duplicados
- ✅ Agrupe em categorias apropriadas
- ❌ Não adicione dorks maliciosos

### 3. Categorias Existentes

- `paineis_admin` - Painéis administrativos
- `arquivos_sensiveis` - Arquivos com dados sensíveis
- `diretorios_expostos` - Listagem de diretórios
- `paginas_login` - Páginas de autenticação
- `erros_debug` - Mensagens de erro
- `arquivos_configuracao` - Arquivos de config
- `banco_dados` - Banco de dados expostos
- `arquivos_backup` - Backups
- `documentos_sensiveis` - Documentos confidenciais
- `git_controle_versao` - Repositórios expostos
- `apis_chaves` - APIs e chaves
- `wordpress` - Específicos para WP
- `custom_dorks` - Dorks personalizados

---

## 🎯 Áreas que Precisam de Ajuda

- [ ] Melhorar cobertura de testes
- [ ] Adicionar suporte a múltiplos domínios
- [ ] Criar interface web
- [ ] Adicionar mais categorias de dorks
- [ ] Melhorar documentação
- [ ] Traduzir para outros idiomas

---

## ❓ Dúvidas?

Se tiver dúvidas:

1. Verifique a [documentação](README.md)
2. Procure nas [Issues](https://github.com/ademakin3051/google-dork-scanner/issues)
3. Abra uma nova Issue com a tag `question`

---

**Obrigado por contribuir! 🙏**
