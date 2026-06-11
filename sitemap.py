"""
modules/sitemap.py
Lê o sitemap XML do blog da Hotmart e extrai URLs + slugs publicados.
Usado para checagem de conteúdo duplicado.
"""

import re
import urllib.request
import gzip
import io
from xml.etree import ElementTree as ET


SITEMAPS = {
    "pt-br": "https://hotmart.com/pt-br/blog/sitemap.xml",
    "es":    "https://hotmart.com/es/blog/sitemap.xml",
}

# Caso o sitemap principal seja um index que aponta para sub-sitemaps
SITEMAP_INDEX_TAG = "{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap"
SITEMAP_URL_TAG   = "{http://www.sitemaps.org/schemas/sitemap/0.9}url"
LOC_TAG           = "{http://www.sitemaps.org/schemas/sitemap/0.9}loc"


def _fetch_xml(url: str) -> bytes:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (SEO-Agent/1.0)"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read()

    # Descomprime se for gzip
    if data[:2] == b'\x1f\x8b':
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as gz:
            data = gz.read()

    return data


def _parse_urls(xml_bytes: bytes) -> list[str]:
    root = ET.fromstring(xml_bytes)

    # Sitemap index → busca sub-sitemaps recursivamente
    sitemaps = root.findall(SITEMAP_INDEX_TAG)
    if sitemaps:
        all_urls = []
        for sm in sitemaps:
            loc = sm.find(LOC_TAG)
            if loc is not None and loc.text:
                try:
                    sub_xml = _fetch_xml(loc.text)
                    all_urls.extend(_parse_urls(sub_xml))
                except Exception:
                    continue
        return all_urls

    # Sitemap normal
    urls = []
    for url_el in root.findall(SITEMAP_URL_TAG):
        loc = url_el.find(LOC_TAG)
        if loc is not None and loc.text:
            urls.append(loc.text.strip())

    return urls


def _url_to_slug(url: str) -> str:
    """Extrai o slug final da URL."""
    return url.rstrip("/").split("/")[-1]


def _slug_to_title(slug: str) -> str:
    """Converte slug em título legível (aproximado)."""
    return slug.replace("-", " ").title()


def load(lang: str = "pt-br") -> list[dict]:
    """
    Retorna lista de dicts: [{"url": "...", "slug": "...", "title": "..."}]
    Falha graciosamente — retorna lista vazia se o sitemap estiver inacessível.
    """
    sitemap_url = SITEMAPS.get(lang, SITEMAPS["pt-br"])

    try:
        xml_bytes = _fetch_xml(sitemap_url)
        urls = _parse_urls(xml_bytes)

        posts = []
        for url in urls:
            slug = _url_to_slug(url)
            if slug and slug != "blog":
                posts.append({
                    "url":   url,
                    "slug":  slug,
                    "title": _slug_to_title(slug),
                })

        return posts

    except Exception as e:
        print(f"⚠️  Não foi possível carregar o sitemap ({e}). Continuando sem checagem de duplicação.")
        return []
