from __future__ import annotations

import argparse
import copy
import os
import re
import shutil
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

from . import __version__, progress
from .chunker import Chunk, chunk_entries, detect_style
from .config import load_config
from .languages import LANGUAGES, LanguageDef, resolve_targets
from .output_manager import OutputManager
from .paths import default_config_path, default_input_root, default_output_root
from .progress import EventType
from .providers.base import BaseProvider
from .reassembler import reassemble
from .srt_parser import parse_srt, serialize_srt
from .text_processor import strip_and_index

_MARKER_NUMBER_RE = re.compile(r"<<(\d+)>>")


def _configure_console_encoding_errors() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(errors="backslashreplace")
        except (OSError, ValueError):
            pass


def _build_provider(cfg, args) -> BaseProvider:
    from .providers.claude_prov import ClaudeProvider
    from .providers.openai_prov import OpenAIProvider

    provider_name = args.provider or cfg.provider
    model = args.model or cfg.model
    api_key = None
    base_url = args.base_url or cfg.base_url or None

    if provider_name == "claude":
        if not api_key:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        return ClaudeProvider(model=model, api_key=api_key)

    if provider_name in ("openai", "lmstudio"):
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
        if provider_name == "lmstudio" and not api_key:
            local_auth_placeholder = "lm-studio"
            api_key = local_auth_placeholder
        return OpenAIProvider(
            model=model,
            api_key=api_key,
            base_url=base_url,
            provider_label=provider_name,
        )

    print(f"Unknown provider: {provider_name}", file=sys.stderr)
    sys.exit(1)


def _resolve_targets(args, cfg) -> list[LanguageDef]:
    """Resolve CLI flags and config into an ordered, deduplicated list of LanguageDef."""
    # CLI layer: any of --targets, --target, --preset → replaces config entirely
    cli_values: list[str] = []
    has_cli = False

    if args.preset:
        cli_values.append(args.preset)
        has_cli = True
    if args.targets:
        cli_values.extend(args.targets)
        has_cli = True
    if args.target:
        print("Warning: --target is deprecated; use --targets instead.", file=sys.stderr)
        cli_values.append(args.target)
        has_cli = True

    if has_cli:
        return resolve_targets(cli_values)

    # Config layer
    if cfg.targets:
        result: list[LanguageDef] = []
        seen: set[str] = set()
        for t in cfg.targets:
            if t.code in seen:
                continue
            seen.add(t.code)
            if t.code in LANGUAGES:
                base = LANGUAGES[t.code]
                mlc = t.max_line_chars if t.max_line_chars > 0 else base.max_line_chars
                name = t.language if t.language else base.prompt_name
                result.append(LanguageDef(t.code, name, mlc))
            else:
                mlc = t.max_line_chars if t.max_line_chars > 0 else 42
                result.append(LanguageDef(t.code, t.language or t.code, mlc))
        return result

    if cfg.preset:
        return resolve_targets([cfg.preset])

    if cfg.target_lang:
        return resolve_targets([cfg.target_lang])

    return []


def _load_glossary_terms(glossary_path: Path | None) -> str:
    """Return raw 'term -> translation' lines, or '' if no glossary."""
    if not glossary_path or not glossary_path.exists():
        return ""
    import csv

    terms = []
    with open(glossary_path, encoding="utf-8") as f:
        for row in csv.reader(f):
            if len(row) >= 2:
                terms.append(f"  {row[0].strip()} -> {row[1].strip()}")
    return "\n".join(terms)


def _build_glossary_note(glossary_path: Path | None) -> str:
    terms = _load_glossary_terms(glossary_path)
    if not terms:
        return ""
    count = terms.count("\n") + 1
    print(f"  Glossary: {count} terms")
    return "\n\nGlossary (use these translations consistently):\n" + terms


def _review_chunks(
    chunks: list[Chunk],
    provider: BaseProvider,
    parallel: int,
    om: OutputManager,
    glossary_terms: str = "",
    source_context: str = "",
) -> None:
    """Pass 4: lexical review of English source. Mutates chunk.source_text in place."""
    non_empty = [(i, c) for i, c in enumerate(chunks) if c.source_text.strip()]
    if not non_empty:
        om.write_json(chunks, 4)
        om.log("  Pass 4: no non-empty chunks to review")
        return

    def review_one(i_chunk: tuple[int, Chunk]) -> tuple[int, str]:
        i, chunk = i_chunk
        n = chunk.marker_count
        marker_hint = (
            f"[This text contains exactly {n} marker{'s' if n != 1 else ''}: "
            f"{', '.join(f'<<{j}>>' for j in range(1, n + 1))}]\n"
            if n > 0
            else "[This text contains no markers]\n"
        )
        text = marker_hint + chunk.source_text

        last_err: Exception | None = None
        for attempt in range(3):
            try:
                result = provider.review(
                    text, glossary_terms=glossary_terms, source_context=source_context
                )
                if attempt > 0:
                    om.log(f"  review chunk {i + 1} OK (attempt {attempt + 1})")
                return i, result
            except Exception as exc:
                om.log(
                    f"  review chunk {i + 1} FAILED (attempt {attempt + 1}): {type(exc).__name__}: {exc}"
                )
                last_err = exc
                if attempt < 2:
                    delay = 2 ** (attempt + 1)
                    time.sleep(delay)
        raise last_err  # type: ignore[misc]

    if parallel > 1:
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {executor.submit(review_one, ic): ic[0] for ic in non_empty}
            completed_count = 0
            for future in as_completed(futures):
                i, reviewed = future.result()
                chunks[i].source_text = reviewed
                completed_count += 1
                print(f"  [{completed_count}/{len(non_empty)}] chunks reviewed", end="\r")
                progress.emit(
                    EventType.PASS_CHUNK,
                    **{"pass": 4, "chunk": completed_count, "total": len(non_empty)},
                )
        print("")
    else:
        for done, (i, chunk) in enumerate(non_empty, 1):
            _, reviewed = review_one((i, chunk))
            chunk.source_text = reviewed
            n = len(chunk.entry_indices)
            print(
                f"  [{done}/{len(non_empty)}] chunk {i + 1}:"
                f" {n} entr{'y' if n == 1 else 'ies'} reviewed"
            )
            progress.emit(
                EventType.PASS_CHUNK, **{"pass": 4, "chunk": done, "total": len(non_empty)}
            )

    om.write_json(chunks, 4)
    om.log(f"  Pass 4: {len(non_empty)}/{len(non_empty)} chunks reviewed")
    om.log("")


def _prepare_translation_source_chunks(
    chunks: list[Chunk],
    provider: BaseProvider,
    parallel: int,
    om: OutputManager,
    glossary_terms: str = "",
    source_context: str = "",
) -> None:
    """Prepare semantic English source for downstream translation. Mutates chunks in place."""
    non_empty = [(i, c) for i, c in enumerate(chunks) if c.source_text.strip()]
    if not non_empty:
        om.write_json(chunks, 4, "translation_source")
        om.log("  Translation source: no non-empty chunks to prepare")
        return

    def validate_markers(result: str, expected_count: int) -> None:
        markers = [int(n) for n in _MARKER_NUMBER_RE.findall(result)]
        expected = list(range(1, expected_count + 1))
        if markers != expected:
            raise ValueError(f"expected markers {expected}, got {markers}")

    def prepare_one(i_chunk: tuple[int, Chunk]) -> tuple[int, str]:
        i, chunk = i_chunk
        n = chunk.marker_count
        marker_hint = (
            f"[This text contains exactly {n} marker{'s' if n != 1 else ''}: "
            f"{', '.join(f'<<{j}>>' for j in range(1, n + 1))}]\n"
            if n > 0
            else "[This text contains no markers]\n"
        )
        text = marker_hint + chunk.source_text

        last_err: Exception | None = None
        for attempt in range(3):
            try:
                result = provider.prepare_translation_source(
                    text,
                    glossary_terms=glossary_terms,
                    source_context=source_context,
                )
                if result.startswith(marker_hint):
                    result = result[len(marker_hint) :]
                validate_markers(result, n)
                if attempt > 0:
                    om.log(f"  translation source chunk {i + 1} OK (attempt {attempt + 1})")
                return i, result
            except Exception as exc:
                om.log(
                    f"  translation source chunk {i + 1} FAILED "
                    f"(attempt {attempt + 1}): {type(exc).__name__}: {exc}"
                )
                last_err = exc
                if attempt < 2:
                    time.sleep(2 ** (attempt + 1))
        raise last_err  # type: ignore[misc]

    if parallel > 1:
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            futures = {executor.submit(prepare_one, ic): ic[0] for ic in non_empty}
            completed_count = 0
            for future in as_completed(futures):
                i, prepared = future.result()
                chunks[i].source_text = prepared
                completed_count += 1
                print(
                    f"  [{completed_count}/{len(non_empty)}] translation-source chunks prepared",
                    end="\r",
                )
        print("")
    else:
        for done, (i, chunk) in enumerate(non_empty, 1):
            _, prepared = prepare_one((i, chunk))
            chunks[i].source_text = prepared
            n = len(chunk.entry_indices)
            print(
                f"  [{done}/{len(non_empty)}] translation-source chunk {i + 1}:"
                f" {n} entr{'y' if n == 1 else 'ies'} prepared"
            )

    om.write_json(chunks, 4, "translation_source")
    om.log(f"  Translation source: {len(non_empty)}/{len(non_empty)} chunks prepared")
    om.log("")


def _translate_language(
    lang: LanguageDef,
    idx: int,
    total: int,
    entries: list,
    chunks: list[Chunk],
    corpus,
    provider: BaseProvider,
    source_lang: str,
    cfg,
    parallel_chunks: int,
    om: OutputManager,
    glossary_note: str,
    print_lock: threading.Lock,
) -> tuple[str, bool]:
    """Run passes 5-7 for one language. Returns (code, success)."""
    code = lang.code

    def safe_print(*a, **kw):
        with print_lock:
            print(*a, **kw)

    label = f"[{idx + 1}/{total}] {code} - {lang.prompt_name}"

    progress.emit(EventType.LANG_START, lang=code)

    if om.should_skip(code):
        safe_print(f"\n{label} (skipped, output exists)")
        om.log(f"[{code}] {lang.prompt_name}")
        om.log("  Skipped (output already exists).")
        om.log("")
        return code, True

    safe_print(f"\n{label}")
    om.log(f"[{code}] {lang.prompt_name}")

    non_empty = [c for c in chunks if c.source_text.strip()]
    translations: list[str] = [""] * len(chunks)

    def translate_one(i_chunk: tuple[int, Chunk]) -> tuple[int, str]:
        i, chunk = i_chunk
        if not chunk.source_text.strip():
            return i, ""

        preceding = ""
        if i > 0:
            prev = chunks[i - 1]
            if prev.entry_indices:
                preceding = corpus.entry_texts[prev.entry_indices[-1]]

        n = chunk.marker_count
        marker_hint = (
            f"[This text contains exactly {n} marker{'s' if n != 1 else ''}: "
            f"{', '.join(f'<<{i}>>' for i in range(1, n + 1))}]\n"
            if n > 0
            else "[This text contains no markers]\n"
        )
        text = marker_hint + chunk.source_text
        if glossary_note:
            text = text + glossary_note

        last_err: Exception | None = None
        for attempt in range(3):
            try:
                t0 = time.time()
                result = provider.translate(
                    text=text,
                    source_lang=source_lang,
                    target_lang=lang.prompt_name,
                    preceding_context=preceding,
                )
                elapsed_ms = int((time.time() - t0) * 1000)
                if attempt > 0:
                    om.log(f"          chunk {i + 1} OK (attempt {attempt + 1})")
                progress.emit(
                    EventType.LANG_CHUNK,
                    lang=code,
                    chunk=i + 1,
                    total=len(chunks),
                    elapsed_ms=elapsed_ms,
                )
                return i, result
            except Exception as exc:
                err_label = f"{type(exc).__name__}: {exc}"
                om.log(f"          chunk {i + 1} FAILED (attempt {attempt + 1}): {err_label}")
                last_err = exc
                if attempt < 2:
                    delay = 2 ** (attempt + 1)  # 2s, 4s
                    safe_print(
                        f"  ! chunk {i + 1}: attempt {attempt + 1} failed"
                        f" ({type(exc).__name__}), retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    safe_print(
                        f"  ! chunk {i + 1}: attempt 3 failed ({type(exc).__name__})"
                        f" - language pipeline aborted"
                    )

        raise last_err  # type: ignore[misc]

    # Pass 5: Translate
    progress.emit(EventType.PASS_START, **{"pass": 5, "name": "Translate"})
    try:
        if parallel_chunks > 1:
            with ThreadPoolExecutor(max_workers=parallel_chunks) as executor:
                futures = {executor.submit(translate_one, (i, c)): i for i, c in enumerate(chunks)}
                completed_count = 0
                for future in as_completed(futures):
                    i, result = future.result()
                    translations[i] = result
                    if chunks[i].source_text.strip():
                        completed_count += 1
                        safe_print(
                            f"  [{completed_count}/{len(non_empty)}] chunks translated",
                            end="\r",
                        )
            safe_print("")
        else:
            done = 0
            for i, chunk in enumerate(chunks):
                _, result = translate_one((i, chunk))
                translations[i] = result
                if chunk.source_text.strip():
                    done += 1
                    n = len(chunk.entry_indices)
                    safe_print(
                        f"  [{done}/{len(non_empty)}] chunk {i + 1}:"
                        f" {n} entr{'y' if n == 1 else 'ies'} translated"
                    )
    except Exception as exc:
        om.log("  LANGUAGE FAILED: Pass 5 exhausted retries. Skipping.")
        om.log("")
        safe_print(f"  FAILED -> {code} skipped. See {om.passes_dir() / 'pipeline.log'}")
        progress.emit(EventType.LANG_FAILED, lang=code, error=str(exc))
        return code, False

    om.write_json(translations, 5, code)
    om.log(f"  Pass 5: {len(non_empty)}/{len(non_empty)} chunks OK")
    progress.emit(EventType.PASS_DONE, **{"pass": 5})

    # Pass 6: Reassemble
    progress.emit(EventType.PASS_START, **{"pass": 6, "name": "Reassemble"})
    max_line_chars = min(lang.max_line_chars, cfg.output.max_line_chars)
    result_entries, fallback_warnings = reassemble(
        entries,
        chunks,
        translations,
        corpus,
        max_line_chars=max_line_chars,
        min_entry_chars=cfg.output.min_entry_chars,
    )
    om.write_json(result_entries, 6, code)
    if fallback_warnings:
        for w in fallback_warnings:
            om.log(f"  Pass 6 WARNING: {w}")
            safe_print(f"  ! {w}")
        om.log(f"  Pass 6: OK ({len(fallback_warnings)} proportional fallback(s))")
    else:
        om.log("  Pass 6: OK")
    progress.emit(EventType.PASS_DONE, **{"pass": 6})

    # Pass 7: Serialize
    progress.emit(EventType.PASS_START, **{"pass": 7, "name": "Serialize"})
    srt_pass_path = om.pass_path(7, code, "srt")
    serialize_srt(result_entries, srt_pass_path, bom=cfg.output.bom)
    final = om.finalize_srt(code)
    om.log(f"  Pass 7: OK -> {final}")
    om.log("")
    safe_print(f"  Done -> {final}")
    progress.emit(EventType.PASS_DONE, **{"pass": 7})
    progress.emit(EventType.LANG_DONE, lang=code, entries=len(result_entries))
    return code, True


def _process_file(
    input_path: Path,
    file_idx: int,
    file_total: int,
    args,
    cfg,
    target_langs: list[LanguageDef],
    source_lang: str,
    provider: BaseProvider,
    model_display: str,
    glossary_note: str,
    glossary_terms: str,
    output_root: Path,
    skip_existing: bool,
) -> bool:
    """Run the full 7-pass pipeline for one input file. Returns True on success."""
    label = f"[{file_idx + 1}/{file_total}] {input_path.name}"
    print(f"\n{'=' * 60}")
    print(f"File {label}")
    print(f"{'=' * 60}")
    progress.emit(
        EventType.FILE_START,
        file=input_path.name,
        index=file_idx + 1,
        total=file_total,
        stem=input_path.stem,
    )

    # ── Pass 1: Parse ─────────────────────────────────────────────────────────
    progress.emit(EventType.PASS_START, **{"pass": 1, "name": "Parse"})
    print(f"Parsing {input_path} ...")
    entries = parse_srt(input_path)
    if not entries:
        print("  No entries found — skipping.", file=sys.stderr)
        progress.emit(
            EventType.FILE_DONE, file=input_path.name, stem=input_path.stem, success=False
        )
        return False
    progress.emit(EventType.PASS_DONE, **{"pass": 1})

    # ── Pass 2: Strip tags / build corpus ─────────────────────────────────────
    progress.emit(EventType.PASS_START, **{"pass": 2, "name": "Strip"})
    corpus = strip_and_index(entries)
    progress.emit(EventType.PASS_DONE, **{"pass": 2})

    # ── Pass 3: Chunk ─────────────────────────────────────────────────────────
    progress.emit(EventType.PASS_START, **{"pass": 3, "name": "Chunk"})
    style = detect_style(corpus.entry_texts)
    chunks = chunk_entries(
        entries,
        corpus.entry_texts,
        max_chunk_chars=cfg.chunking.max_chunk_chars,
        gap_threshold_ms=cfg.chunking.gap_threshold_ms,
    )
    non_empty = [c for c in chunks if c.source_text.strip()]
    print(
        f"  {len(entries)} entries | Style: {style} | "
        f"{len(chunks)} chunks ({len(non_empty)} non-empty, "
        f"{len(chunks) - len(non_empty)} pass-through)"
    )
    progress.emit(EventType.PASS_DONE, **{"pass": 3})

    om = OutputManager(input_path, output_root, skip_existing)

    om.write_json(entries, 1)
    om.write_json(corpus, 2)
    om.write_json(chunks, 3)

    now = datetime.now().isoformat(timespec="seconds")
    om.log(f"=== Run: {now} ===")
    om.log(f"Input:    {input_path.name}  ({len(entries)} entries, {len(non_empty)} chunks)")
    om.log(f"Provider: {provider.name} / {model_display}")
    om.log(f"Source:   {source_lang}")
    om.log("")

    # English is produced automatically from review — strip it from translation targets
    translation_targets = [l for l in target_langs if l.code != "en_US"]  # noqa: E741

    print(f"\nReviewing with {provider.name} / {model_display}")
    print(f"  Source: {source_lang}")

    # ── Pass 4: Lexical review + en_US output ─────────────────────────────────
    om.log("=== Pass 4: Lexical review ===")
    print(f"\nPass 4: Lexical review ({len(non_empty)} chunks)...")
    progress.emit(EventType.PASS_START, **{"pass": 4, "name": "Lexical Review"})
    try:
        _review_chunks(
            chunks,
            provider,
            args.parallel,
            om,
            glossary_terms=glossary_terms,
            source_context=cfg.source_context,
        )
    except Exception as exc:
        print(f"Error: Pass 4 (lexical review) failed: {exc}", file=sys.stderr)
        om.log(f"  FAILED: {type(exc).__name__}: {exc}")
        progress.emit(EventType.FATAL_ERROR, error=str(exc))
        progress.emit(
            EventType.FILE_DONE, file=input_path.name, stem=input_path.stem, success=False
        )
        return False
    progress.emit(EventType.PASS_DONE, **{"pass": 4})

    # Produce en_US SRT directly from reviewed chunks (no translation needed)
    reviewed_entries, en_warnings = reassemble(
        entries,
        chunks,
        [c.source_text for c in chunks],
        corpus,
        max_line_chars=cfg.output.max_line_chars,
        min_entry_chars=cfg.output.min_entry_chars,
        preserve_entry_boundaries=True,
    )
    en_pass_path = om.pass_path(4, "en_US", "srt")
    serialize_srt(reviewed_entries, en_pass_path, bom=cfg.output.bom)
    for w in en_warnings:
        om.log(f"  Pass 4 (en_US) WARNING: {w}")
    if not om.should_skip("en_US"):
        shutil.copy2(en_pass_path, om.final_srt_path("en_US"))
        om.log(f"  Pass 4 (en_US): reviewed English -> {om.final_srt_path('en_US')}")
        print(f"  en_US -> {om.final_srt_path('en_US')}")
    else:
        om.log("  Pass 4 (en_US): skipped (output exists)")

    if not translation_targets:
        print(f"\nOutput:  {om.output_dir()}/")
        om.log("  No translation targets configured.")
        om.log("")
        progress.emit(EventType.FILE_DONE, file=input_path.name, stem=input_path.stem, success=True)
        return True

    translation_chunks = copy.deepcopy(chunks)
    translation_non_empty = [c for c in translation_chunks if c.source_text.strip()]
    om.log("=== Translation source preparation ===")
    print(f"\nPreparing English translation source ({len(translation_non_empty)} chunks)...")
    try:
        _prepare_translation_source_chunks(
            translation_chunks,
            provider,
            args.parallel,
            om,
            glossary_terms=glossary_terms,
            source_context=cfg.source_context,
        )
    except Exception as exc:
        print(f"Error: translation source preparation failed: {exc}", file=sys.stderr)
        om.log(f"  FAILED: {type(exc).__name__}: {exc}")
        progress.emit(EventType.FATAL_ERROR, error=str(exc))
        progress.emit(
            EventType.FILE_DONE, file=input_path.name, stem=input_path.stem, success=False
        )
        return False

    translation_source_entries, source_warnings = reassemble(
        entries,
        translation_chunks,
        [c.source_text for c in translation_chunks],
        corpus,
        max_line_chars=cfg.output.max_line_chars,
        min_entry_chars=cfg.output.min_entry_chars,
    )
    translation_source_path = om.pass_path(4, "translation_source", "srt")
    serialize_srt(translation_source_entries, translation_source_path, bom=cfg.output.bom)
    for w in source_warnings:
        om.log(f"  Translation source WARNING: {w}")
    om.log(f"  Translation source SRT -> {translation_source_path}")

    targets_display = ", ".join(
        f"{l.code} ({l.prompt_name})"
        for l in translation_targets  # noqa: E741
    )
    print(f"\nTargets: {targets_display}")
    print(f"Output:  {om.output_dir()}/")

    # ── Passes 5-7: per-language loop ─────────────────────────────────────────
    completed: list[str] = []
    failed: list[str] = []
    print_lock = threading.Lock()

    def run_one(idx_lang: tuple[int, LanguageDef]) -> tuple[str, bool]:
        idx, lang = idx_lang
        return _translate_language(
            lang=lang,
            idx=idx,
            total=len(translation_targets),
            entries=entries,
            chunks=translation_chunks,
            corpus=corpus,
            provider=provider,
            source_lang=source_lang,
            cfg=cfg,
            parallel_chunks=args.parallel,
            om=om,
            glossary_note=glossary_note,
            print_lock=print_lock,
        )

    if args.parallel_languages > 1:
        with ThreadPoolExecutor(max_workers=args.parallel_languages) as executor:
            futures = [
                executor.submit(run_one, (i, lang)) for i, lang in enumerate(translation_targets)
            ]
            for future in as_completed(futures):
                code, ok = future.result()
                (completed if ok else failed).append(code)
    else:
        for i, lang in enumerate(translation_targets):
            code, ok = run_one((i, lang))
            (completed if ok else failed).append(code)

    total = len(translation_targets)
    done = len(completed)
    print(f"\nSummary: {done}/{total} translations completed.", end="")
    if failed:
        print(f" Failed: {', '.join(failed)}")
    else:
        print()
    print(f"Log: {om.passes_dir() / 'pipeline.log'}")

    summary = f"Summary: {done}/{total} translations completed."
    if failed:
        summary += f" {len(failed)} failed ({', '.join(failed)})."
    om.log(summary)

    success = len(failed) == 0
    progress.emit(EventType.FILE_DONE, file=input_path.name, stem=input_path.stem, success=success)
    return success


def main(argv: list[str] | None = None) -> None:
    _configure_console_encoding_errors()

    parser = argparse.ArgumentParser(
        prog="mae-captions",
        description="Mae Captions translates SRT subtitle files using Claude, OpenAI, or LM Studio.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m mae_captions                         # process all .srt files in inputs/
  python -m mae_captions inputs/movie.srt        # single explicit file
  python -m mae_captions inputs/a.srt inputs/b.srt --preset top5
  python -m mae_captions inputs/movie.srt --targets zh_CN --provider openai --model gpt-4o
  python -m mae_captions inputs/movie.srt --targets de_DE --provider lmstudio --base-url http://localhost:1234/v1
        """,
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "input",
        type=Path,
        nargs="*",
        help="Input .srt file(s). If omitted, all .srt files in inputs/ are processed.",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        metavar="LANG",
        default=None,
        help="One or more target language codes or names",
    )
    parser.add_argument(
        "--preset",
        default=None,
        metavar="NAME",
        help="Named language preset (e.g. top5); combined with --targets",
    )
    parser.add_argument(
        "--target",
        "-t",
        default=None,
        metavar="LANG",
        help="[deprecated] Single target language — use --targets instead",
    )
    parser.add_argument(
        "--source",
        "-s",
        default=None,
        metavar="LANG",
        help="Source language (default: auto-detect)",
    )
    parser.add_argument("--provider", "-p", choices=["claude", "openai", "lmstudio"], default=None)
    parser.add_argument("--model", "-m", default=None)
    parser.add_argument(
        "--base-url",
        default=None,
        dest="base_url",
        help="Base URL for OpenAI-compatible endpoints (LM Studio)",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=None,
        dest="output_root",
        help="Base directory for all outputs (default: ./outputs)",
    )
    parser.add_argument("--config", "-c", type=Path, default=None, help="Path to config YAML file")
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse and chunk only — no LLM calls"
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        metavar="N",
        help="Parallel chunk requests per language (default: 1)",
    )
    parser.add_argument(
        "--parallel-languages",
        type=int,
        default=1,
        metavar="N",
        dest="parallel_languages",
        help="Run language pipelines concurrently (default: 1)",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        dest="skip_existing",
        help="Skip languages whose output SRT already exists",
    )
    parser.add_argument(
        "--force", action="store_true", help="Overrides --skip-existing / config skip_existing"
    )
    parser.add_argument(
        "--glossary", type=Path, default=None, help="CSV file with term,translation pairs"
    )
    parser.add_argument(
        "--progress-events",
        action="store_true",
        default=False,
        dest="progress_events",
        help="Emit newline-delimited JSON progress events to stdout",
    )

    args = parser.parse_args(argv)
    progress.configure(args.progress_events)

    # ── Resolve input files ───────────────────────────────────────────────────
    if args.input:
        input_paths = args.input
        for p in input_paths:
            if not p.exists():
                print(f"Error: file not found: {p}", file=sys.stderr)
                sys.exit(1)
    else:
        inputs_dir = default_input_root(Path.cwd())
        if not inputs_dir.is_dir():
            print("Error: no input files given and inputs/ directory not found.", file=sys.stderr)
            sys.exit(1)
        input_paths = sorted(inputs_dir.glob("*.srt"))
        if not input_paths:
            print("Error: no .srt files found in inputs/.", file=sys.stderr)
            sys.exit(1)
        print(
            f"Found {len(input_paths)} file(s) in inputs/: {', '.join(p.name for p in input_paths)}"
        )

    config_path = args.config or (
        default_config_path(Path.cwd()) if default_config_path(Path.cwd()).exists() else None
    )
    cfg = load_config(config_path)
    source_lang = args.source or cfg.source_lang

    try:
        target_langs = _resolve_targets(args, cfg)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    if not target_langs and not args.dry_run:
        print(
            "Note: no translation targets configured — only reviewed English (en_US) will be output."
        )

    translation_target_codes = [l.code for l in target_langs if l.code != "en_US"]  # noqa: E741
    progress.emit(
        EventType.JOB_START,
        files=[p.name for p in input_paths],
        targets=translation_target_codes,
    )
    _job_start_time = time.monotonic()

    # ── Dry-run: show chunk summary for each file, no LLM calls ──────────────
    if args.dry_run:
        for input_path in input_paths:
            print(f"\n--- {input_path.name} ---")
            entries = parse_srt(input_path)
            if not entries:
                print("  No entries found.")
                continue
            corpus = strip_and_index(entries)
            style = detect_style(corpus.entry_texts)
            chunks = chunk_entries(
                entries,
                corpus.entry_texts,
                max_chunk_chars=cfg.chunking.max_chunk_chars,
                gap_threshold_ms=cfg.chunking.gap_threshold_ms,
            )
            non_empty = [c for c in chunks if c.source_text.strip()]
            print(
                f"  {len(entries)} entries | Style: {style} | "
                f"{len(chunks)} chunks ({len(non_empty)} non-empty)"
            )
            for i, chunk in enumerate(chunks):
                if not chunk.source_text.strip():
                    print(f"  [{i + 1:3}] EMPTY  entries {chunk.entry_indices}")
                    continue
                preview = chunk.source_text[:80]
                if len(chunk.source_text) > 80:
                    preview += "…"
                entry_range = (
                    f"{chunk.entry_indices[0]}-{chunk.entry_indices[-1]}"
                    if len(chunk.entry_indices) > 1
                    else str(chunk.entry_indices[0])
                )
                print(
                    f"  [{i + 1:3}] entries {entry_range:10} "
                    f"| {len(chunk.source_text):4} chars "
                    f"| {chunk.marker_count} markers"
                )
                print(f"        {preview}")
        translation_targets = [l for l in target_langs if l.code != "en_US"]  # noqa: E741
        if translation_targets:
            print("\n--- Resolved translation targets ---")
            for lang in translation_targets:
                print(f"  {lang.code:8} {lang.prompt_name} (max {lang.max_line_chars} chars/line)")
        else:
            print("\n  (no translation targets — only reviewed English will be output)")
        progress.emit(
            EventType.JOB_DONE, elapsed_ms=int((time.monotonic() - _job_start_time) * 1000)
        )
        return

    # ── Build shared resources ────────────────────────────────────────────────
    configured_output_root = (
        Path(cfg.output.output_root) if cfg.output.output_root else default_output_root(Path.cwd())
    )
    output_root = args.output_root or configured_output_root
    skip_existing = (args.skip_existing or cfg.output.skip_existing) and not args.force
    provider = _build_provider(cfg, args)
    model_display = args.model or cfg.model
    glossary_path = args.glossary or (Path(cfg.glossary) if cfg.glossary else None)
    glossary_terms = _load_glossary_terms(glossary_path)
    glossary_note = _build_glossary_note(glossary_path)

    # ── Process each file ─────────────────────────────────────────────────────
    file_results: list[tuple[str, bool]] = []
    for i, input_path in enumerate(input_paths):
        ok = _process_file(
            input_path=input_path,
            file_idx=i,
            file_total=len(input_paths),
            args=args,
            cfg=cfg,
            target_langs=target_langs,
            source_lang=source_lang,
            provider=provider,
            model_display=model_display,
            glossary_note=glossary_note,
            glossary_terms=glossary_terms,
            output_root=output_root,
            skip_existing=skip_existing,
        )
        file_results.append((input_path.name, ok))

    elapsed_ms = int((time.monotonic() - _job_start_time) * 1000)
    progress.emit(EventType.JOB_DONE, elapsed_ms=elapsed_ms)

    if len(input_paths) > 1:
        print(f"\n{'=' * 60}")
        print(
            f"Batch complete: {sum(ok for _, ok in file_results)}/{len(file_results)} files succeeded."
        )
        for name, ok in file_results:
            print(f"  {'OK' if ok else 'FAILED':6}  {name}")
