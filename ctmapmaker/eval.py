from sly import Lexer, Parser

from ctmapmaker.error import MapmakerError


class MapmakerLexer(Lexer):
    tokens = {LE, GE, EQ, NE, LT, GT, AND, OR, NOT, NAME, NUMBER}
    ignore = ' \t'
    literals = {'+', '-', '*', '/', '(', ')', '.'}

    LE = r'<='
    GE = r'>='
    EQ = r'==?'
    NE = r'!=|~=|<>'
    LT = r'<'
    GT = r'>'
    AND = r'&&?|and|AND'
    OR = r'\|\|?|or|OR'
    NOT = r'!|~|not|NOT'
    NAME = r'[a-zA-Z][a-zA-Z0-9]*'

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
        ('left', 'CMP_RESOLVE'),
        ('left', 'LE', 'GE', 'LT', 'GT', 'EQ', 'NE'),
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

    @staticmethod
    def _cmp_to_op(cmp):
        return {
            '<=': 'LE',
            '>=': 'GE',
            '==': 'EQ',
            '=': 'EQ',
            '!=': 'NE',
            '~=': 'NE',
            '<>': 'NE',
            '<': 'LT',
            '>': 'GT',
        }[cmp]

    @_('expr LE expr',
       'expr GE expr',
       'expr EQ expr',
       'expr NE expr',
       'expr LT expr',
       'expr GT expr')
    def cmp(self, p):
        return [self._cmp_to_op(p[1])], [p.expr0, p.expr1]

    @_('cmp LE expr',
       'cmp GE expr',
       'cmp EQ expr',
       'cmp NE expr',
       'cmp LT expr',
       'cmp GT expr')
    def cmp(self, p):
        p.cmp[0].append(self._cmp_to_op(p[1]))
        p.cmp[1].append(p.expr)
        return p.cmp

    @_('cmp %prec CMP_RESOLVE')
    def expr(self, p):
        return ('op_cmp', p.cmp[0], *p.cmp[1])

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
    def name(self, p):
        return p.NAME

    @_('name NAME')
    def name(self, p):
        return p.name + p.NAME

    @_('name')
    def expr(self, p):
        return ('op_getname', p.name)

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

    def op_cmp(self, ctx, stack, ops):
        vals = [stack.pop() for i in range(len(ops) + 1)][::-1]
        result = True
        for i, op in enumerate(ops):
            x, y = vals[i], vals[i+1]
            if op == 'LE':
                result = result and x <= y
            elif op == 'GE':
                result = result and x >= y
            elif op == 'EQ':
                result = result and x == y
            elif op == 'NE':
                result = result and x != y
            elif op == 'LT':
                result = result and x < y
            elif op == 'GT':
                result = result and x > y
            else:
                assert False

        stack.append(result)

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
