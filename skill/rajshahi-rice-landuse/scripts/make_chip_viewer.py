#!/usr/bin/env python3
"""Build a static HTML viewer for the interpretation chips.

Writes `index.html` into the chips directory, grouping images by season and
showing every chip with a search box. The page uses relative image paths, so it
must be opened from the same directory (or served).

Usage
-----
    python make_chip_viewer.py --year 2020
    cd "$RAJSHAHI_RICE_DATA_ROOT/rajshahi-rice/chips/2020"
    python -m http.server 8000
    # then open the forwarded port in your browser
"""

from __future__ import annotations

import argparse
import html
import os
from pathlib import Path

SEASONS = ("BORO", "AMAN", "AUS")
TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Rajshahi reference chips {year}</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 1rem; background: #f7f7f5; }}
  h1 {{ font-size: 1.2rem; }}
  .controls {{ position: sticky; top: 0; background: #f7f7f5; padding: .5rem 0; z-index: 2; }}
  input {{ padding: .4rem; width: 16rem; }}
  section {{ margin-top: 2rem; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: .75rem; }}
  figure {{ margin: 0; background: #fff; border: 1px solid #ddd; padding: .4rem; }}
  img {{ width: 100%; height: auto; display: block; }}
  figcaption {{ font-size: .8rem; color: #444; padding-top: .3rem; }}
</style>
</head>
<body>
<h1>Reference chips {year}</h1>
<div class="controls">
  <input id="q" placeholder="Filter by sample id, e.g. S2020-0041">
  <span id="count"></span>
</div>
{sections}
<script>
const q = document.getElementById('q');
const figures = Array.from(document.querySelectorAll('figure'));
const count = document.getElementById('count');
function apply() {{
  const term = q.value.trim().toUpperCase();
  let shown = 0;
  for (const f of figures) {{
    const match = !term || f.dataset.id.toUpperCase().includes(term);
    f.style.display = match ? '' : 'none';
    if (match) shown++;
  }}
  count.textContent = shown + ' shown';
}}
q.addEventListener('input', apply);
apply();
</script>
</body>
</html>
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, default=2020)
    parser.add_argument(
        "--data-root",
        default=os.environ.get(
            "RAJSHAHI_RICE_DATA_ROOT", "/home/coder/research-runtime/rajshahi-rice"
        ),
    )
    args = parser.parse_args()

    root = Path(args.data_root).expanduser().resolve() / "chips" / str(args.year)
    if not root.exists():
        print(f"chips directory not found: {root}")
        return 2

    sections = []
    for season in SEASONS:
        directory = root / season
        if not directory.exists():
            continue
        figures = []
        for image in sorted(directory.glob("*.png")):
            sample = image.stem
            figures.append(
                f'<figure data-id="{html.escape(sample)}">'
                f'<a href="{season}/{image.name}"><img loading="lazy" '
                f'src="{season}/{image.name}" alt="{html.escape(sample)}"></a>'
                f"<figcaption>{html.escape(sample)} · {season}</figcaption></figure>"
            )
        sections.append(
            f"<section><h2>{season} ({len(figures)} chips)</h2>"
            f'<div class="grid">{"".join(figures)}</div></section>'
        )

    output = root / "index.html"
    output.write_text(
        TEMPLATE.format(year=args.year, sections="\n".join(sections)), encoding="utf-8"
    )
    print(f"viewer: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
