from sly import Lexer, Parser

from ctmapmaker.error import MapmakerError


class MapmakerLexer(Lexer):
    tokens = {NAME, NUMBER, EQ, NE, LT, LE, GT, GE, AND, OR, NOT}
    ignore = ' \t'
    literals = {'+', '-', '*', '/', '(', ')', '.'}

    NAME = r'[a-zA-Z][a-zA-Z0-9]*'
    EQ = r'==?'
    NE = r'<>|~=|~='
    LT = r'<'
    LE = r'<='
    GT = r'>'
    GE = r'>='
    AND = r'&&?|and|AND'
    OR = r'\|\|?|or|OR'
    NOT = r'!|~|not|NOT'

    @_(r'\d+')
    def NUMBER(self, t):
        t.value = int(t.value)
        return t

    def error(self, t):
        raise MapmakerError(f"Illegal character '{t.value[0]}'")


class MapmakerParser(Parser):
    tokens = MapmakerLexer.tokens

    precedence = (
        ('left', 'OR'),
        ('left', 'AND'),
        ('left', 'EQ', 'NE'),
        ('left', 'LT', 'LE', 'GT', 'GE'),
        ('left', '+', '-'),
        ('left', '*', '/'),
        ('right', 'UMINUS', 'NOT'),
        ('left', '.'),
    )

    @_('expr "+" expr')
    def expr(self, p):
        return ('op_add', p.expr0, p.expr1)

    @_('expr "-" expr')
    def expr(self, p):
        return ('op_sub', p.expr0, p.expr1)

    @_('expr "*" expr')
    def expr(self, p):
        return ('op_mul', p.expr0, p.expr1)

    @_('expr "/" expr')
    def expr(self, p):
        return ('op_div', p.expr0, p.expr1)

    @_('"-" expr %prec UMINUS')
    def expr(self, p):
        return ('op_uminus', p.expr)

    @_('expr EQ expr')
    def expr(self, p):
        return ('op_eq', p.expr0, p.expr1)

    @_('expr NE expr')
    def expr(self, p):
        return ('op_ne', p.expr0, p.expr1)

    @_('expr LT expr')
    def expr(self, p):
        return ('op_lt', p.expr0, p.expr1)

    @_('expr LE expr')
    def expr(self, p):
        return ('op_le', p.expr0, p.expr1)

    @_('expr GT expr')
    def expr(self, p):
        return ('op_gt', p.expr0, p.expr1)

    @_('expr GE expr')
    def expr(self, p):
        return ('op_ge', p.expr0, p.expr1)

    @_('expr AND expr')
    def expr(self, p):
        return ('op_and', p.expr0, p.expr1)

    @_('expr OR expr')
    def expr(self, p):
        return ('op_or', p.expr0, p.expr1)

    @_('NOT expr')
    def expr(self, p):
        return ('op_not', p.expr)

    @_('expr "." NAME')
    def expr(self, p):
        return ('op_get', p.expr, p.NAME)

    @_('"(" expr ")"')
    def expr(self, p):
        return p.expr

    @_('NUMBER')
    def expr(self, p):
        return ('op_const', p.NUMBER)

    @_('NAME')
    def expr(self, p):
        return ('op_getname', p.NAME)

    def error(self, token):
        if token:
            raise MapmakerError(f'Syntax error at token {token.type}')
        else:
            raise MapmakerError('Parse error in input. EOF')


class MapmakerAssembler():
    @staticmethod
    def assemble(ast):
        asm = []

        def walk(ast):
            args = []

            for item in ast[1:]:
                if isinstance(item, tuple):
                    walk(item)
                else:
                    args.append(item)
            asm.append((ast[0], *args))

        walk(ast)
        return asm


class MapmakerEval():
    def __init__(self, asm):
        self.asm = asm

    def op_add(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x + y)

    def op_sub(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x - y)

    def op_mul(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x * y)

    def op_div(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x / y)

    def op_uminus(self, ctx, stack):
        x = stack.pop()
        stack.append(-x)

    def op_get(self, ctx, stack, name):
        x = stack.pop()
        stack.append(x[name])

    def op_eq(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x == y)

    def op_ne(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x != y)

    def op_lt(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x < y)

    def op_le(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x <= y)

    def op_gt(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x > y)

    def op_ge(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x >= y)

    def op_and(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x and y)

    def op_or(self, ctx, stack):
        y = stack.pop()
        x = stack.pop()
        stack.append(x or y)

    def op_not(self, ctx, stack):
        x = stack.pop()
        stack.append(not x)

    def op_const(self, ctx, stack, value):
        stack.append(value)

    def op_getname(self, ctx, stack, name):
        stack.append(ctx[name])

    def eval(self, ctx):
        stack = []

        for stmt in self.asm:
            op, *args = stmt
            getattr(self, op)(ctx, stack, *args)

        assert len(stack) == 1
        result, = stack
        return result


def mapmaker_compile(text):
    tokens = MapmakerLexer().tokenize(text)
    ast = MapmakerParser().parse(tokens)
    asm = MapmakerAssembler().assemble(ast)
    return MapmakerEval(asm).eval


if __name__ == '__main__':
    lexer = MapmakerLexer()
    parser = MapmakerParser()
    assembler = MapmakerAssembler()
    while True:
        try:
            text = input('mapmaker > ')
        except EOFError:
            break
        if text:
            tokens = lexer.tokenize(text)
            ast = parser.parse(tokens)
            asm = assembler.assemble(ast)
            for i, stmt in enumerate(asm):
                print(i, *stmt)
