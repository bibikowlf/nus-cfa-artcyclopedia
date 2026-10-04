#!/usr/bin/env python3
"""
build_venues.py
---------------
1. Reads an unrolled CSV file (flexible header matching for venue details).
2. Converts it into a structured JS array-of-objects literal (e.g. venuesData).
3. Resolves photo paths to point to relative directory (../photos/venues/).
4. Finds the existing `const venuesData = [ ... ];` block inside your HTML template
   and injects the new data.
5. Writes the result to the output HTML file.
"""

import argparse
import csv
import json
import os
import re
import sys


def js_string_literal(value: str) -> str:
    return json.dumps(str(value or ""), ensure_ascii=False)


def expand_escaped_newlines(value: str) -> str:
    return re.sub(r"\\r\\n|\\n|\\r", "\n", str(value or ""))


def parse_capacity(raw_cap: str) -> int:
    """Extracts the highest integer found in a capacity string (e.g., '1607 - 1710 pax' -> 1710)."""
    if not raw_cap:
        return 0
    numbers = [int(n) for n in re.findall(r"\d+", str(raw_cap))]
    return max(numbers) if numbers else 0


def format_image_path(raw_img: str) -> str:
    """Formats image filename to point to sibling photos/venues directory relative to venues/."""
    if not raw_img:
        return ""
    
    # If path already contains relative or absolute routing, leave it as is
    if "/" in raw_img or "\\" in raw_img:
        return raw_img.replace("\\", "/")
    
    # Prepend folder path for clean folder separation
    return f"../photos/venue/{raw_img}"


def read_csv_rows(csv_path: str):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise ValueError("CSV file has no header row detected.")
        
        normalized_rows = []
        for row in reader:
            norm_row = {k.strip().lower(): (v or "").strip() for k, v in row.items() if k}
            normalized_rows.append(norm_row)
        return normalized_rows


def validate_clusters(venue_rows, cluster_rows):
    venue_clusters = {row.get("cluster", "") for row in venue_rows}
    clusters = {row.get("cluster", "") for row in cluster_rows}
    alerts = []

    for cluster in sorted(venue_clusters - clusters):
        alerts.append(f"ALERT: Venue cluster '{cluster}' does not appear in clusters.csv.")
    for cluster in sorted(clusters - venue_clusters):
        alerts.append(f"ALERT: Cluster '{cluster}' in clusters.csv is not used by any venue.")

    return alerts


def build_venues_js_block(rows, var_name):
    lines = [f"    const {var_name} = ["]
    for i, row in enumerate(rows):
        cluster = row.get("cluster", "")
        subcategory = row.get("subcategory") or ""
        
        # Handle header variations for venue name
        venue_name = row.get("venue") or ""
        
        # Parse capacity flexibly
        raw_cap = row.get("capacity", "")
        capacity = parse_capacity(raw_cap)
        
        # Extract additional fields
        booking = expand_escaped_newlines(row.get("booking") or "")
        hours = expand_escaped_newlines(row.get("hours") or "")
        notes = expand_escaped_newlines(row.get("notes") or row.get("remarks") or "")

        # Process image path
        raw_image = row.get("image") or ""
        image_path = format_image_path(raw_image)

        item_str = (
            f'{{ '
            f'cluster: {js_string_literal(cluster)}, '
            f'subcategory: {js_string_literal(subcategory)}, '
            f'name: {js_string_literal(venue_name)}, '
            f'capacity: {capacity}, '
            f'image: {js_string_literal(image_path)}, '
            f'hours: {js_string_literal(hours)}, '
            f'booking: {js_string_literal(booking)}, '
            f'notes: {js_string_literal(notes)} '
            f'}}'
        )
        comma = "," if i < len(rows) - 1 else ""
        lines.append(item_str + comma)
    lines.append("    ];")
    return "\n".join(lines)


def build_clusters_js_block(rows):
    lines = ["    const clustersData = ["]
    for i, row in enumerate(rows):
        item_str = (
            f'{{ '
            f'cluster: {js_string_literal(row.get("cluster", ""))}, '
            f'notes: {js_string_literal(expand_escaped_newlines(row.get("notes", "")))}, '
            f'image: {js_string_literal(format_image_path(row.get("image", "")))} '
            f'}}'
        )
        comma = "," if i < len(rows) - 1 else ""
        lines.append(item_str + comma)
    lines.append("    ];")
    return "\n".join(lines)


def inject_into_html(html_text, js_block, var_name):
    pattern = re.compile(
        r"const\s+" + re.escape(var_name) + r"\s*=\s*\[.*?\]\s*;",
        re.DOTALL
    )

    if pattern.search(html_text):
        new_html = pattern.sub(lambda _: js_block, html_text, count=1)
    else:
        insertion_point = html_text.find("</script>")
        if insertion_point == -1:
            script_wrapped = f"<script>\n  {js_block}\n</script>\n"
            if "body" in html_text:
                new_html = html_text.replace("</body>", script_wrapped + "</body>")
            else:
                new_html = html_text + "\n" + script_wrapped
        else:
            new_html = html_text[:insertion_point] + "  " + js_block + "\n" + html_text[insertion_point:]

    return new_html


def main():
    parser = argparse.ArgumentParser(description="Compile CSV -> JS -> HTML for CAC Venues.")
    parser.add_argument("input_csv", help="Path to input CSV file")
    parser.add_argument("template_html", help="Path to source HTML template")
    parser.add_argument("output_html", help="Path to output HTML file")
    parser.add_argument("--var", default="venuesData", help="JS variable name")
    parser.add_argument("--clusters-csv", help="Path to cluster notes CSV")
    args = parser.parse_args()

    try:
        venue_rows = read_csv_rows(args.input_csv)
    except Exception as e:
        sys.exit(f"Error reading venues CSV: {e}")

    clusters_csv = args.clusters_csv or os.path.join(
        os.path.dirname(args.input_csv), "clusters.csv"
    )
    try:
        cluster_rows = read_csv_rows(clusters_csv)
    except Exception as e:
        sys.exit(f"Error reading clusters CSV: {e}")

    for alert in validate_clusters(venue_rows, cluster_rows):
        print(alert, file=sys.stderr)

    venues_js_block = build_venues_js_block(venue_rows, args.var)
    clusters_js_block = build_clusters_js_block(cluster_rows)

    with open(args.template_html, "r", encoding="utf-8") as f:
        html_text = f.read()

    new_html = inject_into_html(html_text, venues_js_block, args.var)
    new_html = inject_into_html(new_html, clusters_js_block, "clustersData")

    with open(args.output_html, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(
        f"Successfully compiled {len(venue_rows)} venues and "
        f"{len(cluster_rows)} clusters into '{args.output_html}'."
    )


if __name__ == "__main__":
    main()