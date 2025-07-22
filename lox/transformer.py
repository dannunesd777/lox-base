"""
Implementa o transformador da árvore sintática que converte entre as representações

    lark.Tree -> lox.ast.Node.

A resolução de vários exercícios requer a modificação ou implementação de vários
métodos desta classe.
"""

from typing import Callable
from lark import Transformer, v_args

from . import runtime as op
from .ast import *


def op_handler(op: Callable):
    """
    Fábrica de métodos que lidam com operações binárias na árvore sintática.

    Recebe a função que implementa a operação em tempo de execução.
    """

    def method(self, left, right):
        return BinOp(left, right, op)

    return method


@v_args(inline=True)
class LoxTransformer(Transformer):
    # Programa
    def program(self, *stmts):
        return Program(list(stmts))

    # Operações matemáticas básicas
    mul = op_handler(op.mul)
    div = op_handler(op.truediv)
    sub = op_handler(op.sub)
    add = op_handler(op.add)

    # Comparações
    gt = op_handler(op.gt)
    lt = op_handler(op.lt)
    ge = op_handler(op.ge)
    le = op_handler(op.le)
    eq = op_handler(op.eq)
    ne = op_handler(op.ne)

    # Outras expressões
    def call(self, callee: Var, params: list):
        return Call(callee, params)
        
    def params(self, *args):
        params = list(args)
        return params

    # Comandos
    def print_cmd(self, expr):
        return Print(expr)

    def NUMBER(self, token):
        text = str(token)
        if '.' in text:
            num = float(text)
        else:
            num = int(text)
        return Literal(num)
    
    def STRING(self, token):
        text = str(token)[1:-1]
        return Literal(text)
    
    def NIL(self, _):
        return Literal(None)

    def BOOL(self, token):
        return Literal(token == "true")

    def VAR(self, token):
        name = str(token)
        return Var(name)
    
    def atr(self, obj, atr):
        return Getattr(obj, atr.name)

    def not_(self, expr):
        return UnaryOp(op=op.not_, expr=expr)
    
    def neg(self, expr):
        return UnaryOp(op=op.neg, expr=expr)
    
    def unary(self, expr):
        return expr
    
    def logic_and (self, primeiro_arg, *resto):
        expr = primeiro_arg # fazer isso para poder fazer mais de um and (ex: a and b and c) 
        for i in resto:
            expr = And(expr, i)
        return expr

    def logic_or(self, primeiro_arg, *resto):
        expr = primeiro_arg # fazer isso para poder fazer mais de um or (ex: a or b or c) 
        for i in resto:
            expr = Or(expr, i)
        return expr 
    
    def assignment(self, *args):
        if len(args) == 2:
            var, expr = args
            return Assign(var.name, expr)
        else:
            return args[0]
    
    def IDENTIFIER(self, token):
        return Var(str(token))
    
    def setattr(self, obj, attr, value):
        attr_name = attr.name if hasattr(attr, "name") else str(attr)
        return Setattr(obj, attr_name, value)

    def assign(self, name, value):
        return Assign(name.name, value)   

    def block(self, *stmts: Stmt):
        return Block(list(stmts))

    def if_cmd(self, cond: Expr, then: Stmt, orelse: Stmt = Block([])):
        return If(cond, then, orelse)

    def var_def(self, var: Var, value=None):
        if value is None:
            value = Literal(None)
        return VarDef(var.name, value)
    
    def while_cmd(self, cond: Expr, body: Stmt):
        return While(cond, body)

    def for_cmd(self, for_args, stmt):
        init, cond, incr = for_args
        if init is None:
            init = Literal(None)
        if cond is None:
            cond = Literal(True)
        if incr is None:
            incr = Literal(None)
        if isinstance(incr, Literal) and incr.value is None:
            while_body = stmt
        else:
            while_body = Block([stmt, incr])
        while_stmt = While(cond, while_body)
        return Block([init, while_stmt])

    def for_args(self, init, cond, incr):
        return (init, cond, incr)

    def opt_expr(self, expr=None):
        return expr

    def fun_def(self, name: Var, args: list[str], body: Block):
        return Function(name.name, args, body.stmts)
        
    def fun_args(self, *args: Var) -> list[str]:
        return [arg.name for arg in args]

    def return_cmd(self, expr: Expr = None):
        if expr is None:
            expr = Literal(None)
        return Return(expr)

    def class_def(self, name, *args):
        # args pode ter 1 ou 2 elementos dependendo se há superclasse
        if len(args) == 1:
            # Sem superclasse: args[0] é methods
            superclass = None
            methods = args[0]
        elif len(args) == 2:
            # Com superclasse: args[0] é superclass, args[1] é methods
            superclass = args[0]
            methods = args[1]
        else:
            # Caso de erro
            superclass = None
            methods = []
        
        return Class(name.name, superclass, methods)
    
    def class_super(self, superclass):
        return superclass
    
    def class_methods(self, *items):
        return list(items)  # just return the list of methods

    def method_def(self, name, arg_names, body):
        return Function(name.name, arg_names, body.stmts)
    
    def THIS(self, token):
        return This()
    
    def CLASS(self, token):
        return str(token)
    
    def FUN(self, token):
        return str(token)
    
    def PRINT(self, token):
        return str(token)
    
    def RETURN(self, token):
        return str(token)
    
    def IF(self, token):
        return str(token)
    
    def ELSE(self, token):
        return str(token)
    
    def WHILE(self, token):
        return str(token)
    
    def FOR(self, token):
        return str(token)
    
    def super_expr(self, super_token, method_name):
        return Super(method_name.name)
    
    def SUPER(self, token):
        return str(token)