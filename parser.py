from .lexer import tokenize, JempError


class Parser:
    def __init__(self, src):
        self.t = tokenize(src)
        self.i = 0

    # --- helpers
    def peek(self):
        return self.t[self.i]

    def next(self):
        tok = self.t[self.i]
        self.i += 1
        return tok

    def is_(self, val):
        k, v, _ = self.peek()
        return k in ("op", "kw") and v == val

    def match(self, val):
        if self.is_(val):
            self.i += 1
            return True
        return False

    def expect(self, val):
        if not self.match(val):
            k, v, line = self.peek()
            raise JempError(f"Expected '{val}' but found '{v if v is not None else 'end of file'}'", line)

    def ident(self):
        k, v, line = self.next()
        if k != "id":
            raise JempError("Expected a name", line)
        return v

    # --- statements
    def program(self):
        out = []
        while self.peek()[0] != "eof":
            out.append(self.stmt())
        return out

    def block(self):
        self.expect("{")
        out = []
        while not self.is_("}"):
            if self.peek()[0] == "eof":
                raise JempError("Unclosed '{'", self.peek()[2])
            out.append(self.stmt())
        self.expect("}")
        return out

    def stmt(self):
        line = self.peek()[2]
        if self.match(";"):
            return ("block", [])
        if self.match("let"):
            name = self.ident()
            self.expect("=")
            return ("let", name, self.expr(), line)
        if self.is_("fn") and self.t[self.i + 1][0] == "id":
            self.next()
            name = self.ident()
            return ("let", name, self.fn_rest(name), line)
        if self.match("if"):
            return self.if_rest(line)
        if self.match("while"):
            cond = self.expr()
            return ("while", cond, self.block())
        if self.match("for"):
            var = self.ident()
            self.expect("in")
            it = self.expr()
            return ("for", var, it, self.block(), line)
        if self.match("return"):
            if self.is_("}") or self.is_(";") or self.peek()[0] == "eof":
                return ("return", ("lit", None))
            return ("return", self.expr())
        if self.match("break"):
            return ("break",)
        if self.match("continue"):
            return ("continue",)
        e = self.expr()
        if self.match("="):
            if e[0] not in ("var", "index"):
                raise JempError("Invalid assignment target", line)
            return ("assign", e, self.expr(), line)
        return ("expr", e)

    def if_rest(self, line):
        cond = self.expr()
        then = self.block()
        els = None
        if self.match("else"):
            els = [self.if_rest(self.peek()[2])] if self.match("if") else self.block()
        return ("if", cond, then, els)

    def fn_rest(self, name="<fn>"):
        self.expect("(")
        params = []
        while not self.is_(")"):
            params.append(self.ident())
            if not self.match(","):
                break
        self.expect(")")
        return ("fn", name, params, self.block())

    # --- expressions (precedence climbing)
    def expr(self):
        return self.or_()

    def binary(self, sub, ops):
        left = sub()
        while self.peek()[0] in ("op", "kw") and self.peek()[1] in ops:
            _, op, line = self.next()
            left = ("bin", op, left, sub(), line)
        return left

    def or_(self):
        left = self.and_()
        while self.match("or"):
            left = ("logic", "or", left, self.and_())
        return left

    def and_(self):
        left = self.eq()
        while self.match("and"):
            left = ("logic", "and", left, self.eq())
        return left

    def eq(self): return self.binary(self.cmp, ("==", "!="))
    def cmp(self): return self.binary(self.term, ("<", ">", "<=", ">="))
    def term(self): return self.binary(self.factor, ("+", "-"))
    def factor(self): return self.binary(self.unary, ("*", "/", "%"))

    def unary(self):
        line = self.peek()[2]
        if self.match("-"):
            return ("neg", self.unary(), line)
        if self.match("not"):
            return ("not", self.unary())
        return self.postfix()

    def postfix(self):
        e = self.primary()
        while True:
            line = self.peek()[2]
            if self.match("("):
                args = []
                while not self.is_(")"):
                    args.append(self.expr())
                    if not self.match(","):
                        break
                self.expect(")")
                e = ("call", e, args, line)
            elif self.match("["):
                idx = self.expr()
                self.expect("]")
                e = ("index", e, idx, line)
            else:
                return e

    def primary(self):
        k, v, line = self.next()
        if k in ("num", "str"):
            return ("lit", v)
        if k == "id":
            return ("var", v, line)
        if k == "kw":
            if v in ("true", "false"):
                return ("lit", v == "true")
            if v == "nil":
                return ("lit", None)
            if v == "fn":
                return self.fn_rest()
        if k == "op":
            if v == "(":
                e = self.expr()
                self.expect(")")
                return e
            if v == "[":
                items = []
                while not self.is_("]"):
                    items.append(self.expr())
                    if not self.match(","):
                        break
                self.expect("]")
                return ("list", items)
            if v == "{":
                pairs = []
                while not self.is_("}"):
                    key = self.expr()
                    self.expect(":")
                    pairs.append((key, self.expr()))
                    if not self.match(","):
                        break
                self.expect("}")
                return ("dict", pairs)
        raise JempError(f"Unexpected '{v if v is not None else 'end of file'}'", line)


def parse(src):
    return Parser(src).program()
