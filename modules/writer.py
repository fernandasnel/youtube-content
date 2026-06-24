"""
modules/writer.py
Cérebro do agente. Usa a API da Anthropic para:
  1. Sugerir ângulos editoriais (2-3, informados por keywords + sitemap)
  2. Gerar outline SEO
  3. Revisar outline com feedback
  4. Escrever o post completo no formato HTML da Hotmart
"""

import os
import json
import re
import datetime
import anthropic

MODEL = "claude-sonnet-4-6"
client = None


def _get_client() -> anthropic.Anthropic:
    global client
    if client is None:
        client = anthropic.Anthropic()
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


def _current_year() -> int:
    return datetime.datetime.now().year


# ── 1. Sugestão de ângulos ─────────────────────────────────────────────────────

def suggest_angles(transcript_text: str, published_posts: list, lang: str, kw_data: dict) -> list:
    lang_label = "português brasileiro" if lang == "pt-br" else "espanhol"
    year = _current_year()

    published_slugs = "\n".join(f"- {p['slug']}" for p in published_posts[:80])
    sec_kws = ", ".join(kw_data.get("secondary", []))

    system = f"""Você é um estrategista de conteúdo SEO sênior especializado em negócios digitais.
Seu objetivo é propor ângulos editoriais únicos para posts de blog em {lang_label}.
Sempre retorne JSON válido, sem markdown, sem texto extra."""

    user = f"""Analise a transcrição abaixo e proponha 2 a 3 ângulos editoriais para um blog post.

ANO ATUAL: {year}

PALAVRA-CHAVE PRINCIPAL: {kw_data['main']}
PALAVRAS-CHAVE SECUNDÁRIAS: {sec_kws or "não definidas"}
INTENÇÃO DE BUSCA: {kw_data.get('intent', 'informacional')}

TRANSCRIÇÃO (primeiros 3000 caracteres):
{transcript_text[:3000]}

POSTS JÁ PUBLICADOS NO BLOG (evite temas já cobertos):
{published_slugs or "Nenhum disponível"}

Para cada ângulo, forneça:
- Um título de post (sentence case: só primeira letra maiúscula + nomes próprios/marcas)
- Um parágrafo curto descrevendo o que o post vai abordar (2-3 frases, como se fosse o lead)
- Um racional de 1 frase explicando por que este ângulo e não outros (mencione se evita duplicar algo do sitemap ou aproveita lacuna de busca)

Retorne EXATAMENTE este JSON:
{{
  "angles": [
    {{
      "title": "título do post em sentence case",
      "preview": "parágrafo curto de 2-3 frases descrevendo o que o post vai abordar",
      "rationale": "por que este ângulo é a melhor oportunidade agora (1 frase)"
    }}
  ]
}}"""

    raw = _call(system, user, max_tokens=1500)

    try:
        data = json.loads(_clean_json(raw))
        return data.get("angles", [])
    except Exception:
        return [{"title": "Ângulo extraído do vídeo", "preview": "", "rationale": "Baseado no conteúdo do vídeo"}]


# ── 2. Geração de outline ──────────────────────────────────────────────────────

def generate_outline(
    transcript_text: str,
    angle: str,
    kw_data: dict,
    published_posts: list,
    lang: str,
) -> dict:
    lang_label = "português brasileiro" if lang == "pt-br" else "espanhol"
    domain = "hotmart.com/pt-br/blog" if lang == "pt-br" else "hotmart.com/es/blog"
    year = _current_year()

    user = f"""Crie um outline completo para um blog post SEO em {lang_label}.

ANO ATUAL: {year}
ÂNGULO EDITORIAL: {angle}
PALAVRA-CHAVE PRINCIPAL: {kw_data['main']}
PALAVRAS-CHAVE SECUNDÁRIAS: {', '.join(kw_data['secondary'])}
INTENÇÃO DE BUSCA: {kw_data['intent']}

TRANSCRIÇÃO DO VÍDEO (primeiros 4000 caracteres):
{transcript_text[:4000]}

REGRAS DE CAPITALIZAÇÃO:
- Títulos e subtítulos em sentence case: apenas primeira letra maiúscula + nomes próprios e marcas registradas
- Exemplos corretos: "Como criar seu primeiro produto digital", "Guia completo para iniciantes em {year}"
- Exemplos errados: "Como Criar Seu Primeiro Produto Digital", "GUIA COMPLETO"

Retorne EXATAMENTE este JSON:
{{
  "slug": "url-amigavel-com-hifens",
  "meta_title": "título SEO até 60 caracteres com KW principal (sentence case)",
  "meta_description": "descrição até 155 caracteres atraente com KW",
  "h1": "título principal do post com KW (sentence case)",
  "intro_hook": "primeira frase de abertura do post (gancho)",
  "h2s": [
    {{
      "title": "título do H2 em sentence case",
      "h3s": ["título H3 em sentence case se necessário"],
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

    raw = _call(system, user, max_tokens=4000)

    try:
        return json.loads(_clean_json(raw))
    except Exception as e:
        raise ValueError(f"Erro ao parsear outline: {e}\nResposta: {raw[:500]}")


# ── 3. Revisão de outline ──────────────────────────────────────────────────────

def revise_outline(outline: dict, feedback: str, lang: str) -> dict:
    system = """Você é um especialista em SEO. Revise o outline abaixo com base no feedback.
Mantenha títulos em sentence case (só primeira letra maiúscula + nomes próprios/marcas).
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
        return outline


# ── 4. Redação do post completo ────────────────────────────────────────────────

def write_post(transcript_text: str, outline: dict, kw_data: dict, lang: str) -> str:
    lang_label = "português brasileiro" if lang == "pt-br" else "espanhol"
    blog_domain = "https://hotmart.com/pt-br/blog" if lang == "pt-br" else "https://hotmart.com/es/blog"
    year = _current_year()

    h2s_text = "\n".join(
        f"- H2: {h['title']}\n  Pontos: {', '.join(h.get('key_points', []))}"
        for h in outline.get("h2s", [])
    )

    system = f"""Você é um redator sênior de conteúdo SEO da Hotmart, especializado em negócios digitais e criação de infoprodutos.
Escreva posts de blog em {lang_label} fiéis ao tom de voz da Hotmart e ao conteúdo do vídeo de origem.
O ano atual é {year}.

TOM DE VOZ HOTMART (siga sempre):
- Parceiro, não professor. Use "a gente", "vamos", "você". Oriente e celebre conquistas
- Direto ao ponto: sem enrolação, sem papo corporativo. Comece pelo que importa
- Leveza e charme: humor sagaz quando cabe, mas nunca forçado
- Fale de dinheiro com orgulho e clareza: números reais, sem promessas vagas
- Vocabulário: prefira "a gente", "bora", "vender mais" — evite "potencializar", "alavancar", "ecossistema sinérgico", "maximizar"

FIDELIDADE AO CONTEÚDO:
- Use APENAS informações, dados e exemplos presentes na transcrição do vídeo
- NÃO invente estatísticas, cases ou exemplos que não estejam na transcrição
- Se o vídeo não der material suficiente para 2500 palavras, escreva o quanto for possível com qualidade — não estique artificialmente
- Preserve a narrativa e os dados exatos mencionados (ex: "1.722 placas black em 2025", "CPM saltou de R$5,3 para R$96,71")

REGRAS DE FORMATO (siga à risca):
- Use HTML limpo, sem classes CSS, sem atributos desnecessários
- Parágrafos curtos: máximo 3 linhas cada. Priorize quebras de linha para facilitar leitura mobile
- Nunca junte mais de 3 frases em um mesmo bloco de texto corrido
- Títulos: <h2>Título</h2> e <h3>Subtítulo</h3>
- Títulos em sentence case: apenas primeira letra maiúscula + nomes próprios e marcas
- Negrito: <strong>texto</strong> para termos importantes
- Listas não ordenadas: <ul><li>item</li></ul>
- Listas ordenadas: <ol><li>item</li></ol>
- Links internos: <a href="URL_COMPLETA">texto âncora</a>
- Shortcode de índice no topo: [post_index]<a href="#t1">Título seção 1</a>...[/post_index]
- IDs de âncora nos H2s: <h2 id="t1">Título</h2>
- Shortcode de FAQ no final: [hotmart_faq][/hotmart_faq]
- NÃO inclua <html>, <head>, <body> nem <p> tags
- PROIBIDO: travessão (—). Substitua por vírgula, ponto e vírgula ou reescreva a frase
- PROIBIDO: títulos com todas as palavras em maiúsculo (Title Case)"""

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

TRANSCRIÇÃO DO VÍDEO (fonte exclusiva de dados, exemplos e narrativa):
{transcript_text[:6000]}

INSTRUÇÕES:
1. Comece com [post_index] com links âncora para cada H2
2. Escreva a introdução usando o gancho fornecido (2-3 parágrafos curtos)
3. Desenvolva cada H2 com profundidade usando APENAS o que está na transcrição
4. Parágrafos curtos: máximo 3 linhas. Use listas quando for enumerar mais de 2 itens
5. Use <strong> para termos-chave na primeira ocorrência
6. A KW principal deve aparecer no primeiro parágrafo, em H2s e naturalmente no texto
7. Termine com uma conclusão acionável e o shortcode [hotmart_faq][/hotmart_faq]
8. NÃO use travessão (—) em nenhum momento
9. Todos os títulos H2 e H3 em sentence case
10. Se o conteúdo do vídeo não sustentar 2500 palavras, escreva o máximo possível com qualidade

Escreva o post COMPLETO agora:"""

    return _call(system, user, max_tokens=8000)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _clean_json(text: str) -> str:
    """Remove markdown code fences e texto extra antes/depois do JSON."""
    text = re.sub(r"```(?:json)?", "", text).strip()
    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    return match.group(1) if match else text
