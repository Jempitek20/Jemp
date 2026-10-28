# Jemp

A small, readable programming language with a hand-written lexer, recursive-descent parser and tree-walking interpreter. About 500 lines of pure Python, no dependencies.

```jemp
fn fib(n) {
  if n < 2 { return n }
  return fib(n - 1) + fib(n - 2)
}
for i in range(10) { print(fib(i)) }
```

## Run it

```bash
python -m jemp examples/fib.jemp   # run a file
python -m jemp                     # interactive REPL
pytest                             # run tests
```

## Language tour

| Feature | Syntax |
|---|---|
| Variables | `let x = 5` / `x = x + 1` |
| Types | numbers, strings, `true`/`false`, `nil`, lists, dicts, functions |
| Functions | `fn add(a, b) { return a + b }` (first-class, with closures) |
| Anonymous fn | `let sq = fn(x) { return x * x }` |
| Conditions | `if ... { } else if ... { } else { }` |
| Loops | `while cond { }`, `for x in list { }`, `break`, `continue` |
| Logic | `and`, `or`, `not` (short-circuit) |
| Lists / dicts | `[1, 2]`, `l[0]`, `{"a": 1}`, `d["a"]` |
| Comments | `# like this` |

Builtins: `print len range str num type push pop keys sqrt floor abs upper lower split join input`

## Layout

```
jemp/lexer.py        source -> tokens
jemp/parser.py       tokens -> AST
jemp/interpreter.py  AST -> execution, builtins
examples/            sample programs
tests/               pytest suite
```

## Ideas for next steps

Method calls (`list.push(x)`), imports, a bytecode VM, string interpolation, classes.

## License

Apache-2.0
