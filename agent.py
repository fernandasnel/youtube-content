#!/usr/bin/env python3
"""
SEO Agent — YouTube → Blog Post (Hotmart format)
Uso: python agent.py
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from modules import transcript, sitemap, keywords, writer, utils

def main():
    utils.banner()

    yt_url = input("\n🎬  Cole a URL do YouTube: ").strip()
    if not yt_url:
        print("URL não pode ser vazia."); sys.exit(1)

    lang = utils.ask_choice(
        "Idioma do vídeo (e do post)?",
        ["pt-br", "es"]
    )

    print("\n⏳  Buscando transcrição...")
    transcript_text = transcript.get(yt_url, lang)
    if not transcript_text:
        print("❌  Não foi possível obter a transcrição. Verifique se o vídeo tem legendas ativas.")
        sys.exit(1)
    print(f"✅  Transcrição obtida ({len(transcript_text.split())} palavras)")

    print("\n🔍  Carregando posts publicados para checagem de duplicação...")
    published_posts = sitemap.load(lang)
    print(f"✅  {len(published_posts)} posts carregados do sitemap")

    print("\n🧠  Analisando transcrição e sugerindo ângulos...")
    angles = writer.suggest_angles(transcript_text, published_posts, lang)

    print("\n" + "─"*60)
    print("📐  ÂNGULOS SUGERIDOS (escolha um ou descreva o seu):\n")
    for i, angle in enumerate(angles, 1):
        print(f"  {i}. {angle['title']}")
        print(f"     → {angle.get('rationale', '')}\n")

    angle_input = input("Digite o número do ângulo escolhido (ou escreva o seu): ").strip()

    if angle_input.isdigit() and 1 <= int(angle_input) <= len(angles):
        angle_description = angles[int(angle_input) - 1]['title']
    else:
        angle_description = angle_input

    print(f"\n✅  Ângulo definido: {angle_description}")

    use_ahrefs = utils.ask_yes_no("\n🔑  Buscar palavras-chave via Ahrefs API?")

    if use_ahrefs:
        kw_data = keywords.from_ahrefs(angle_description, lang)
    else:
        print("\nDigite as palavras-chave (Enter para pular):")
        main_kw  = input("  Palavra-chave principal: ").strip()
        sec_kws  = input("  Palavras-chave secundárias (separadas por vírgula): ").strip()
        intent   = input("  Intenção de busca (informacional/comercial/transacional): ").strip()
        kw_data  = keywords.from_manual(main_kw, sec_kws, intent)

    print(f"\n✅  Palavras-chave: {kw_data['main']} + {len(kw_data['secondary'])} secundárias")

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

    print("\n✍️   Redigindo o post completo (1-2 minutos)...\n")
    post_html = writer.write_post(transcript_text, outline, kw_data, lang)

    word_count = len(post_html.replace('<', ' <').split())
    print(f"\n✅  Post gerado com ~{word_count} palavras")

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{output_dir}/{outline.get('slug', 'post')}.html"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(post_html)

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
