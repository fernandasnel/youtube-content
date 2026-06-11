"""
modules/transcript.py
Busca a transcrição de um vídeo do YouTube via youtube-transcript-api.
Suporta PT-BR e ES com fallback para EN.
"""

from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled
import re


LANG_PRIORITIES = {
    "pt-br": ["pt", "pt-BR", "pt-br", "en"],
    "es":    ["es", "es-419", "en"],
}


def _extract_video_id(url: str) -> str:
    patterns = [
        r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    raise ValueError(f"Não foi possível extrair o ID do vídeo de: {url}")


def get(url: str, lang: str = "pt-br") -> str | None:
    """
    Retorna a transcrição completa como string.
    Retorna None se não houver transcrição disponível.
    """
    video_id = _extract_video_id(url)
    priorities = LANG_PRIORITIES.get(lang, ["pt", "en"])

    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        # Tenta idiomas na ordem de prioridade
        transcript = None
        for lang_code in priorities:
            try:
                transcript = transcript_list.find_transcript([lang_code])
                break
            except Exception:
                continue

        # Fallback: pega qualquer um e traduz
        if not transcript:
            transcript = transcript_list.find_generated_transcript(
                [t.language_code for t in transcript_list]
            )

        entries = transcript.fetch()
        full_text = " ".join(e["text"] for e in entries)

        # Limpa artefatos comuns de transcrição automática
        full_text = re.sub(r"\[.*?\]", "", full_text)   # [Música], [Aplausos]
        full_text = re.sub(r"\s+", " ", full_text).strip()

        return full_text

    except TranscriptsDisabled:
        print("⚠️  Transcrições desabilitadas neste vídeo.")
        return None
    except NoTranscriptFound:
        print("⚠️  Nenhuma transcrição encontrada.")
        return None
    except Exception as e:
        print(f"⚠️  Erro ao buscar transcrição: {e}")
        return None
