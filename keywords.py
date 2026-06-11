"""
modules/keywords.py
Pesquisa de palavras-chave via Ahrefs API (Standard plan) ou input manual.
Ahrefs API v3: https://developers.ahrefs.com/api/v3
"""

import os
import json
import urllib.request
import urllib.parse


AHREFS_API_BASE = "https://api.ahrefs.com/v3"
COUNTRY_MAP = {
    "pt-br": "br",
    "es":    "mx",  # ajuste para o país-alvo principal em espanhol
}


def _ahrefs_get(endpoint: str, params: dict) -> dict:
    token = os.environ.get("AHREFS_API_TOKEN")
    if not token:
        raise EnvironmentError("AHREFS_API_TOKEN não encontrado no .env")

    query = urllib.parse.urlencode(params)
    url = f"{AHREFS_API_BASE}/{endpoint}?{query}"

    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    })

    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def from_ahrefs(topic: str, lang: str = "pt-br") -> dict:
    """
    Busca dados de palavras-chave no Ahrefs para o tópico/ângulo escolhido.
    Retorna dict padronizado com main, secondary, volume, kd, intent.
    """
    country = COUNTRY_MAP.get(lang, "br")

    try:
        # 1. Keyword ideas para o tópico
        ideas_resp = _ahrefs_get("keywords-explorer/keyword-ideas", {
            "keyword":  topic,
            "country":  country,
            "limit":    20,
            "select":   "keyword,volume,keyword_difficulty,parent_topic",
        })

        keywords_raw = ideas_resp.get("keywords", [])

        if not keywords_raw:
            print("⚠️  Ahrefs não retornou keywords. Usando input manual.")
            return _manual_fallback()

        # Ordena por volume desc, filtra KD não impossível
        filtered = [
            k for k in keywords_raw
            if k.get("volume", 0) > 0 and k.get("keyword_difficulty", 100) <= 70
        ]
        filtered.sort(key=lambda x: x.get("volume", 0), reverse=True)

        main_kw = filtered[0]["keyword"] if filtered else topic
        secondary = [k["keyword"] for k in filtered[1:6]]

        # 2. SERP overview para a KW principal (pega intent aproximado)
        intent = "informacional"  # default
        try:
            serp_resp = _ahrefs_get("keywords-explorer/serp-overview", {
                "keyword": main_kw,
                "country": country,
            })
            # Analisa os tipos de resultado para inferir intent
            serp_types = [r.get("type", "") for r in serp_resp.get("serp", [])]
            if any(t in ["shopping", "product"] for t in serp_types):
                intent = "comercial"
            elif any(t in ["how_to", "featured_snippet"] for t in serp_types):
                intent = "informacional"
        except Exception:
            pass

        print(f"  📊 Ahrefs — KW principal: '{main_kw}' | "
              f"Volume: {filtered[0].get('volume','?')} | "
              f"KD: {filtered[0].get('keyword_difficulty','?')}")

        return {
            "main":      main_kw,
            "secondary": secondary,
            "intent":    intent,
            "volume":    filtered[0].get("volume"),
            "kd":        filtered[0].get("keyword_difficulty"),
            "source":    "ahrefs",
        }

    except Exception as e:
        print(f"⚠️  Erro na API do Ahrefs: {e}")
        print("   Alternando para input manual...")
        return _manual_fallback()


def from_manual(main_kw: str, sec_kws_str: str, intent: str) -> dict:
    secondary = [k.strip() for k in sec_kws_str.split(",") if k.strip()]
    return {
        "main":      main_kw or "palavra-chave principal",
        "secondary": secondary,
        "intent":    intent or "informacional",
        "volume":    None,
        "kd":        None,
        "source":    "manual",
    }


def _manual_fallback() -> dict:
    print("\nDigite as palavras-chave manualmente:")
    main_kw  = input("  Palavra-chave principal: ").strip()
    sec_kws  = input("  Secundárias (vírgula): ").strip()
    intent   = input("  Intenção (informacional/comercial/transacional): ").strip()
    return from_manual(main_kw, sec_kws, intent)
