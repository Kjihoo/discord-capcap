class CaptionManager:
    def __init__(self, max_chars_per_line=25, max_lines=2):
        self.max_chars_per_line = max_chars_per_line
        self.max_lines = max_lines
        self.lines: list[str] = []

    def push(self, text: str) -> str | None:
        if not text:
            return None

        words = text.split()
        for word in words:
            if not self.lines:
                self.lines.append(word)
            elif len(self.lines[-1]) + len(word) + 1 <= self.max_chars_per_line:
                self.lines[-1] += " " + word
            else:
                self.lines.append(word)

            if len(self.lines) > self.max_lines:
                self.lines.pop(0)

        return "\n".join(self.lines)
