---
name: seo-youtube
description: >
  Transforma vídeo do YouTube, roteiro em DOCX ou texto colado em post de blog SEO
  otimizado para o blog da Hotmart. Integra com o KWS Research skill para pesquisa
  real de keywords via Ahrefs. Gera HTML completo com estrutura H1/H2/H3, índice,
  meta title, meta description, FAQ e comentário com metadados para o CMS.
  Use quando o usuário quiser criar um post de blog a partir de um vídeo, roteiro
  ou transcrição. Gatilhos: "cria um post", "transforma esse vídeo em post",
  "gera blog post", "seo youtube", "post do youtube", "converte roteiro em post",
  "escreve post a partir de transcrição", "blog post hotmart".
---

# SEO YouTube Skill

Transforma conteúdo em vídeo (YouTube), roteiro (DOCX) ou transcrição em texto
em um post de blog SEO completo no formato da Hotmart.

## Fluxo de Uso

A skill é interativa. Ao executar, faz as seguintes perguntas:

1. **Idioma** — pt-br ou es
2. **Fonte do conteúdo** — URL do YouTube, arquivo .docx ou texto colado
3. **Keywords** — pesquisa via Ahrefs (KWS Research) ou entrada manual
4. **Ângulo editorial** — escolha entre 2-3 sugestões geradas pelo agente
5. **Aprovação da estrutura** — revisa H1, H2s, slug, meta tags antes de redigir

## Como Executar

```bash
cd ~/Claude\ -\ Youtube\ Agent
python3 agent.py

# Ou passando a URL direto:
python3 agent.py https://www.youtube.com/watch?v=VIDEO_ID
```

## O que a Skill Faz

### Fontes de conteúdo suportadas
- **URL do YouTube** — busca transcrição via `youtube-transcript-api` (com cache local)
- **Arquivo .docx** — lê roteiro com `python-docx`
- **Texto colado** — aceita transcrição ou roteiro em texto corrido

### Etapas do agente
1. **Keywords** — chama `kws_research.py` com `--output json`, exibe top 15 por TP, usuário escolhe KW principal; secundárias são puxadas do mesmo cluster automaticamente
2. **Ângulos** — Claude sugere 2-3 opções com preview e racional, considerando posts já publicados no sitemap
3. **Outline** — Claude gera estrutura completa (slug, meta, H1, H2s, H3s, FAQ topics)
4. **Redação** — Claude redige o post completo em HTML (+2500 palavras)
5. **Output** — salva em `output/<slug>.html` com comentário de metadados no topo

### Integração com KWS Research
O passo de keywords delega para `~/Claude - KWS Research/scripts/kws_research.py`.
Qualquer melhoria no `/seo-keyword` skill reflete automaticamente aqui.

## Output Esperado

```html
<!--
  URL             : https://hotmart.com/pt-br/blog/slug-do-post
  Slug            : /slug-do-post
  Meta title      : Título SEO até 60 chars
  Meta description: Descrição até 155 chars
  Keyword principal: keyword principal
  Keywords secundárias: kw2, kw3, kw4
-->
[post_index]...[/post_index]
<h1>Título do post</h1>
<p>Introdução...</p>
...
[hotmart_faq][/hotmart_faq]
```

## Dependências

```
anthropic>=0.30.0
youtube-transcript-api>=0.6.2
python-dotenv>=1.0.0
python-docx>=1.1.0
```

Instalar: `pip3 install -r requirements.txt`

## Repositório

https://github.com/fernandasnel/seo-youtube-skill
