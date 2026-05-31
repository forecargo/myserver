"""単語帳画像のバッチ抽出 CLI。

Usage:
    python main.py                          # sample_jpg/ -> output/
    python main.py -i my_inputs -o my_out   # 入出力ディレクトリ指定
    python main.py --overwrite              # 既存 JSON を上書き
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from pydantic import ValidationError

from config import INPUT_DIR, OUTPUT_DIR
from extractor import extract_from_image

logger = logging.getLogger("vocab_extractor")

# 対象画像拡張子 (大文字小文字は問わない)
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="単語帳画像から JSON を抽出する")
    parser.add_argument(
        "-i",
        "--input-dir",
        type=Path,
        default=INPUT_DIR,
        help=f"入力画像ディレクトリ (default: {INPUT_DIR})",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help=f"出力 JSON ディレクトリ (default: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="既存の出力 JSON を上書きする (デフォルトは存在すればスキップ)",
    )
    parser.add_argument(
        "--rotate",
        type=int,
        choices=(0, 90, 180, 270),
        default=0,
        help=(
            "EXIF 補正後に追加で回す角度 (反時計回り)。"
            "ピクセルが右 90° 倒れているスキャンは 90 を指定"
        ),
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="DEBUG ログを有効化",
    )
    return parser.parse_args(argv)


def find_images(input_dir: Path) -> list[Path]:
    if not input_dir.is_dir():
        raise FileNotFoundError(f"入力ディレクトリが存在しません: {input_dir}")
    images = sorted(
        p for p in input_dir.iterdir() if p.suffix.lower() in IMAGE_SUFFIXES
    )
    return images


def process_image(
    image_path: Path,
    output_dir: Path,
    *,
    overwrite: bool,
    rotate_deg: int = 0,
) -> str:
    """単一画像を抽出して JSON 保存。戻り値はステータス ('ok' / 'skip' / 'error')。"""
    out_path = output_dir / f"{image_path.stem}.json"
    if out_path.exists() and not overwrite:
        logger.info("skip (exists): %s", out_path.name)
        return "skip"

    try:
        result = extract_from_image(image_path, rotate_deg=rotate_deg)
    except ValidationError as exc:
        logger.error("schema validation failed for %s: %s", image_path.name, exc)
        return "error"
    except Exception as exc:  # API エラー / ネットワーク / その他
        logger.error("extraction failed for %s: %s", image_path.name, exc)
        return "error"

    # 個別ファイルへ即座に書き出す → 後続が落ちても既出分は保護される
    out_path.write_text(
        json.dumps(result.model_dump(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    logger.info("wrote %s (%d items)", out_path.name, len(result.vocabulary_list))
    return "ok"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        images = find_images(args.input_dir)
    except FileNotFoundError as exc:
        logger.error(str(exc))
        return 2

    if not images:
        logger.warning("入力画像が見つかりません: %s", args.input_dir)
        return 0

    args.output_dir.mkdir(parents=True, exist_ok=True)
    logger.info("found %d image(s) in %s", len(images), args.input_dir)

    counts = {"ok": 0, "skip": 0, "error": 0}
    for image_path in images:
        logger.info("processing %s ...", image_path.name)
        status = process_image(
            image_path,
            args.output_dir,
            overwrite=args.overwrite,
            rotate_deg=args.rotate,
        )
        counts[status] += 1

    logger.info(
        "done: ok=%d skip=%d error=%d (total=%d)",
        counts["ok"],
        counts["skip"],
        counts["error"],
        len(images),
    )
    return 0 if counts["error"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
