# SEO Agent — YouTube → Blog Post

Transforma vídeos do YouTube em posts de blog prontos para o CMS da Hotmart.

**O que o agente faz:**
1. Lê a transcrição completa do vídeo
2. Carrega os posts publicados (sitemap PT-BR e ES) para evitar duplicação
3. Sugere 5 ângulos editoriais baseados no conteúdo e lacunas do blog
4. Pesquisa palavras-chave via Ahrefs API (ou aceita input manual)
5. Gera outline com slug, meta title, meta description, H1 e H2s
6. Você aprova (ou ajusta) a estrutura antes de escrever
7. Redige o post completo (+2.500 palavras) no formato HTML do blog

---

## Instalação (5 minutos)

### Pré-requisitos
- Python 3.10 ou superior ([download](https://www.python.org/downloads/))
- Git ([download](https://git-scm.com/))

### 1. Clone o repositório
```bash
git clone https://github.com/SEU-ORG/seo-agent.git
cd seo-agent
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

> Se tiver múltiplas versões de Python, use `pip3` ou `python3 -m pip install -r requirements.txt`

### 3. Configure suas API keys
```bash
cp .env.example .env
```

Abra o arquivo `.env` em qualquer editor de texto e preencha:

```
ANTHROPIC_API_KEY=sk-ant-...    ← obrigatório (https://console.anthropic.com/keys)
AHREFS_API_TOKEN=...            ← opcional (só se quiser usar Ahrefs automático)
```

> **Nunca compartilhe o arquivo `.env`.** Ele está no `.gitignore` e não vai para o Git.

---

## Como usar

```bash
python agent.py
```

O agente vai guiar você passo a passo pelo terminal.

### Fluxo completo

```
🎬 Cole a URL do YouTube
   ↓
🌐 Escolha o idioma (pt-br / es)
   ↓
🔍 Agente carrega posts publicados (anti-duplicação automática)
   ↓
🧠 Agente sugere 5 ângulos editoriais → você escolhe
   ↓
🔑 Ahrefs API automático OU você digita as keywords
   ↓
📋 Agente gera outline → você aprova ou ajusta
   ↓
✍️  Agente escreve o post completo (+2500 palavras)
   ↓
📁 HTML salvo em output/SLUG-DO-POST.html
```

### Output

O arquivo gerado em `output/` contém HTML pronto para colar no CMS:
- `[post_index]` com âncoras para navegação
- H2s com `id="t1"`, `id="t2"`...
- `<strong>`, `<em>`, `<ul>`, `<ol>` sem classes
- Links internos sugeridos
- `[hotmart_faq][/hotmart_faq]` no final

---

## Usando no Claude Code

Se você usa o [Claude Code](https://claude.ai/code), pode abrir a pasta do projeto e pedir ao Claude para rodar o agente ou modificar módulos:

```
# No terminal do Claude Code
python agent.py
```

---

## Usando no VSCode

1. Abra a pasta `seo-agent` no VSCode
2. Abra o terminal integrado (`Ctrl+` `)
3. `python agent.py`

---

## Estrutura do projeto

```
seo-agent/
├── agent.py              ← ponto de entrada principal
├── modules/
│   ├── transcript.py     ← busca transcrição do YouTube
│   ├── sitemap.py        ← lê sitemap PT-BR e ES (anti-duplicação)
│   ├── keywords.py       ← Ahrefs API + fallback manual
│   ├── writer.py         ← toda a lógica de IA (Claude)
│   └── utils.py          ← helpers de CLI
├── output/               ← posts gerados (criado automaticamente)
├── .env                  ← suas API keys (não vai pro Git)
├── .env.example          ← template das keys
├── requirements.txt      ← dependências Python
└── README.md
```

---

## Requisitos das APIs

| API | Necessária? | Onde obter |
|-----|-------------|------------|
| Anthropic (Claude) | **Sim** | [console.anthropic.com](https://console.anthropic.com/keys) |
| Ahrefs | Opcional | [ahrefs.com/api](https://ahrefs.com/api) — plano Standard+ |

---

## Problemas comuns

**"Não foi possível obter a transcrição"**
→ O vídeo precisa ter legendas ativas (automáticas ou manuais). Vídeos muito curtos ou sem fala podem não ter.

**"ANTHROPIC_API_KEY não encontrado"**
→ Verifique se o arquivo `.env` existe na pasta raiz e se a key está preenchida.

**Sitemap retornou 0 posts**
→ O sitemap pode estar temporariamente inacessível. O agente continua funcionando, só sem checagem de duplicação.

---

## Roadmap futuro

- [ ] Publicação direta via API do WordPress
- [ ] Interface web (Streamlit ou FastAPI)
- [ ] Cache de sitemaps para não rebuscar a cada run
- [ ] Suporte a múltiplos blogs / domínios
- [ ] Histórico de posts gerados com score de qualidade
