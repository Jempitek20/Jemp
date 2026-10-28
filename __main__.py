import sys
from . import run, JempError


def repl():
    from .interpreter import Interpreter, show
    from .parser import parse
    it = Interpreter()
    print("Jemp 0.1 - Ctrl+D to exit")
    while True:
        try:
            line = input(">>> ")
            prog = parse(line)
            if len(prog) == 1 and prog[0][0] == "expr":
                v = it.eval(prog[0][1], it.globals)
                if v is not None:
                    print(show(v))
            else:
                it.exec_block(prog, it.globals)
        except EOFError:
            print()
            return
        except JempError as e:
            print("Error:", e)


def main():
    if len(sys.argv) < 2:
        return repl()
    try:
        with open(sys.argv[1], encoding="utf-8") as f:
            run(f.read())
    except JempError as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"File not found: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)


main()
