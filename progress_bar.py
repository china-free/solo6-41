import sys
from typing import Optional


class ProgressBar:
    def __init__(self, total: int, bar_width: int = 40, prefix: str = "Progress"):
        self.total = total
        self.bar_width = bar_width
        self.prefix = prefix
        self.current = 0
        self._last_line_length = 0

    def update(self, current: Optional[int] = None, message: str = ""):
        if current is not None:
            self.current = current
        else:
            self.current += 1

        if self.total <= 0:
            percent = 100
            filled = self.bar_width
        else:
            percent = int(self.current * 100 / self.total)
            filled = int(self.current * self.bar_width / self.total)

        bar = '█' * filled + '░' * (self.bar_width - filled)
        line = f"\r{self.prefix}: |{bar}| {percent:3d}% ({self.current}/{self.total})"
        if message:
            line += f" {message}"

        line = line[:120]
        if len(line) < self._last_line_length:
            line += ' ' * (self._last_line_length - len(line))
        self._last_line_length = len(line)

        sys.stdout.write(line)
        sys.stdout.flush()

    def finish(self, message: str = "Done"):
        self.update(current=self.total, message=message)
        sys.stdout.write('\n')
        sys.stdout.flush()
