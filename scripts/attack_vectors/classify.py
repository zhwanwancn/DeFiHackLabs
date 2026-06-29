#!/usr/bin/env python3
"""Extract PoC context and classify attack vectors via OpenAI."""

from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from openai import AsyncOpenAI

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_SRC = REPO_ROOT / "src" / "test"
DEFAULT_OUTPUT = SCRIPT_DIR / "output"
TAXONOMY_PATH = SCRIPT_DIR / "taxonomy.yaml"

ROOT_CAUSE_PATTERNS = [
    re.compile(r"Root cause\s*[:：]\s*(.+)", re.IGNORECASE),
    re.compile(r"root cause\s*[:：]\s*(.+)", re.IGNORECASE),
    re.compile(r"Vulnerability\s*[:：]\s*(.+)", re.IGNORECASE),
    re.compile(r"@Vulnerability\s*(.+)", re.IGNORECASE),
]

CODE_HINTS = [
    ("flashLoan", "flash-loan-assisted"),
    ("flashloan", "flash-loan-assisted"),
    ("FLASH_LOAN", "flash-loan-assisted"),
    ("skim(", "liquidity-pool-manipulation"),
    ("getReserves(", "price-oracle-manipulation"),
    ("initWallet(", "uninitialized-contract"),
    ("initialize(", "uninitialized-contract"),
    ("delegatecall", "arbitrary-external-call"),
    ("permit(", "signature-approval-abuse"),
]


@dataclass
class PoCContext:
    path: str
    header_comments: str = ""
    root_cause_hints: list[str] = field(default_factory=list)
    code_hints: list[str] = field(default_factory=list)
    exploit_snippet: str = ""
    line_count: int = 0


@dataclass
class Classification:
    path: str
    attack_vectors: list[str]
    primary_vector: str
    root_cause: str
    confidence: float
    model: str
    classified_at: str
    error: str = ""


def load_taxonomy(path: Path = TAXONOMY_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def taxonomy_prompt_block(taxonomy: dict[str, Any]) -> str:
    lines = ["Allowed attack vector IDs (use only these):"]
    for vid, meta in taxonomy["attack_vectors"].items():
        lines.append(f"- {vid}: {meta['name_en']} — {meta['description']}")
    for rule in taxonomy.get("rules", []):
        lines.append(f"Rule: {rule}")
    return "\n".join(lines)


def discover_poc_files(src_dir: Path) -> list[Path]:
    files = sorted(src_dir.rglob("*exp*.sol"))
    return [p for p in files if p.is_file() and "/KyberSwap/interfaces/" not in str(p)]


def extract_header_comments(text: str, max_lines: int = 120) -> str:
    lines: list[str] = []
    for line in text.splitlines()[:max_lines]:
        stripped = line.strip()
        if stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
            lines.append(line)
        elif stripped == "" and lines:
            lines.append(line)
        elif lines and not stripped.startswith("contract ") and not stripped.startswith("interface "):
            if stripped.startswith("import "):
                break
            if stripped and not stripped.startswith("pragma "):
                break
    return "\n".join(lines).strip()


def extract_root_cause_hints(text: str) -> list[str]:
    hints: list[str] = []
    for pattern in ROOT_CAUSE_PATTERNS:
        for match in pattern.finditer(text):
            hint = match.group(1).strip().rstrip("*/").strip()
            if hint and hint not in hints:
                hints.append(hint[:500])
    return hints


def extract_code_hints(text: str) -> list[str]:
    found: list[str] = []
    lower = text.lower()
    for needle, label in CODE_HINTS:
        if needle.lower() in lower and label not in found:
            found.append(label)
    return found


def extract_exploit_snippet(text: str, max_chars: int = 6000) -> str:
    match = re.search(
        r"function\s+test(?:Exploit|PoC|Attack)\s*\([^)]*\)[^{]*\{",
        text,
        re.IGNORECASE,
    )
    if not match:
        match = re.search(r"function\s+run\s*\([^)]*\)[^{]*\{", text)
    if match:
        start = match.start()
        return text[start : start + max_chars]
    return text[:max_chars]


def build_context(path: Path, repo_root: Path = REPO_ROOT) -> PoCContext:
    rel = path.relative_to(repo_root).as_posix()
    text = path.read_text(encoding="utf-8", errors="replace")
    return PoCContext(
        path=rel,
        header_comments=extract_header_comments(text),
        root_cause_hints=extract_root_cause_hints(text),
        code_hints=extract_code_hints(text),
        exploit_snippet=extract_exploit_snippet(text),
        line_count=len(text.splitlines()),
    )


def context_to_prompt(ctx: PoCContext) -> str:
    parts = [f"File: {ctx.path}", f"Lines: {ctx.line_count}"]
    if ctx.header_comments:
        parts.append(f"Header comments:\n{ctx.header_comments}")
    if ctx.root_cause_hints:
        parts.append("Extracted root cause hints:\n- " + "\n- ".join(ctx.root_cause_hints))
    if ctx.code_hints:
        parts.append("Code pattern hints: " + ", ".join(ctx.code_hints))
    if ctx.exploit_snippet:
        parts.append(f"Exploit function snippet:\n```solidity\n{ctx.exploit_snippet}\n```")
    return "\n\n".join(parts)


def valid_vector_ids(taxonomy: dict[str, Any]) -> set[str]:
    return set(taxonomy["attack_vectors"].keys())


def normalize_classification(raw: dict[str, Any], valid_ids: set[str]) -> tuple[list[str], str]:
    vectors = raw.get("attack_vectors") or []
    cleaned: list[str] = []
    for v in vectors:
        v = str(v).strip().upper()
        if v in valid_ids and v not in cleaned:
            cleaned.append(v)
    primary = str(raw.get("primary_vector", "")).strip().upper()
    if primary not in valid_ids and cleaned:
        primary = cleaned[0]
    elif primary not in valid_ids:
        primary = cleaned[0] if cleaned else "AV05"
    if primary and primary not in cleaned:
        cleaned.insert(0, primary)
    if not cleaned:
        cleaned = ["AV05"]
    return cleaned[:3], primary or cleaned[0]


async def classify_one(
    client: AsyncOpenAI,
    ctx: PoCContext,
    taxonomy: dict[str, Any],
    model: str,
) -> Classification:
    valid_ids = valid_vector_ids(taxonomy)
    system = (
        "You classify DeFi hack PoC files into standardized attack vectors. "
        "Return strict JSON only."
    )
    user = (
        f"{taxonomy_prompt_block(taxonomy)}\n\n"
        "Analyze this Foundry PoC and return JSON:\n"
        "{\n"
        '  "attack_vectors": ["AVxx", ...],\n'
        '  "primary_vector": "AVxx",\n'
        '  "root_cause": "one sentence in English",\n'
        '  "confidence": 0.0-1.0\n'
        "}\n\n"
        f"{context_to_prompt(ctx)}"
    )
    now = datetime.now(timezone.utc).isoformat()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content or "{}"
        raw = json.loads(content)
        vectors, primary = normalize_classification(raw, valid_ids)
        return Classification(
            path=ctx.path,
            attack_vectors=vectors,
            primary_vector=primary,
            root_cause=str(raw.get("root_cause", "")).strip()[:500],
            confidence=float(raw.get("confidence", 0.7)),
            model=model,
            classified_at=now,
        )
    except Exception as exc:  # noqa: BLE001
        return Classification(
            path=ctx.path,
            attack_vectors=["AV05"],
            primary_vector="AV05",
            root_cause="classification failed",
            confidence=0.0,
            model=model,
            classified_at=now,
            error=str(exc),
        )


def load_cache(cache_path: Path) -> dict[str, Classification]:
    if not cache_path.exists():
        return {}
    cached: dict[str, Classification] = {}
    with cache_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            cached[data["path"]] = Classification(**data)
    return cached


def append_cache(cache_path: Path, item: Classification) -> None:
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")


def write_labels_csv(labels: list[Classification], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "contract_path",
                "attack_vectors",
                "primary_vector",
                "root_cause",
                "confidence",
                "model",
                "classified_at",
                "error",
            ],
        )
        writer.writeheader()
        for item in sorted(labels, key=lambda x: x.path):
            writer.writerow(
                {
                    "contract_path": item.path,
                    "attack_vectors": ",".join(item.attack_vectors),
                    "primary_vector": item.primary_vector,
                    "root_cause": item.root_cause,
                    "confidence": item.confidence,
                    "model": item.model,
                    "classified_at": item.classified_at,
                    "error": item.error,
                }
            )


def write_ranking(
    labels: list[Classification],
    taxonomy: dict[str, Any],
    out_path: Path,
    *,
    count_mode: str = "case",
) -> dict[str, int]:
    """count_mode: 'case' = each case counts once per vector; 'primary' = primary only."""
    counter: Counter[str] = Counter()
    total_cases = len(labels)
    errors = sum(1 for x in labels if x.error)

    for item in labels:
        if count_mode == "primary":
            counter[item.primary_vector] += 1
        else:
            for v in item.attack_vectors:
                counter[v] += 1

    av_meta = taxonomy["attack_vectors"]
    rows = counter.most_common()

    lines = [
        "# DeFiHackLabs Attack Vector Ranking",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"Total PoC cases: {total_cases}",
        f"Classification errors: {errors}",
        f"Count mode: `{count_mode}` (each vector tag per case)",
        "",
        "## Ranking (descending by occurrence)",
        "",
        "| Rank | ID | Attack Vector (EN) | 中文 | Count | % of Cases |",
        "|------|-----|-------------------|------|-------|------------|",
    ]
    for rank, (vid, count) in enumerate(rows, start=1):
        meta = av_meta.get(vid, {})
        pct = (count / total_cases * 100) if total_cases else 0
        lines.append(
            f"| {rank} | {vid} | {meta.get('name_en', '?')} | "
            f"{meta.get('name_zh', '?')} | {count} | {pct:.1f}% |"
        )

    lines.extend(["", "## Top examples per vector", ""])
    by_vector: dict[str, list[Classification]] = {}
    for item in labels:
        key = item.primary_vector
        by_vector.setdefault(key, []).append(item)

    for vid, _ in rows[:10]:
        examples = by_vector.get(vid, [])[:3]
        if not examples:
            continue
        meta = av_meta.get(vid, {})
        lines.append(f"### {vid} — {meta.get('name_en', vid)}")
        for ex in examples:
            lines.append(f"- `{ex.path}` — {ex.root_cause}")
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return dict(counter)


async def run_classify(args: argparse.Namespace) -> int:
    load_dotenv(REPO_ROOT / ".env")
    load_dotenv(SCRIPT_DIR / ".env")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set", file=sys.stderr)
        return 1

    taxonomy = load_taxonomy()
    src_dir = Path(args.src_dir)
    output_dir = Path(args.output_dir)
    cache_path = output_dir / "labels.jsonl"
    csv_path = output_dir / "attack_vector_labels.csv"
    ranking_path = output_dir / "attack_vector_ranking.md"

    all_files = discover_poc_files(src_dir)
    if args.limit:
        all_files = all_files[: args.limit]

    cached = load_cache(cache_path) if args.resume else {}
    pending: list[PoCContext] = []
    for path in all_files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel not in cached:
            pending.append(build_context(path, REPO_ROOT))

    print(f"Total files: {len(all_files)}, cached: {len(cached)}, pending: {len(pending)}")

    client = AsyncOpenAI(api_key=api_key)
    sem = asyncio.Semaphore(args.concurrency)

    async def worker(ctx: PoCContext) -> Classification:
        async with sem:
            result = await classify_one(client, ctx, taxonomy, args.model)
            append_cache(cache_path, result)
            print(f"  [{result.primary_vector}] {ctx.path}")
            return result

    if pending:
        results = await asyncio.gather(*[worker(ctx) for ctx in pending])
        for r in results:
            cached[r.path] = r

    labels = [cached[path.relative_to(REPO_ROOT).as_posix()] for path in all_files if path.relative_to(REPO_ROOT).as_posix() in cached]
    write_labels_csv(labels, csv_path)
    write_ranking(labels, taxonomy, ranking_path, count_mode=args.count_mode)
    primary_ranking_path = output_dir / "attack_vector_ranking_primary.md"
    write_ranking(labels, taxonomy, primary_ranking_path, count_mode="primary")

    print(f"\nWrote {csv_path}")
    print(f"Wrote {ranking_path}")
    print(f"Wrote {primary_ranking_path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Classify DeFiHackLabs PoC attack vectors")
    parser.add_argument("--src-dir", default=str(DEFAULT_SRC))
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--model", default="gpt-4o-mini")
    parser.add_argument("--concurrency", type=int, default=8)
    parser.add_argument("--limit", type=int, default=0, help="Max files (0 = all)")
    parser.add_argument("--resume", action="store_true", help="Skip paths already in labels.jsonl")
    parser.add_argument(
        "--count-mode",
        choices=["case", "primary"],
        default="case",
        help="Ranking count: all tags per case vs primary only",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.limit == 0:
        args.limit = None  # type: ignore[assignment]
    return asyncio.run(run_classify(args))


if __name__ == "__main__":
    raise SystemExit(main())
