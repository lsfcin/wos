# Extract public Dart API surface into a compact .dart.api stub file
import re, sys
from pathlib import Path

TOP = re.compile(
    r'^(?:abstract\s+|final\s+|sealed\s+|base\s+|interface\s+)*'
    r'(?:class|mixin|enum|extension|typedef)\s+(\w)'
)
SKIP = ('import ', 'export ', 'part ', 'library ', '//', '@', 'const ', 'final ')

def extract(src: Path) -> list:
    lines = src.read_text(encoding='utf-8', errors='ignore').splitlines()
    out, in_class = [f'// {src.name}'], False
    for line in lines:
        s = line.strip()
        if not s or any(s.startswith(p) for p in SKIP):
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0:
            if s == '}':
                in_class = False
                continue
            m = TOP.match(s)
            if m and not m.group(1).startswith('_'):
                out.append(s.split('{')[0].strip())
                in_class = True
        elif indent == 2 and in_class:
            if s.startswith('_') or s.startswith('@') or s.startswith('//'):
                continue
            sig = s.split('{')[0].split('=>')[0].strip()
            if sig and re.search(r'\w', sig):
                out.append(f'  {sig}')
    return out

def main():
    if len(sys.argv) < 2:
        sys.exit(1)
    src = Path(sys.argv[1])
    if not src.exists():
        sys.exit(1)
    dst = src.parent / (src.stem + '.dart.api')
    dst.write_text('\n'.join(extract(src)) + '\n', encoding='utf-8', newline='\n')
    print(f'✓ .dart.api: {dst}')

if __name__ == '__main__':
    main()
