#!/bin/bash
# Регенерація PDF гайдів з .md файлів
# Запуск: ./scripts/regen_docs.sh
#
# Залежності: pandoc, chromium (headless), fonts-noto-color-emoji, fonts-symbola
# Шрифти ставляться через: sudo apt install fonts-noto-color-emoji ttf-ancient-fonts

set -e
cd "$(dirname "$0")/.."

PROJECT_DIR="$(pwd)"
DOCS_DIR="$PROJECT_DIR/data/docs"
mkdir -p "$DOCS_DIR"

# CSS у тимчасовий файл (один на обидва PDF)
CSS_FILE=$(mktemp --suffix=.css)
cat > "$CSS_FILE" << 'CSSEOF'
@page { margin: 2cm; size: A4; background: #f5f5f5; }
html { background: #f5f5f5; }
body {
  font-family: "DejaVu Sans", "Noto Color Emoji", sans-serif;
  line-height: 1.55;
  color: #222;
  max-width: 800px;
  margin: auto;
  background: #f5f5f5;
  padding: 1em;
}
h1 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.3em; }
h2 { color: #34495e; border-bottom: 1px solid #ccc; padding-bottom: 0.2em; margin-top: 1.5em; }
h3 { color: #555; }
code {
  background: #ebebeb;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 0.9em;
  font-family: "DejaVu Sans Mono", monospace;
}
pre {
  background: #ebebeb;
  border: 1px solid #d0d0d0;
  padding: 1em;
  border-radius: 4px;
  overflow-x: auto;
}
pre code { background: transparent; padding: 0; }
table { border-collapse: collapse; margin: 1em 0; background: #ffffff; }
th, td { border: 1px solid #ccc; padding: 8px 12px; text-align: left; }
th { background: #e8e8e8; }
blockquote {
  border-left: 4px solid #3498db;
  padding: 0.5em 1em;
  color: #444;
  margin-left: 0;
  background: #ebebeb;
  border-radius: 0 4px 4px 0;
}
ul, ol { padding-left: 1.5em; }
hr { border: 0; border-top: 1px solid #ccc; margin: 2em 0; }
a { color: #2980b9; text-decoration: none; }
CSSEOF

regen_pdf() {
    local md_file="$1"
    local pdf_name="$2"
    local title="$3"
    local html_file="/tmp/${pdf_name%.pdf}.html"
    local pdf_path="$DOCS_DIR/$pdf_name"

    echo "→ $md_file → $pdf_name"

    pandoc "$md_file" \
        -o "$html_file" \
        --standalone \
        --metadata title="$title" \
        -V lang=uk \
        --css="$CSS_FILE"

    chromium --headless --disable-gpu --no-sandbox \
        --print-to-pdf="$pdf_path" \
        --print-to-pdf-no-header \
        --no-pdf-header-footer \
        "file://$html_file" 2>&1 | grep -v "no-decommit" | tail -2

    if [ -f "$pdf_path" ]; then
        local size=$(du -h "$pdf_path" | cut -f1)
        echo "  ✓ $pdf_path ($size)"
    else
        echo "  ✗ FAILED"
        return 1
    fi
}

echo "=== Регенерація PDF гайдів ==="
regen_pdf "ADMIN_GUIDE.md" "admin_guide.pdf" "Адмінка InSilver v3 — інструкція для Влада"
regen_pdf "USER_GUIDE.md" "user_guide.pdf" "Інструкція для клієнтів — InSilver"

# Cleanup
rm -f "$CSS_FILE"

echo ""
echo "=== Готово. Файли у $DOCS_DIR ==="
ls -la "$DOCS_DIR"/*.pdf
