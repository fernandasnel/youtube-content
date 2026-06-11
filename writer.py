"""
modules/writer.py
Cérebro do agente. Usa a API da Anthropic para:
  1. Sugerir ângulos editoriais
  2. Gerar outline SEO
  3. Revisar outline com feedback
  4. Escrever o post completo no formato HTML da Hotmart
"""

import os
import json
import re
import anthropic

MODEL = "claude-sonnet-4-20250514"
client = None


def _get_client() -> anthropic.Anthropic:
    global client
    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise EnvironmentError("ANTHROPIC_API_KEY não encontrado no .env")
        client = anthropic.Anthropic(api_key=api_key)
    return client


def _call(system: str, user: str, max_tokens: int = 2000) -> str:
    c = _get_client()
    msg = c.messages.create(
        model=MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


# ── 1. Sugestão de ângulos ─────────────────────────────────────────────────────

def suggest_angles(transcript_text: str, published_posts: list[dict], lang: str) -> list[dict]:
    lang_label = "português brasileiro" if lang == "pt-br" else "espanhol"

    published_slugs = "\n".join(f"- {p['slug']}" for p in published_posts[:80])

    system = f"""Você é um estrategista de conteúdo SEO sênior especializado em negócios digitais.
Seu objetivo é identificar ângulos editoriais únicos para posts de blog em {lang_label}.
Sempre retorne JSON válido, sem markdown, sem texto extra."""

    user = f"""Analise esta transcrição de vídeo do YouTube e sugira 5 ângulos editoriais para um blog post.

TRANSCRIÇÃO (primeiros 3000 caracteres):
{transcript_text[:3000]}

POSTS JÁ PUBLICADOS NO BLOG (evite duplicar esses tópicos):
{published_slugs or "Nenhum disponível"}

Retorne EXATAMENTE este JSON:
{{
  "angles": [
    {{
      "title": "título do ângulo em {lang_label}",
      "rationale": "por que este ângulo é estratégico (1 frase)",
      "target_audience": "quem se beneficia deste post",
      "unique_value": "o que diferencia dos posts existentes"
    }}
  ]
}}"""

    raw = _call(system, user, max_tokens=1500)

    try:
        data = json.loads(_clean_json(raw))
        return data.get("angles", [])
    except Exception:
        # Fallback se JSON quebrar
        return [{"title": "Ângulo extraído do vídeo", "rationale": "Baseado no conteúdo do vídeo"}]


# ── 2. Geração de outline ──────────────────────────────────────────────────────

def generate_outline(
    transcript_text: str,
    angle: str,
    kw_data: dict,
    published_posts: list[dict],
    lang: str,
) -> dict:
    lang_label = "português brasileiro" if lang == "pt-br" else "espanhol"
    domain = "hotmart.com/pt-br/blog" if lang == "pt-br" else "hotmart.com/es/blog"

    user = f"""Crie um outline completo para um blog post SEO em {lang_label}.

ÂNGULO EDITORIAL: {angle}
PALAVRA-CHAVE PRINCIPAL: {kw_data['main']}
PALAVRAS-CHAVE SECUNDÁRIAS: {', '.join(kw_data['secondary'])}
INTENÇÃO DE BUSCA: {kw_data['intent']}

TRANSCRIÇÃO DO VÍDEO (resumo dos primeiros 4000 caracteres):
{transcript_text[:4000]}

Retorne EXATAMENTE este JSON:
{{
  "slug": "url-amigavel-com-hifens",
  "meta_title": "título SEO até 60 caracteres com KW principal",
  "meta_description": "descrição até 155 caracteres atraente com KW",
  "h1": "título principal do post com KW",
  "intro_hook": "primeira frase de abertura do post (gancho)",
  "h2s": [
    {{
      "title": "título do H2",
      "h3s": ["título H3 se necessário", "outro H3"],
      "key_points": ["ponto principal que deve constar nesta seção"]
    }}
  ],
  "internal_links_suggestion": ["slug-de-post-existente-para-linkar"],
  "faq_topics": ["pergunta frequente 1", "pergunta frequente 2"]
}}

Gere entre 5 e 7 H2s. O post deve ter potencial para mais de 2500 palavras."""

    system = f"""Você é um especialista em SEO técnico e estratégia de conteúdo.
Crie outlines otimizados para ranquear no Google para o domínio {domain}.
Retorne apenas JSON válido, sem markdown, sem texto extra."""

    raw = _call(system, user, max_tokens=2000)

    try:
        return json.loads(_clean_json(raw))
    except Exception as e:
        raise ValueError(f"Erro ao parsear outline: {e}\nResposta: {raw[:500]}")


# ── 3. Revisão de outline ──────────────────────────────────────────────────────

def revise_outline(outline: dict, feedback: str, lang: str) -> dict:
    lang_label = "português brasileiro" if lang == "pt-br" else "espanhol"

    system = f"""Você é um especialista em SEO. Revise o outline abaixo com base no feedback.
Retorne apenas o JSON do outline revisado, sem texto extra."""

    user = f"""Outline atual:
{json.dumps(outline, ensure_ascii=False, indent=2)}

Feedback do editor:
{feedback}

Retorne o outline revisado no mesmo formato JSON."""

    raw = _call(system, user, max_tokens=2000)
    try:
        return json.loads(_clean_json(raw))
    except Exception:
        return outline  # Retorna original se falhar


# ── 4. Redação do post completo ────────────────────────────────────────────────

def write_post(transcript_text: str, outline: dict, kw_data: dict, lang: str) -> str:
    lang_label = "português brasileiro" if lang == "pt-br" else "espanhol"
    blog_domain = "https://hotmart.com/pt-br/blog" if lang == "pt-br" else "https://hotmart.com/es/blog"

    h2s_text = "\n".join(
        f"- H2: {h['title']}\n  Pontos: {', '.join(h.get('key_points', []))}"
        for h in outline.get("h2s", [])
    )

    system = f"""Você é um redator sênior de conteúdo SEO, especializado em negócios digitais e criação de infoprodutos.
Escreva posts de blog de alta qualidade em {lang_label} para o blog da Hotmart.

REGRAS DE FORMATO (siga à risca):
- Use HTML limpo, sem classes CSS, sem atributos desnecessários
- Parágrafos: texto puro (sem tag <p>, use quebras duplas entre parágrafos)
- Títulos: <h2>Título</h2> e <h3>Subtítulo</h3>
- Negrito: <strong>texto</strong> para termos importantes
- Itálico: <em>texto</em> para exemplos e citações
- Listas não ordenadas: <ul><li>item</li></ul>
- Listas ordenadas: <ol><li>item</li></ol>
- Links internos: <a href="URL_COMPLETA">texto âncora</a>
- Shortcode de índice no topo: [post_index]<a href="#t1">Título seção 1</a>...[/post_index]
- IDs de âncora nos H2s: <h2 id="t1">Título</h2>
- Shortcode de FAQ no final: [hotmart_faq][/hotmart_faq]
- NÃO inclua <html>, <head>, <body> nem <p> tags
- O post deve ter MAIS DE 2500 palavras
- Tom: direto, prático, autoritativo, sem jargão acadêmico"""

    user = f"""Escreva o post completo com base nestas informações:

H1: {outline['h1']}
META DESCRIPTION: {outline['meta_description']}
GANCHO DE ABERTURA: {outline.get('intro_hook', '')}

PALAVRA-CHAVE PRINCIPAL: {kw_data['main']}
PALAVRAS-CHAVE SECUNDÁRIAS: {', '.join(kw_data['secondary'])}

ESTRUTURA:
{h2s_text}

SUGESTÕES DE LINKS INTERNOS (use quando relevante):
{chr(10).join(f"- {blog_domain}/{s}" for s in outline.get('internal_links_suggestion', []))}

TRANSCRIÇÃO DO VÍDEO (use como fonte de insights, dados e exemplos):
{transcript_text[:6000]}

INSTRUÇÕES:
1. Comece com [post_index] com links âncora para cada H2
2. Escreva a introdução usando o gancho fornecido (2-3 parágrafos)
3. Desenvolva cada H2 com profundidade — mínimo 3 parágrafos por seção
4. Use <strong> para termos-chave na primeira ocorrência
5. Inclua pelo menos 2 exemplos práticos por H2 quando relevante
6. A KW principal deve aparecer no primeiro parágrafo, em H2s e naturalmente no texto
7. Termine com uma conclusão acionável e o shortcode [hotmart_faq][/hotmart_faq]
8. Tom: {lang_label}, prático, sem enrolação

Escreva o post COMPLETO agora:"""

    return _call(system, user, max_tokens=8000)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _clean_json(text: str) -> str:
    """Remove markdown code fences e texto extra antes/depois do JSON."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    # Encontra o JSON entre { } ou [ ]
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    return match.group(1) if match else text
