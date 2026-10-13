"""共用：讓腳本在任何主控台（含 Windows cp950）都能輸出中文與 ✓ ✗ 符號。

每支腳本開頭 `import _utf8` 即可；無法重新設定編碼的環境會靜默略過。
"""
import sys

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
