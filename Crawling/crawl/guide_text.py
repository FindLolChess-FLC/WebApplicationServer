"""Convert authored guide markup to readable plain text."""
import re
from html.parser import HTMLParser


class _GuideText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in ('script', 'style'):
            self.hidden += 1
        elif not self.hidden:
            if tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4'):
                self.parts.append('\n\n')
            elif tag in ('br', 'hr'):
                self.parts.append('\n')
            elif tag == 'li':
                self.parts.append('\n• ')

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)
        elif not self.hidden and tag in ('p', 'div', 'h1', 'h2', 'h3', 'h4', 'li'):
            self.parts.append('\n\n')

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)

    def text(self):
        text = re.sub(r'[ \t\xa0]+', ' ', ''.join(self.parts))
        text = '\n'.join(line.strip() for line in text.splitlines())
        return re.sub(r'\n{3,}', '\n\n', text).strip()


def guide_text(html):
    parser = _GuideText()
    parser.feed(html)
    return parser.text()
