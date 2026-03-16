from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

# Ensure project root is importable in script mode and frozen mode.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
