"""
modules/keywords.py
Pesquisa de palavras-chave delegada ao KWS Research skill (kws_research.py).
Qualquer melhoria no script de KWS Research reflete automaticamente aqui.
"""

import os
import sys
import json
import subprocess

KWS_SCRIPT = os.path.expanduser("~/Claude - KWS Research/scripts/kws_research.py")


def _fmt_vol(v) -> str:
    if v is None:
        return "-"
    try:
        v = int(v)
    except (TypeError, ValueError):
        return "-"
    if v >= 1_000_000:
        return f"{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}k"
    return str(v)


def _parse_intent(intents_obj) -> str:
    if not intents_obj:
        return "informacional"
    if isinstance(intents_obj, str):
        return intents_obj
    active = [k for k, v in intents_obj.items() if v]
    if not active:
        return "informacional"
    mapping = {
        "informational": "informacional",
        "commercial": "comercial",
        "transactional": "transacional",
        "navigational": "navegacional",
    }
    return mapping.get(active[0], active[0])


def from_ahrefs(topic: str, lang: str = "pt-br") -> dict:
    country = "br" if lang == "pt-br" else "es"

    if not os.path.exists(KWS_SCRIPT):
        print(f"⚠️  Script KWS Research não encontrado em: {KWS_SCRIPT}")
        return _manual_fallback()

    print(f"\n⏳  Pesquisando keywords via KWS Research (país: {country.upper()})...")

    proc = subprocess.run(
        [sys.executable, KWS_SCRIPT,
         "--keywords", topic,
         "--country", country,
         "--output", "json"],
        capture_output=True, text=True, timeout=120
    )

    if proc.returncode != 0 or not proc.stdout.strip():
        print(f"⚠️  Erro no KWS Research:\n{proc.stderr[:400]}")
        return _manual_fallback()

    try:
        clusters = json.loads(proc.stdout)
    except json.JSONDecodeError:
        print("⚠️  Resposta inválida do KWS Research.")
        return _manual_fallback()

    # Flatten preservando cluster de origem
    all_kws = []
    for cluster in clusters:
        for kw in cluster.get("keywords", []):
            kw["_cluster"] = cluster.get("cluster", "")
            all_kws.append(kw)

    if not all_kws:
        print("⚠️  Nenhuma keyword retornada.")
        return _manual_fallback()

    all_kws.sort(key=lambda x: x.get("traffic_potential") or 0, reverse=True)
    top = all_kws[:15]

    print(f"\n{'─'*65}")
    print("🔑  TOP KEYWORDS ENCONTRADAS:\n")
    for i, kw in enumerate(top, 1):
        vol = _fmt_vol(kw.get("volume"))
        kd  = str(kw.get("difficulty") or "-")
        tp  = _fmt_vol(kw.get("traffic_potential"))
        cluster = kw.get("_cluster", "")[:28]
        print(f"  {i:2}. {kw['keyword']:<38} Vol:{vol:>6}  KD:{kd:>3}  TP:{tp:>6}  [{cluster}]")
    print(f"{'─'*65}")

    raw = input("\n  Número da KW principal (ou escreva outra): ").strip()

    if raw.isdigit() and 1 <= int(raw) <= len(top):
        chosen = top[int(raw) - 1]
    else:
        chosen = {"keyword": raw or all_kws[0]["keyword"], "_cluster": "", "intents": {}}

    main_kw = chosen["keyword"]
    main_cluster = chosen.get("_cluster", "")

    # Secundárias: mesmo cluster, excluindo a principal
    same_cluster = [k for k in all_kws if k.get("_cluster") == main_cluster and k["keyword"] != main_kw]
    secondary = [k["keyword"] for k in same_cluster[:5]]

    # Se cluster vazio, pega as próximas do top geral
    if not secondary:
        secondary = [k["keyword"] for k in all_kws if k["keyword"] != main_kw][:5]

    intent = _parse_intent(chosen.get("intents"))
    cluster_label = f" (cluster: {main_cluster})" if main_cluster else ""
    print(f"\n✅  KW principal: '{main_kw}'{cluster_label}")
    print(f"   Secundárias: {', '.join(secondary)}")

    return {
        "main":      main_kw,
        "secondary": secondary,
        "intent":    intent,
        "volume":    chosen.get("volume"),
        "kd":        chosen.get("difficulty"),
        "source":    "ahrefs-kws-research",
    }


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
    main_kw = input("  Palavra-chave principal: ").strip()
    sec_kws = input("  Secundárias (vírgula): ").strip()
    intent  = input("  Intenção (informacional/comercial/transacional): ").strip()
    return from_manual(main_kw, sec_kws, intent)
