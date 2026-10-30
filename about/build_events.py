#!/usr/bin/env python3
"""
build_events.py
---------------
1. Reads a CSV file (columns: title, photo, url).
2. Converts it to a JS array-of-objects literal (e.g. eventsData).
3. Finds the existing `const eventsData = [ ... ];` block inside your HTML
   template and replaces it with the freshly generated data.
   - If no such block exists yet, it inserts one right before </script>.
4. Writes the result to the output HTML file, OVERWRITING it if it exists.

Usage:
    python build_events.py events.csv template.html index.html --var eventsData
"""

import argparse
import csv
import json
import re
import sys


def js_string_literal(value: str) -> str:
    if value is None:
        value = ""
    # Returns a valid double-quoted JS string literal
    return json.dumps(str(value), ensure_ascii=False)


def read_csv_rows(csv_path: str):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV file has no header row / no columns detected.")
        rows = [row for row in reader]
        return reader.fieldnames, rows


def build_js_block(rows, fields, var_name):
    lines = [f"    const {var_name} = ["]
    for i, row in enumerate(rows):
        # Generates structured rows like: { "title": "...", "photo": "...", "url": "..." }
        parts = [f'{js_string_literal(field)}: {js_string_literal(row.get(field, ""))}' for field in fields]
        comma = "," if i < len(rows) - 1 else ""
        lines.append("      { " + ", ".join(parts) + " }" + comma)
    lines.append("    ];")
    return "\n".join(lines)


def inject_into_html(html_text, js_block, var_name):
    # Matches: const <var_name> = [ ... ]; across multiple lines
    pattern = re.compile(
        r"const\s+" + re.escape(var_name) + r"\s*=\s*\[.*?\]\s*;",
        re.DOTALL
    )

    if pattern.search(html_text):
        new_html = pattern.sub(js_block, html_text, count=1)
    else:
        # Fallback: insert just before the first closing </script>
        insertion_point = html_text.find("</script>")
        if insertion_point == -1:
            script_wrapped = f"<script>\n  {js_block}\n</script>\n"
            if "</body>" in html_text:
                new_html = html_text.replace("</body>", script_wrapped + "</body>")
            else:
                new_html = html_text + "\n" + script_wrapped
        else:
            new_html = html_text[:insertion_point] + "  " + js_block + "\n" + html_text[insertion_point:]

    return new_html


def main():
    parser = argparse.ArgumentParser(description="Compile CSV -> JS -> HTML for CAC Events.")
    parser.add_argument("input_csv", help="Path to input CSV file")
    parser.add_argument("template_html", help="Path to source HTML template")
    parser.add_argument("output_html", help="Path to output HTML file (overwritten)")
    parser.add_argument("--var", default="eventsData", help="JS variable name (default: eventsData)")
    parser.add_argument("--fields", default=None, help="Comma-separated column order override")
    args = parser.parse_args()

    try:
        fieldnames, rows = read_csv_rows(args.input_csv)
    except Exception as e:
        sys.exit(f"Error reading CSV: {e}")

    if args.fields:
        fields = [f.strip() for f in args.fields.split(",")]
        missing = [f for f in fields if f not in fieldnames]
        if missing:
            sys.exit(f"Error: requested field(s) not found in CSV header: {missing}\n"
                     f"CSV header columns are: {fieldnames}")
    else:
        # Enforces order matching your template keys: title, photo, url, button
        preferred_order = ["title", "photo", "url", "button"]
        fields = [f for f in preferred_order if f in fieldnames] + [f for f in fieldnames if f not in preferred_order]

    js_block = build_js_block(rows, fields, args.var)

    with open(args.template_html, "r", encoding="utf-8") as f:
        html_text = f.read()

    new_html = inject_into_html(html_text, js_block, args.var)

    with open(args.output_html, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"Successfully compiled {len(rows)} records from '{args.input_csv}' into '{args.output_html}' "
          f"(variable: {args.var}).")


if __name__ == "__main__":
    main()