"""
normalizar_texto.py — Normalización ortográfica de transcripciones en quechua sureño.

Problema que resuelve: el WER/CER de un ASR es muy sensible a diferencias "invisibles"
en el texto de referencia (variantes del apóstrofo, mayúsculas, puntuación, formas
Unicode distintas). Si no se normaliza de forma consistente, dos cadenas que suenan
idénticas cuentan como error. Este módulo fija una convención única y documentada.

DECISIONES (rigurosidad teórica e interpretativa):
  1. Forma Unicode NFC  -> una misma letra tiene una sola representación de bytes.
  2. Apóstrofo unificado -> en quechua sureño el apóstrofo marca la GLOTALIZACIÓN de
     oclusivas (p', t', ch', k', q'); es fonémico y NO debe eliminarse. Se unifican sus
     variantes tipográficas (’ U+2019, ʼ U+02BC, ` U+0060, ´ U+00B4) al apóstrofo
     recto ' (U+0027) para que 'q'ara' y 'q’ara' cuenten como la misma palabra.
  3. Minúsculas -> el ASR no distingue mayúsculas; se pasa todo a minúsculas.
  4. Puntuación de borde -> se retira la puntuación que no se pronuncia
     (.,;:¿?¡!«»"“”()[]…—) pero se CONSERVA el apóstrofo y el guion internos de palabra.
  5. Espacios -> se colapsan espacios múltiples y se recortan los extremos.
  6. Dígitos -> se MARCAN (no se borran): un número escrito como "3" es ambiguo para el
     ASR (¿"kimsa"? ¿"tres"?). La función `tiene_digitos` permite filtrarlos o revisarlos
     antes de entrenar, en vez de introducir ruido silencioso.

Uso:
    from normalizar_texto import normalizar_quechua, tiene_digitos
    texto_norm = normalizar_quechua("¿Imaynan q’ara wasiykipi?")
    #  -> "imaynan q'ara wasiykipi"
"""

from __future__ import annotations

import re
import unicodedata

# Variantes tipográficas del apóstrofo -> apóstrofo recto (U+0027).
_APOSTROFOS = {
    "’": "'",  # ’ right single quotation mark
    "ʼ": "'",  # ʼ modifier letter apostrophe
    "`": "'",  # ` grave accent usado como apóstrofo
    "´": "'",  # ´ acute accent usado como apóstrofo
    "′": "'",  # ′ prime
}

# Puntuación que no se pronuncia y debe retirarse (se conservan ' y - internos).
_PUNTUACION = r"[.,;:¿?¡!«»\"“”\(\)\[\]\{\}…—–/\\|@#$%^&*+=~<>]"

# Apóstrofo o guion pegados a un borde de palabra (no son fonémicos ahí) -> fuera.
_APOS_BORDE = re.compile(r"(?<!\w)['-]|['-](?!\w)")
_ESPACIOS = re.compile(r"\s+")
_DIGITOS = re.compile(r"\d")


def tiene_digitos(texto: str) -> bool:
    """True si la cadena contiene algún dígito (texto ambiguo para el ASR)."""
    return bool(_DIGITOS.search(texto or ""))


def normalizar_quechua(texto: str) -> str:
    """Devuelve la transcripción normalizada según la convención documentada arriba."""
    if not texto:
        return ""
    # 1. Unicode NFC.
    t = unicodedata.normalize("NFC", texto)
    # 2. Unificar apóstrofos (preserva la glotalización p', t', ch', k', q').
    for malo, bueno in _APOSTROFOS.items():
        t = t.replace(malo, bueno)
    # 3. Minúsculas.
    t = t.lower()
    # 4. Retirar puntuación no pronunciada (conserva ' y - internos).
    t = re.sub(_PUNTUACION, " ", t)
    #    y los apóstrofos/guiones que quedaron en el borde de una palabra.
    t = _APOS_BORDE.sub("", t)
    # 5. Colapsar espacios.
    t = _ESPACIOS.sub(" ", t).strip()
    return t


if __name__ == "__main__":
    # Pruebas de humo: casos representativos del quechua sureño.
    casos = [
        ("¿Imaynan q’ara wasiykipi?", "imaynan q'ara wasiykipi"),
        ("P'unchay   kusikuy!!", "p'unchay kusikuy"),
        ("«Hampi» wasi —runasimipi.", "hampi wasi runasimipi"),
        ("Unquq 3 killapi", "unquq 3 killapi"),  # el dígito NO se borra: se marca aparte
    ]
    ok = True
    for entrada, esperado in casos:
        obtenido = normalizar_quechua(entrada)
        marca = "OK " if obtenido == esperado else "XX "
        if obtenido != esperado:
            ok = False
        print(f"{marca}{entrada!r:40} -> {obtenido!r}  (esperado {esperado!r})")
    print(f"tiene_digitos('Unquq 3 killapi') = {tiene_digitos('Unquq 3 killapi')}")
    print("TODOS OK" if ok else "FALLÓ ALGÚN CASO")
