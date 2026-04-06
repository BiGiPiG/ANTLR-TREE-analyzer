import sys
import antlr4
from antlr4.error.ErrorListener import ErrorListener
from TransliatoryLexer import TransliatoryLexer
from TransliatoryParser import TransliatoryParser
from TransliatoryVisitor import TransliatoryVisitor


class ErrorCollector(ErrorListener):
    def __init__(self):
        self.errors = []

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        self.errors.append(f"[ERROR] Line {line}:{column} -> {msg}")


class ExprVisitor(TransliatoryVisitor):
    def __init__(self):
        self.lines = []
        self.depth = 0

    def _indent(self):
        return "  " * self.depth

    def _log(self, msg):
        self.lines.append(f"{self._indent()}└─ {msg}")

    def visitExpr(self, ctx):
        self._log("expr")
        self.depth += 1
        self.visitChildren(ctx)
        self.depth -= 1

    def visitAssignTail(self, ctx):
        is_eps = ctx.getChildCount() == 0
        self._log(f"assignTail{' (ε)' if is_eps else ''}")
        self.depth += 1
        self.visitChildren(ctx)
        self.depth -= 1

    def visitSimpleExpr(self, ctx):
        self._log("simpleExpr")
        self.depth += 1
        self.visitChildren(ctx)
        self.depth -= 1

    def visitIncTail(self, ctx):
        is_eps = ctx.getChildCount() == 0
        self._log(f"incTail{' (ε)' if is_eps else ''}")
        self.depth += 1
        self.visitChildren(ctx)
        self.depth -= 1

    def visitOperand(self, ctx):
        self._log(f"operand: {ctx.getText()}")
        self.depth += 1
        self.visitChildren(ctx)
        self.depth -= 1


class SemanticVisitor(TransliatoryVisitor):
    def __init__(self, env: dict):
        self.errors = []
        self.env = env

    def visitStart(self, ctx):
        for expr_ctx in ctx.expr():
            self._process_expr(expr_ctx)
        return self.visitChildren(ctx)

    def _process_expr(self, expr_ctx):
        simple = expr_ctx.simpleExpr()
        assign_tail = expr_ctx.assignTail()
        is_lhs = assign_tail.getChildCount() > 0
        self._check_simple_expr(simple, is_assignment_lhs=is_lhs)
        if is_lhs:
            rhs_expr = assign_tail.expr()
            if rhs_expr:
                self._process_expr(rhs_expr)

    def _check_simple_expr(self, simple_ctx, is_assignment_lhs=False):
        operand = simple_ctx.operand()
        text = operand.getText()
        inc_tails = simple_ctx.incTail()
        has_pre_inc = len(inc_tails) > 0 and inc_tails[0].getChildCount() > 0
        has_post_inc = len(inc_tails) > 1 and inc_tails[1].getChildCount() > 0
        if text.isdigit():
            if is_assignment_lhs:
                self.errors.append(f"Literal '{text}' cannot be an l-value (assignment target)")
            if has_pre_inc or has_post_inc:
                self.errors.append(f"Increment applied to literal '{text}'")
            return
        if text not in self.env:
            self.env[text] = {"declared": False, "pre_inc": False, "post_inc": False}
        var_info = self.env[text]
        if has_pre_inc:
            var_info["pre_inc"] = True
        if has_post_inc:
            var_info["post_inc"] = True
        if is_assignment_lhs:
            var_info["declared"] = True
        else:
            if not var_info["declared"]:
                self.errors.append(f"Variable '{text}' is not initialized")


def analyze_line(line_text: str, line_num: int, env: dict) -> bool:
    input_stream = antlr4.InputStream(line_text)
    lexer = TransliatoryLexer(input_stream)
    lexer.removeErrorListeners()
    err_collector = ErrorCollector()
    lexer.addErrorListener(err_collector)
    token_stream = antlr4.CommonTokenStream(lexer)
    parser = TransliatoryParser(token_stream)
    parser.removeErrorListeners()
    parser.addErrorListener(err_collector)
    tree = parser.start()
    if err_collector.errors:
        for err in err_collector.errors:
            print(f"[ERROR] Syntax error (line {line_num}): {err.split('->')[1].strip()}")
        return False
    print(f"--- Statement (line {line_num}): {line_text} ---")
    tree_visitor = ExprVisitor()
    tree_visitor.visit(tree)
    print("\n".join(tree_visitor.lines))
    sem_visitor = SemanticVisitor(env)
    sem_visitor.visit(tree)
    if sem_visitor.errors:
        for err in sem_visitor.errors:
            print(f"[WARNING] Semantic error (line {line_num}): {err}")
        return False
    return True


def print_environment(env: dict):
    if not env:
        print("\n[INFO] Environment is empty (no variables declared).")
        return
    print("\n" + "=" * 60)
    print("=== SYMBOL TABLE (ENVIRONMENT) ===")
    print(f"{'Identifier':<15} | {'Status':<18} | {'Increment Operations'}")
    print("-" * 60)
    for name, info in env.items():
        status = "Declared (l-value)" if info["declared"] else "Read-only (r-value)"
        inc_ops = []
        if info["pre_inc"]:
            inc_ops.append("Prefix ++")
        if info["post_inc"]:
            inc_ops.append("Postfix ++")
        inc_str = ", ".join(inc_ops) if inc_ops else "None"
        print(f"{name:<15} | {status:<18} | {inc_str}")
    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <file_path>")
        return
    file_path = sys.argv[1]
    print(f"=== Analyzing file: {file_path} ===\n")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        env = {}
        valid_count = 0
        for idx, line in enumerate(lines, 1):
            if analyze_line(line, idx, env):
                valid_count += 1
            print()
        print(f"[OK] Successfully processed {valid_count} out of {len(lines)} lines.")
        print_environment(env)
    except FileNotFoundError:
        print(f"[ERROR] File '{file_path}' not found.")
    except Exception as e:
        print(f"[ERROR] An error occurred: {e}")


if __name__ == "__main__":
    main()