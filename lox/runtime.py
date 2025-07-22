import builtins
from dataclasses import dataclass
from operator import add, eq, ge, gt, le, lt, mul, ne, neg, not_, sub, truediv
from typing import TYPE_CHECKING
import types
import math

from .ctx import Ctx

if TYPE_CHECKING:
    from .ast import Stmt, Value

__all__ = [
    "add",
    "eq",
    "ge",
    "gt",
    "le",
    "lt",
    "mul",
    "ne",
    "neg",
    "not_",
    "print",
    "show",
    "sub",
    "truthy",
    "truediv",
]


class LoxInstance:
    """
    Classe base para todos os objetos Lox.
    """


@dataclass
class LoxFunction:
    """
    Classe base para todas as funções Lox.
    """

    name: str
    args: list[str]
    body: list["Stmt"]
    ctx: Ctx

    def __call__(self, *args):
        env = dict(zip(self.args, args, strict=True))
        env = self.ctx.push(env)

        try:
            for stmt in self.body:
                stmt.eval(env)
        except LoxReturn as e:
            return e.value


class LoxReturn(Exception):
    """
    Exceção para retornar de uma função Lox.
    """

    def __init__(self, value):
        self.value = value
        super().__init__()


class LoxError(Exception):
    """
    Exceção para erros de execução Lox.
    """


# Lox-specific operators that handle type checking
def lox_add(left: "Value", right: "Value") -> "Value":
    """Soma em Lox - apenas números e strings"""
    # Verifica se um dos operandos é booleano
    if isinstance(left, bool) or isinstance(right, bool):
        raise LoxError("Operands must be two numbers or two strings.")
    
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left + right
    elif isinstance(left, str) and isinstance(right, str):
        return left + right
    else:
        raise LoxError(f"Operação '+' não suportada entre {type(left).__name__} e {type(right).__name__}")


def lox_sub(left: "Value", right: "Value") -> "Value":
    """Subtração em Lox - apenas números"""
    # Verifica se um dos operandos é booleano
    if isinstance(left, bool) or isinstance(right, bool):
        raise LoxError("Operands must be numbers.")
    
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left - right
    else:
        raise LoxError(f"Operação '-' não suportada entre {type(left).__name__} e {type(right).__name__}")


def lox_mul(left: "Value", right: "Value") -> "Value":
    """Multiplicação em Lox - apenas números"""
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left * right
    else:
        raise LoxError(f"Operação '*' não suportada entre {type(left).__name__} e {type(right).__name__}")


def lox_truediv(left: "Value", right: "Value") -> "Value":
    """Divisão em Lox - apenas números"""
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if right == 0:
            return float('nan')  # Retorna NaN em vez de lançar exceção
        return left / right
    else:
        raise LoxError(f"Operação '/' não suportada entre {type(left).__name__} e {type(right).__name__}")


def lox_ge(left: "Value", right: "Value") -> "Value":
    """Maior ou igual em Lox - apenas números"""
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left >= right
    else:
        raise LoxError(f"Operação '>=' não suportada entre {type(left).__name__} e {type(right).__name__}")


def lox_le(left: "Value", right: "Value") -> "Value":
    """Menor ou igual em Lox - apenas números"""
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left <= right
    else:
        raise LoxError(f"Operação '<=' não suportada entre {type(left).__name__} e {type(right).__name__}")


def lox_gt(left: "Value", right: "Value") -> "Value":
    """Maior que em Lox - apenas números"""
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left > right
    else:
        raise LoxError(f"Operação '>' não suportada entre {type(left).__name__} e {type(right).__name__}")


def lox_lt(left: "Value", right: "Value") -> "Value":
    """Menor que em Lox - apenas números"""
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left < right
    else:
        raise LoxError(f"Operação '<' não suportada entre {type(left).__name__} e {type(right).__name__}")


def lox_eq(left: "Value", right: "Value") -> "Value":
    """Igualdade estrita em Lox - tipos diferentes são sempre diferentes"""
    if type(left) != type(right):
        return False
    
    # Tratamento especial para métodos (LoxFunction)
    from .ast import LoxFunction
    if isinstance(left, LoxFunction):
        return left is right  # Compara identidade de objetos
    
    return left == right


def lox_ne(left: "Value", right: "Value") -> "Value":
    """Desigualdade estrita em Lox"""
    return not lox_eq(left, right)


def lox_not(value: "Value") -> "Value":
    """Negação lógica em Lox"""
    return not truthy(value)


def lox_neg(value: "Value") -> "Value":
    """Negação numérica em Lox - preserva zero negativo"""
    if isinstance(value, (int, float)):
        if value == 0:
            # Preserva zero negativo
            return -0.0
        return -value
    else:
        raise LoxError(f"Operação '-' não suportada para {type(value).__name__}")


# Override the imported operators with Lox-specific versions
add = lox_add
sub = lox_sub
mul = lox_mul
truediv = lox_truediv
ge = lox_ge
le = lox_le
gt = lox_gt
lt = lox_lt
eq = lox_eq
ne = lox_ne
not_ = lox_not
neg = lox_neg


nan = float("nan")
inf = float("inf")


def print(value: "Value"):
    """
    Imprime um valor lox.
    """
    builtins.print(show(value))


def show(value: "Value") -> str:
    """
    Converte valor lox para string.
    """
    # Handle None -> "nil"
    if value is None:
        return "nil"
    
    # Handle boolean values
    if value is True:
        return "true"
    if value is False:
        return "false"
    
    # Handle floats that are integers, but preserve negative zero
    if isinstance(value, float) and value.is_integer():
        if value == 0 and math.copysign(1, value) < 0:
            return "-0"  # Preserve negative zero
        return str(int(value))
    
    # Handle LoxClass, LoxInstance, LoxFunction
    from .ast import LoxClass, LoxInstance, LoxFunction
    
    if isinstance(value, LoxClass):
        return str(value)
    
    if isinstance(value, LoxInstance):
        return f"{value.lox_class.name} instance"
    
    if isinstance(value, LoxFunction):
        return f"<fn {value.name}>"
    
    # Handle native Python functions
    if isinstance(value, (types.FunctionType, types.BuiltinFunctionType, types.BuiltinMethodType)):
        return "<native fn>"
    
    # Default case
    return str(value)


def show_repr(value: "Value") -> str:
    """
    Mostra um valor lox, mas coloca aspas em strings.
    """
    if isinstance(value, str):
        return f'"{value}"'
    return show(value)


def truthy(value: "Value") -> bool:
    """
    Converte valor lox para booleano segundo a semântica do lox.
    """
    if value is None or value is False:
        return False
    return True
