import re

KEYWORDS = {"let", "fn", "if", "else", "while", "for", "in", "return", "break",
            "continue", "true", "false", "nil", "and", "or", "not"}

TOKEN = re.compile(r'''
    (?P<ws>[ \t\r]+|\#[^\n]*)
  | (?P<nl>\n)
  | (?P<num>\d+(?:\.\d+)?)
  | (?P<str>"(?:\\.|[^"\\])*")
  | (?P<id>[A-Za-z_]\w*)
  | (?P<op>==|!=|<=|>=|[-+*/%<>=(){}\[\],:;])
''', re.X)

ESC = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


class JempError(Exception):
    def __init__(self, msg, line=None):
        super().__init__(f"[line {line}] {msg}" if line else msg)


def tokenize(src):
    toks, pos, line = [], 0, 1
    while pos < len(src):
        m = TOKEN.match(src, pos)
        if not m:
            raise JempError(f"Unexpected character {src[pos]!r}", line)
        kind, text = m.lastgroup, m.group()
        pos = m.end()
        if kind == "nl":
            line += 1
        elif kind == "num":
            toks.append(("num", float(text) if "." in text else int(text), line))
        elif kind == "str":
            s = re.sub(r"\\(.)", lambda e: ESC.get(e.group(1), e.group(1)), text[1:-1])
            toks.append(("str", s, line))
        elif kind == "id":
            toks.append(("kw" if text in KEYWORDS else "id", text, line))
        elif kind == "op":
            toks.append(("op", text, line))
    toks.append(("eof", None, line))
    return toks
