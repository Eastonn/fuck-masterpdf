#!/usr/bin/env python3
"""
Удаление водяного знака "Created in Master PDF Editor" из PDF-файлов.

Использование через uv:
    uv run remove_watermark.py input.pdf
    uv run remove_watermark.py input.pdf -o output.pdf
    uv run remove_watermark.py *.pdf
"""

import argparse
import re
import sys
from pathlib import Path

import pikepdf


def find_watermark_xobjects(page):
    """Находит Form XObject'ы с водяным знаком Master PDF Editor.

    Универсальный паттерн (EN/RU/любая локаль):
    - Form XObject с красным цветом (1 0 0 rg или 1 0 0 scn)
    - содержит только текстовый блок BT...ET с hex-глифами <xxxx>Tj
    - обёрнут в q...Q (save/restore graphics state)
    """
    watermark_names = []

    resources = page.get("/Resources")
    if not resources or "/XObject" not in resources:
        return watermark_names

    for name, xobj in resources["/XObject"].items():
        if xobj.get("/Subtype") != "/Form":
            continue
        try:
            data = xobj.read_bytes().decode("latin-1")
        except Exception:
            continue

        has_red = "1 0 0 rg" in data or "1 0 0 scn" in data
        has_hex_glyphs = bool(re.search(r"<[0-9A-Fa-f]{4,}>Tj", data))
        has_text_block = "BT" in data and "ET" in data
        if has_red and has_hex_glyphs and has_text_block:
            watermark_names.append(name)

    return watermark_names


def remove_watermark(input_path, output_path):
    """Удаляет водяной знак из PDF. Возвращает количество очищенных страниц."""
    pdf = pikepdf.open(input_path)
    cleaned = 0

    for page in pdf.pages:
        wm_xobjects = find_watermark_xobjects(page)
        if not wm_xobjects:
            continue

        contents = page.get("/Contents")
        if contents is None:
            continue

        if isinstance(contents, pikepdf.Array):
            raw = b""
            for stream in contents:
                raw += stream.read_bytes()
        else:
            raw = contents.read_bytes()

        text = raw.decode("latin-1")

        for xobj_name in wm_xobjects:
            escaped = re.escape(xobj_name)
            pattern = (
                r"q\s+"
                r"[\d.\-]+\s+[\d.\-]+\s+[\d.\-]+\s+[\d.\-]+\s+"
                r"[\d.\-]+\s+[\d.\-]+\s+cm\s+"
                r"(?:/\w+\s+gs\s*)?"
                rf"{escaped}\s+Do\s+Q\s*\n?"
            )
            text = re.sub(pattern, "", text)

        page["/Contents"] = pdf.make_stream(text.encode("latin-1"))

        xobjects = page["/Resources"]["/XObject"]
        for name in wm_xobjects:
            if name in xobjects:
                del xobjects[name]

        cleaned += 1

    if cleaned == 0:
        return 0

    pdf.save(output_path)
    return cleaned


def main():
    parser = argparse.ArgumentParser(
        description='Удаление водяного знака "Created in Master PDF Editor" из PDF'
    )
    parser.add_argument("files", nargs="+", help="PDF-файлы для обработки")
    parser.add_argument(
        "-o", "--output",
        help="Выходной файл (только для одного входного). По умолчанию: имя_clean.pdf",
    )
    parser.add_argument(
        "--suffix", default="_clean",
        help="Суффикс для выходных файлов (по умолчанию: _clean)",
    )
    parser.add_argument(
        "--inplace", action="store_true",
        help="Перезаписать исходные файлы (создаёт .bak-копию)",
    )

    args = parser.parse_args()

    if args.output and len(args.files) > 1:
        print("Ошибка: -o/--output можно использовать только с одним файлом")
        sys.exit(1)

    total = 0
    for filepath in args.files:
        path = Path(filepath)
        if not path.exists():
            print(f"  Файл не найден: {filepath}")
            continue
        if path.suffix.lower() != ".pdf":
            print(f"  Не PDF: {filepath}")
            continue

        if args.output:
            output_path = args.output
        elif args.inplace:
            backup = path.with_suffix(".pdf.bak")
            path.rename(backup)
            filepath = str(backup)
            output_path = str(path)
        else:
            output_path = str(path.with_stem(path.stem + args.suffix))

        print(f"{path.name}:")
        result = remove_watermark(filepath, output_path)
        if result > 0:
            orig = Path(filepath).stat().st_size
            new = Path(output_path).stat().st_size
            print(f"  Очищено страниц: {result}")
            print(f"  Размер: {orig // 1024} KB → {new // 1024} KB")
            print(f"  Сохранено: {output_path}")
            total += result
        else:
            print("  Водяной знак не найден")
        print()

    if total > 0:
        print(f"Готово. Обработано страниц: {total}")
    else:
        print("Водяные знаки не найдены.")
        sys.exit(1)


if __name__ == "__main__":
    main()
