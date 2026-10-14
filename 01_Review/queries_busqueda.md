# Estrategia de búsqueda — Revisión sistemática

**Proyecto:** Reconocimiento de voz, traducción automática y síntesis de voz aplicados al quechua (comunicación médico-paciente)
**Fecha de búsqueda:** por registrar al ejecutar cada motor.
**Lógica:** `(bloque LENGUA) AND (bloque TECNOLOGÍA)`. El dominio médico NO se incluye en la query (devolvería casi 0 resultados); se aplica como criterio de inclusión/relevancia en el cribado.

---

## Bloques conceptuales

- **Lengua:** Quechua, Quechuan, Runasimi, "Runa Simi", Quichua, Qhichwa
- **Tecnología:** "speech recognition", ASR, "automatic speech recognition", "speech-to-text", "speech to text", STT, "machine translation", NMT, "neural machine translation", SMT, "statistical machine translation", "speech synthesis", "speech synthesizer", TTS, "text-to-speech", "text to speech", "voice synthesis"

---

## 1. Scopus (ejecutada — 41 resultados, 13/10/2026)

```
TITLE-ABS-KEY(
  (Quechua OR Quechuan OR Runasimi OR "Runa Simi" OR Quichua OR Qhichwa)
  AND
  ("speech recognition" OR ASR OR "automatic speech recognition"
   OR "speech-to-text" OR "speech to text" OR STT
   OR "machine translation" OR NMT OR "neural machine translation"
   OR SMT OR "statistical machine translation"
   OR "speech synthesis" OR "speech synthesizer"
   OR TTS OR "text-to-speech" OR "text to speech" OR "voice synthesis")
)
```

---

## 2. IEEE Xplore (Command Search)

> Pegar en **Advanced Search → Command Search**. `"All Metadata"` cubre título, resumen y palabras clave (buena cobertura).

```
("All Metadata":Quechua OR "All Metadata":Quechuan OR "All Metadata":Runasimi OR "All Metadata":"Runa Simi" OR "All Metadata":Quichua OR "All Metadata":Qhichwa)
AND
("All Metadata":"speech recognition" OR "All Metadata":ASR OR "All Metadata":"automatic speech recognition" OR "All Metadata":"speech-to-text" OR "All Metadata":"speech to text" OR "All Metadata":STT OR "All Metadata":"machine translation" OR "All Metadata":NMT OR "All Metadata":"neural machine translation" OR "All Metadata":SMT OR "All Metadata":"statistical machine translation" OR "All Metadata":"speech synthesis" OR "All Metadata":"speech synthesizer" OR "All Metadata":TTS OR "All Metadata":"text-to-speech" OR "All Metadata":"text to speech" OR "All Metadata":"voice synthesis")
```

**Resultados:** 2  **Fecha:** 14/10/2026

---

## 3. ACM Digital Library (Advanced Search — campo ABSTRACT)

> IMPORTANTE: usar el **formulario de búsqueda avanzada**, NO la barra simple
> (la barra envuelve la cadena en `AllField` y rompe el AND).
> Usar el campo **Abstract** (no `All`, que busca en el texto completo y devuelve
> cientos de miles de falsos positivos). Abstract ≈ TITLE-ABS-KEY de Scopus.

**Formulario:** condición 1 (Abstract) = bloque lengua · AND · condición 2 (Abstract) = bloque tecnología.

**Cadena equivalente (pegar en Edit Search, no en la barra):**

```
[[Abstract: quechua] OR [Abstract: quechuan] OR [Abstract: runasimi] OR [Abstract: "runa simi"] OR [Abstract: quichua] OR [Abstract: qhichwa]]
AND
[[Abstract: "speech recognition"] OR [Abstract: asr] OR [Abstract: "automatic speech recognition"] OR [Abstract: "speech-to-text"] OR [Abstract: stt] OR [Abstract: "machine translation"] OR [Abstract: nmt] OR [Abstract: "neural machine translation"] OR [Abstract: smt] OR [Abstract: "statistical machine translation"] OR [Abstract: "speech synthesis"] OR [Abstract: "speech synthesizer"] OR [Abstract: tts] OR [Abstract: "text-to-speech"] OR [Abstract: "voice synthesis"]]
```

**Resultados:** 19  **Fecha:** 14/10/2026 (campo `All`/Anywhere, sin límite de años; Basic Edition no permite exportar — usar Zotero o Knimbus)

---

## Seguimiento PRISMA (identificación)

| Fuente | Resultados | Fecha |
|--------|-----------:|-------|
| Scopus | 41 | 13/10/2026 |
| IEEE Xplore | 2 | 14/10/2026 |
| ACM Digital Library | 19 | 14/10/2026 |
| **Total identificados** | **62** | |
| Duplicados eliminados | 4 | |
| Para cribado | **58** | |

**Deduplicación:** Zotero unió 4 duplicados internos de ACM (19 → 15 únicos). Entre bases no hay solapamiento (DOIs de editoriales distintas: Scopus 10.18653/10.1007/10.21437, IEEE 10.1109, ACM 10.1145).

**Archivos finales (raíz del proyecto):** `scopus.bib` (41), `ieee.bib` (2), `acm.bib` (15).

**Cribado preliminar:** ACM = 15 fuera de tema (coincidencias de texto completo; ninguno trata sobre quechua) → ~0 incluidos. IEEE: Guzmán 2021 relevante; Abbasova 2026 a excluir. El núcleo de estudios incluidos vendrá de Scopus.
