#!/usr/bin/env python3
"""
SEO Agent — YouTube → Blog Post (Hotmart format)
Uso: python agent.py [youtube_url | caminho.docx]
"""

import os
import sys
import subprocess

# Carrega .env antes de qualquer verificação de chave
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def _load_api_key():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return

    try:
        result = subprocess.run(
            ["security", "find-generic-password", "-s", "Claude Safe Storage", "-a", "Claude Key", "-w"],
            capture_output=True, text=True, timeout=5
        )
        raw = result.stdout.strip()
        if raw and raw.startswith("sk-ant-"):
            os.environ["ANTHROPIC_API_KEY"] = raw
            return
    except Exception:
        pass

    print("\n⚠️  ANTHROPIC_API_KEY não encontrada no ambiente.")
    print("   1. export ANTHROPIC_API_KEY=sk-ant-...")
    print("   2. Crie um arquivo .env com ANTHROPIC_API_KEY=sk-ant-...")
    key = input("\n   Cole sua API key agora (ou Enter para cancelar): ").strip()
    if key.startswith("sk-ant-"):
        os.environ["ANTHROPIC_API_KEY"] = key
    else:
        print("❌  API key inválida ou não fornecida. Encerrando.")
        sys.exit(1)


_load_api_key()

from modules import transcript, sitemap, keywords, writer, utils


def _read_docx(path: str) -> str:
    try:
        from docx import Document
    except ImportError:
        print("❌  python-docx não instalado. Rode: pip3 install python-docx")
        sys.exit(1)

    doc = Document(path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paragraphs)


def _get_transcript_text(lang: str) -> str:
    """Pergunta o tipo de input e retorna o texto da transcrição."""

    input_type = utils.ask_choice(
        "Qual é a fonte do conteúdo?",
        ["URL do YouTube", "Arquivo .docx (roteiro)", "Texto / transcrição (colar)"]
    )

    if input_type == "URL do YouTube":
        if len(sys.argv) > 1:
            url = sys.argv[1].strip()
            print(f"\n🎬  URL: {url}")
        else:
            url = input("\n🎬  Cole a URL do YouTube: ").strip()
        if not url:
            print("URL não pode ser vazia."); sys.exit(1)

        print("\n⏳  Buscando transcrição...")
        text = transcript.get(url, lang)
        if not text:
            print("❌  Não foi possível obter a transcrição. Verifique se o vídeo tem legendas ativas.")
            sys.exit(1)
        print(f"✅  Transcrição obtida ({len(text.split())} palavras)")
        return text

    elif input_type == "Arquivo .docx (roteiro)":
        path = input("\n📄  Caminho do arquivo .docx: ").strip().strip("'\"")
        if not os.path.exists(path):
            print(f"❌  Arquivo não encontrado: {path}"); sys.exit(1)
        print("\n⏳  Lendo arquivo...")
        text = _read_docx(path)
        if not text:
            print("❌  O arquivo está vazio ou não tem texto legível."); sys.exit(1)
        print(f"✅  Roteiro lido ({len(text.split())} palavras)")
        return text

    else:  # texto corrido
        print("\n📝  Cole o texto (transcrição ou roteiro).")
        print("   Quando terminar, pressione Enter em uma linha vazia:\n")
        lines = []
        while True:
            try:
                line = input()
            except EOFError:
                break
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        text = "\n".join(lines).strip()
        if not text:
            print("❌  Nenhum texto fornecido."); sys.exit(1)
        print(f"✅  Texto recebido ({len(text.split())} palavras)")
        return text


def _build_metadata_comment(outline: dict, kw_data: dict) -> str:
    sec_kws = ", ".join(kw_data.get("secondary", []))
    slug = outline.get("slug", "")
    blog_base = "https://hotmart.com/pt-br/blog"
    return (
        f"<!--\n"
        f"  URL             : {blog_base}/{slug}\n"
        f"  Slug            : /{slug}\n"
        f"  Meta title      : {outline.get('meta_title', '')}\n"
        f"  Meta description: {outline.get('meta_description', '')}\n"
        f"  Keyword principal: {kw_data.get('main', '')}\n"
        f"  Keywords secundárias: {sec_kws}\n"
        f"-->\n"
    )


def main():
    utils.banner()

    lang = utils.ask_choice(
        "Idioma do conteúdo (e do post)?",
        ["pt-br", "es"]
    )

    transcript_text = _get_transcript_text(lang)

    print("\n🔍  Carregando posts publicados para checagem de duplicação...")
    published_posts = sitemap.load(lang)
    print(f"✅  {len(published_posts)} posts carregados do sitemap")

    # ── Keywords primeiro ──────────────────────────────────────────────────────
    use_ahrefs = utils.ask_yes_no("\n🔑  Buscar palavras-chave via Ahrefs API?")

    if use_ahrefs:
        topic_hint = input("  Tema central do conteúdo (para busca no Ahrefs): ").strip()
        kw_data = keywords.from_ahrefs(topic_hint, lang)
    else:
        print("\nDigite as palavras-chave (Enter para pular):")
        main_kw = input("  Palavra-chave principal: ").strip()
        sec_kws = input("  Palavras-chave secundárias (separadas por vírgula): ").strip()
        intent  = input("  Intenção de busca (informacional/comercial/transacional): ").strip()
        kw_data = keywords.from_manual(main_kw, sec_kws, intent)

    print(f"\n✅  Palavras-chave: {kw_data['main']} + {len(kw_data['secondary'])} secundárias")

    # ── Ângulos informados pelas keywords ──────────────────────────────────────
    print("\n🧠  Analisando conteúdo e sugerindo ângulos...")
    angles = writer.suggest_angles(transcript_text, published_posts, lang, kw_data)

    print("\n" + "─"*60)
    print("📐  ÂNGULOS SUGERIDOS:\n")
    for i, angle in enumerate(angles, 1):
        print(f"  {i}. {angle['title']}")
        print(f"     {angle.get('preview', '')}")
        print(f"     → {angle.get('rationale', '')}\n")

    angle_input = input("Digite o número do ângulo (ou escreva o seu): ").strip()

    if angle_input.isdigit() and 1 <= int(angle_input) <= len(angles):
        angle_description = angles[int(angle_input) - 1]['title']
    else:
        angle_description = angle_input

    print(f"\n✅  Ângulo definido: {angle_description}")

    # ── Outline ────────────────────────────────────────────────────────────────
    print("\n📋  Gerando estrutura do post...")
    outline = writer.generate_outline(transcript_text, angle_description, kw_data, published_posts, lang)

    print("\n" + "─"*60)
    print("📄  ESTRUTURA PROPOSTA:\n")
    print(f"  Slug      : /{outline.get('slug', '')}")
    print(f"  Meta Title: {outline.get('meta_title', '')}")
    print(f"  Meta Desc : {outline.get('meta_description', '')}")
    print(f"  H1        : {outline.get('h1', '')}")
    print(f"\n  Seções:")
    for i, h2 in enumerate(outline.get('h2s', []), 1):
        print(f"    {i}. {h2['title']}")
        for h3 in h2.get('h3s', []):
            print(f"       • {h3}")

    print("\n" + "─"*60)
    proceed = utils.ask_yes_no("\n✏️   Aprovar estrutura e gerar o post completo?")

    if not proceed:
        print("\n💬  O que ajustar na estrutura?")
        feedback = input("  > ").strip()
        outline = writer.revise_outline(outline, feedback, lang)
        print(f"\n✅  Estrutura revisada.")

    # ── Redação ────────────────────────────────────────────────────────────────
    print("\n✍️   Redigindo o post completo (1-2 minutos)...\n")
    post_html = writer.write_post(transcript_text, outline, kw_data, lang)

    word_count = len(post_html.replace('<', ' <').split())
    print(f"\n✅  Post gerado com ~{word_count} palavras")

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{outline.get('slug', 'post')}.html"

    metadata_comment = _build_metadata_comment(outline, kw_data)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(metadata_comment + post_html)

    print("\n" + "─"*60)
    print(f"📁  Arquivo: {filename}")
    print(f"🔗  Slug:    /{outline.get('slug', '')}")
    print(f"🏷️   Title:   {outline.get('meta_title', '')}")
    print(f"📝  Desc:    {outline.get('meta_description', '')[:80]}...")
    print("─"*60)
    print("🎉  Pronto! Cole o HTML no seu CMS.")
    print("─"*60 + "\n")


if __name__ == "__main__":
    main()
