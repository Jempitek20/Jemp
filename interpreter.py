import math
import sys
from .lexer import JempError
from .parser import parse


class Return(Exception):
    def __init__(self, value): self.value = value
class Break(Exception): pass
class Continue(Exception): pass


class Env:
    def __init__(self, parent=None):
        self.vars, self.parent = {}, parent

    def lookup(self, name, line):
        e = self
        while e:
            if name in e.vars:
                return e
            e = e.parent
        raise JempError(f"Undefined variable '{name}'", line)

    def get(self, name, line): return self.lookup(name, line).vars[name]
    def set(self, name, val, line): self.lookup(name, line).vars[name] = val
    def define(self, name, val): self.vars[name] = val


class Function:
    def __init__(self, name, params, body, closure):
        self.name, self.params, self.body, self.closure = name, params, body, closure

    def __repr__(self): return f"<fn {self.name}>"


def show(v):
    if v is None: return "nil"
    if v is True: return "true"
    if v is False: return "false"
    if isinstance(v, float) and v.is_integer(): return str(int(v))
    if isinstance(v, str): return v
    if isinstance(v, list): return "[" + ", ".join(rep(x) for x in v) + "]"
    if isinstance(v, dict): return "{" + ", ".join(f"{rep(k)}: {rep(x)}" for k, x in v.items()) + "}"
    return str(v)


def rep(v): return f'"{v}"' if isinstance(v, str) else show(v)


def truthy(v): return v is not None and v is not False


def _num(x, name):
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise JempError(f"{name}() needs a number")
    return x


def _len(x):
    if not isinstance(x, (str, list, dict)): raise JempError("len() needs a string, list or dict")
    return len(x)


def _range(*a):
    return list(range(*[int(_num(x, "range")) for x in a]))


def _num_conv(x):
    try:
        f = float(x)
        return int(f) if f.is_integer() else f
    except (ValueError, TypeError):
        raise JempError(f"Cannot convert {rep(x)} to a number")


def _push(l, x):
    l.append(x)
    return l


def _type(x):
    if x is None: return "nil"
    if isinstance(x, bool): return "bool"
    if isinstance(x, (int, float)): return "number"
    if isinstance(x, str): return "string"
    if isinstance(x, list): return "list"
    if isinstance(x, dict): return "dict"
    return "function"


BUILTINS = {
    "print": lambda *a: print(*[show(x) for x in a]),
    "len": _len,
    "range": _range,
    "str": show,
    "num": _num_conv,
    "type": _type,
    "push": _push,
    "pop": lambda l: l.pop(),
    "keys": lambda d: list(d.keys()),
    "sqrt": lambda x: math.sqrt(_num(x, "sqrt")),
    "floor": lambda x: math.floor(_num(x, "floor")),
    "abs": lambda x: abs(_num(x, "abs")),
    "upper": lambda s: s.upper(),
    "lower": lambda s: s.lower(),
    "split": lambda s, sep=" ": s.split(sep),
    "join": lambda l, sep="": sep.join(show(x) for x in l),
    "input": lambda p="": input(p),
}


class Interpreter:
    def __init__(self):
        self.globals = Env()
        for k, v in BUILTINS.items():
            self.globals.define(k, v)
        self.depth = 0

    def run(self, src):
        self.exec_block(parse(src), self.globals)

    def exec_block(self, stmts, env):
        for s in stmts:
            self.exec(s, env)

    def exec(self, s, env):
        k = s[0]
        if k == "expr": self.eval(s[1], env)
        elif k == "let": env.define(s[1], self.eval(s[2], env))
        elif k == "assign":
            target, val = s[1], self.eval(s[2], env)
            if target[0] == "var":
                env.set(target[1], val, target[2])
            else:
                obj, idx = self.eval(target[1], env), self.eval(target[2], env)
                try:
                    obj[idx] = val
                except (IndexError, TypeError, KeyError):
                    raise JempError("Bad index assignment", target[3])
        elif k == "if":
            if truthy(self.eval(s[1], env)): self.exec_block(s[2], Env(env))
            elif s[3] is not None: self.exec_block(s[3], Env(env))
        elif k == "while":
            while truthy(self.eval(s[1], env)):
                try: self.exec_block(s[2], Env(env))
                except Break: break
                except Continue: continue
        elif k == "for":
            it = self.eval(s[2], env)
            if isinstance(it, (dict, str)): it = list(it)
            if not isinstance(it, list): raise JempError("Can only loop over a list, string or dict", s[4])
            for x in list(it):
                e = Env(env)
                e.define(s[1], x)
                try: self.exec_block(s[3], e)
                except Break: break
                except Continue: continue
        elif k == "return": raise Return(self.eval(s[1], env))
        elif k == "break": raise Break()
        elif k == "continue": raise Continue()
        elif k == "block": self.exec_block(s[1], Env(env))

    def eval(self, n, env):
        k = n[0]
        if k == "lit": return n[1]
        if k == "var": return env.get(n[1], n[2])
        if k == "list": return [self.eval(x, env) for x in n[1]]
        if k == "dict": return {self.eval(a, env): self.eval(b, env) for a, b in n[1]}
        if k == "fn": return Function(n[1], n[2], n[3], env)
        if k == "neg":
            v = self.eval(n[1], env)
            if isinstance(v, bool) or not isinstance(v, (int, float)): raise JempError("Can only negate numbers", n[2])
            return -v
        if k == "not": return not truthy(self.eval(n[1], env))
        if k == "logic":
            left = self.eval(n[2], env)
            if n[1] == "or": return left if truthy(left) else self.eval(n[3], env)
            return self.eval(n[3], env) if truthy(left) else left
        if k == "bin": return self.binop(n[1], self.eval(n[2], env), self.eval(n[3], env), n[4])
        if k == "index":
            obj, idx = self.eval(n[1], env), self.eval(n[2], env)
            try: return obj[idx]
            except (IndexError, KeyError): raise JempError(f"Index {rep(idx)} out of range", n[3])
            except TypeError: raise JempError("Value is not indexable", n[3])
        if k == "call": return self.call(self.eval(n[1], env), [self.eval(a, env) for a in n[2]], n[3])
        raise JempError(f"Unknown node {k}")

    def binop(self, op, a, b, line):
        num = lambda x: isinstance(x, (int, float)) and not isinstance(x, bool)
        if op == "==": return a == b
        if op == "!=": return a != b
        if op == "+":
            if num(a) and num(b): return a + b
            if isinstance(a, str) or isinstance(b, str): return show(a) + show(b)
            if isinstance(a, list) and isinstance(b, list): return a + b
            raise JempError("Cannot add these values", line)
        if op in ("<", ">", "<=", ">="):
            if not ((num(a) and num(b)) or (isinstance(a, str) and isinstance(b, str))):
                raise JempError("Can only compare two numbers or two strings", line)
            return {"<": a < b, ">": a > b, "<=": a <= b, ">=": a >= b}[op]
        if not (num(a) and num(b)):
            if op == "*" and isinstance(a, str) and isinstance(b, int): return a * b
            raise JempError(f"'{op}' needs numbers", line)
        if op == "-": return a - b
        if op == "*": return a * b
        if b == 0: raise JempError("Division by zero", line)
        if op == "/":
            r = a / b
            return int(r) if float(r).is_integer() else r
        return a % b

    def call(self, f, args, line):
        if callable(f):
            try: return f(*args)
            except JempError as e: raise JempError(str(e), line)
            except TypeError: raise JempError("Wrong arguments for builtin", line)
            except (ValueError, IndexError, AttributeError, KeyError) as e:
                raise JempError(f"Builtin error: {e}", line)
        if not isinstance(f, Function): raise JempError("Can only call functions", line)
        if len(args) != len(f.params):
            raise JempError(f"{f.name}() takes {len(f.params)} argument(s), got {len(args)}", line)
        if self.depth > 400: raise JempError("Stack overflow", line)
        env = Env(f.closure)
        for p, a in zip(f.params, args): env.define(p, a)
        self.depth += 1
        try:
            self.exec_block(f.body, env)
        except Return as r:
            return r.value
        finally:
            self.depth -= 1
        return None


def run(src):
    sys.setrecursionlimit(10000)
    Interpreter().run(src)
