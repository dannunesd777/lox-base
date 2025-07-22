from abc import ABC
from dataclasses import dataclass, field 
from typing import Callable, Optional  

from .ctx import Ctx
from .errors import SemanticError
from .node import Cursor

# Declaramos nossa classe base num módulo separado para esconder um pouco de
# Python relativamente avançado de quem não se interessar pelo assunto.
#
# A classe Node implementa um método `pretty` que imprime as árvores de forma
# legível. Também possui funcionalidades para navegar na árvore usando cursores
# e métodos de visitação.
from .node import Node


#
# TIPOS BÁSICOS
#

# Tipos de valores que podem aparecer durante a execução do programa
Value = bool | str | float | None

# Palavras reservadas da linguagem Lox
RESERVED_WORDS = {
    "and", "class", "else", "false", "for", "fun", "if", "nil", 
    "or", "print", "return", "super", "this", "true", "var", "while"
}


class Expr(Node, ABC):
    """
    Classe base para expressões.

    Expressões são nós que podem ser avaliados para produzir um valor.
    Também podem ser atribuídos a variáveis, passados como argumentos para
    funções, etc.
    """


class Stmt(Node, ABC):
    """
    Classe base para comandos.

    Comandos são associdos a construtos sintáticos que alteram o fluxo de
    execução do código ou declaram elementos como classes, funções, etc.
    """


@dataclass
class Program(Node):
    """
    Representa um programa.

    Um programa é uma lista de comandos.
    """

    stmts: list[Stmt]

    def eval(self, ctx: Ctx):
        for stmt in self.stmts:
            stmt.eval(ctx)


#
# EXPRESSÕES
#
@dataclass
class BinOp(Expr):
    """
    Uma operação infixa com dois operandos.

    Ex.: x + y, 2 * x, 3.14 > 3 and 3.14 < 4
    """

    left: Expr
    right: Expr
    op: Callable[[Value, Value], Value]

    def eval(self, ctx: Ctx):
        left_value = self.left.eval(ctx)
        right_value = self.right.eval(ctx)
        return self.op(left_value, right_value)


@dataclass
class Var(Expr):
    """
    Uma variável no código

    Ex.: x, y, z
    """

    name: str

    def eval(self, ctx: Ctx):
        try:
            return ctx[self.name]
        except KeyError:
            raise NameError(f"variável {self.name} não existe!")
    
    def validate_self(self, cursor: Cursor):
        """
        Valida que o nome da variável não é uma palavra reservada.
        """
        if self.name in RESERVED_WORDS:
            raise SemanticError(f"Expect variable name.", token=self.name)


@dataclass
class Literal(Expr):
    """
    Representa valores literais no código, ex.: strings, booleanos,
    números, etc.

    Ex.: "Hello, world!", 42, 3.14, true, nil
    """

    value: Value

    def eval(self, ctx: Ctx):
        return self.value


@dataclass
class And(Expr):
    """
    Uma operação infixa com dois operandos.

    Ex.: x and y
    """
    left: Expr
    right: Expr

    def eval(self, ctx: Ctx):
        left_value = self.left.eval(ctx)
        if not is_lox_true(left_value): # logica do curto circuito
            return left_value
        return self.right.eval(ctx)


@dataclass
class Or(Expr):
    """
    Uma operação infixa com dois operandos.
    Ex.: x or y
    """
    left: Expr
    right: Expr

    def eval(self, ctx: Ctx):
        left_value = self.left.eval(ctx)
        if is_lox_true(left_value): # logica do curto circuito
            return left_value
        return self.right.eval(ctx)

@dataclass
class UnaryOp(Expr):
    """
    Uma operação prefixa com um operando.

    Ex.: -x, !x
    """
    op: Callable[[Value], Value]
    expr: Expr

    def eval(self, ctx: Ctx):
        value = self.expr.eval(ctx)
        return self.op(value)


@dataclass
class Call(Expr):
    """
    Uma chamada de função.

    Ex.: fat(42)
    """
    callee: str
    params: list[Expr]

    def eval(self, ctx: Ctx):
        func = self.callee.eval(ctx) if isinstance(self.callee, Expr) else self.callee
        params = [param.eval(ctx) for param in self.params]
        if callable(func):
            return func(*params)
        raise TypeError(f"{func} não é uma função!")


@dataclass
class This(Expr):
    """
    Acesso ao `this`.

    Ex.: this
    """
    # Dummy field to ensure dataclass generates __annotations__
    _dummy: None = field(default=None, init=False, repr=False)
    
    def eval(self, ctx: Ctx):
        try:
            return ctx["this"]
        except KeyError:
            raise NameError(f"variável this não existe!")
    
    def validate_self(self, cursor):
        """
        Valida que this só aparece dentro de classes.
        """
        # Percorre todos os pais procurando por uma Class
        for parent_cursor in cursor.parents():
            if isinstance(parent_cursor.node, Class):
                return  # Encontrou uma Class, está válido
        
        # Se chegou aqui, não encontrou nenhuma Class nos pais
        from .errors import SemanticError
        raise SemanticError("Can't use 'this' outside of a class.", "this")



@dataclass
class Super(Expr):
    """
    Acesso a method ou atributo da superclasse.

    Ex.: super.x
    """
    method_name: str
    
    def eval(self, ctx: Ctx):
        try:
            super_class = ctx["super"]
            this_instance = ctx["this"]
            method = super_class.get_method(self.method_name)
            return method.bind(this_instance)
        except KeyError as e:
            if "super" in str(e):
                raise NameError("variável super não existe!")
            elif "this" in str(e):
                raise NameError("variável this não existe!")
            else:
                raise
    
    def validate_self(self, cursor):
        """
        Valida que super só aparece dentro de classes que herdam de outras classes.
        """
        # Percorre todos os pais procurando por uma Class
        for parent_cursor in cursor.parents():
            if isinstance(parent_cursor.node, Class):
                class_node = parent_cursor.node
                # Verifica se a classe tem uma superclasse
                if class_node.superclass is not None:
                    return  # Encontrou uma Class com superclasse, está válido
                else:
                    raise SemanticError("Can't use 'super' in a class with no superclass.", "super")
        
        # Se chegou aqui, não encontrou nenhuma Class nos pais
        raise SemanticError("Can't use 'super' outside of a class.", "super")


@dataclass
class Assign(Expr):
    """
    Atribuição de variável.

    Ex.: x = 42
    """
    name: str
    value: Expr

    def eval(self, ctx: Ctx):
        value = self.value.eval(ctx)
        ctx[self.name] = value
        return value


@dataclass
class Getattr(Expr):
    """
    Acesso a atributo de um objeto.
    
    Ex.: x.y
    """
    obj: Expr
    attr: str

    def eval(self, ctx: Ctx):
        base = self.obj.eval(ctx)
        
        # Se for uma instância de LoxInstance, use o método get
        if isinstance(base, LoxInstance):
            return base.get(self.attr)
        
        # Se for um objeto LoxSuper, procure o método na superclasse
        if isinstance(base, LoxSuper):
            return base.superclass.get_method(self.attr)
        
        # Para outros objetos, use getattr padrão
        try:
            return getattr(base, self.attr)
        except AttributeError:
            raise AttributeError(f"O objeto '{base}' não possui o atributo '{self.attr}'")


@dataclass
class Setattr(Expr):
    obj: Expr
    attr: str
    value: Expr

    def eval(self, ctx: Ctx):
        obj_value = self.obj.eval(ctx)
        value = self.value.eval(ctx)
        
        # Se for uma instância de LoxInstance, use o método set
        if isinstance(obj_value, LoxInstance):
            obj_value.set(self.attr, value)
            return value
        
        # Em Lox, não podemos definir atributos em classes ou funções
        if isinstance(obj_value, (LoxClass, LoxFunction)):
            raise RuntimeError("Only instances have fields.")
        
        # Para outros objetos, use setattr padrão
        setattr(obj_value, self.attr, value)
        return value


#
# COMANDOS
#
@dataclass
class Print(Stmt):
    """
    Representa uma instrução de impressão.

    Ex.: print "Hello, world!";
    """

    expr: Expr

    def eval(self, ctx: Ctx):
        from .runtime import show
        value = self.expr.eval(ctx)
        print(show(value))


@dataclass
class Return(Stmt):
    """
    Representa uma instrução de retorno.

    Ex.: return x;
    """
    value: Expr

    def eval(self, ctx: Ctx):
        value = self.value.eval(ctx)
        raise LoxReturn(value)
    
    def validate_self(self, cursor):
        """
        Valida que return só aparece dentro de funções e que não retorna valor de inicializadores.
        """
        from .errors import SemanticError
        
        # Percorre todos os pais procurando por uma Function
        for parent_cursor in cursor.parents():
            if isinstance(parent_cursor.node, Function):
                # Verifica se está dentro de um método init de uma classe
                if parent_cursor.node.name == "init":
                    # Verifica se a função está diretamente dentro de uma classe (não aninhada)
                    parent = parent_cursor.parent()
                    if isinstance(parent.node, Class):
                        # Se o valor não for None, é um erro
                        if not isinstance(self.value, Literal) or self.value.value is not None:
                            raise SemanticError("Can't return a value from an initializer.", token="return")
                return  # Encontrou uma Function, está válido
        
        # Se chegou aqui, não encontrou nenhuma Function nos pais
        raise SemanticError("Can't return from top-level code.", token="return")


@dataclass
class VarDef(Stmt):
    """
    Representa uma declaração de variável.

    Ex.: var x = 42;
    """
    name: str
    value: Expr

    def eval(self, ctx: Ctx):
        key = self.name
        value = self.value.eval(ctx)
        ctx.var_def(key, value)  # <-- troque define por var_def!
    
    def validate_self(self, cursor: Cursor):
        """
        Valida que o nome da variável não é uma palavra reservada e que não está sendo usada em seu próprio inicializador.
        """
        if self.name in RESERVED_WORDS:
            raise SemanticError(f"Expect variable name.", token=self.name)
        
        # Verifica se a variável está sendo usada em seu próprio inicializador
        if self._uses_variable_in_expression(self.value, self.name):
            # Verifica se está no mesmo escopo (bloco)
            for parent_cursor in cursor.parents():
                if isinstance(parent_cursor.node, Block):
                    # Se está dentro de um bloco, é uma variável local
                    raise SemanticError("Can't read local variable in its own initializer.", token=self.name)
                elif isinstance(parent_cursor.node, Program):
                    # Se está no nível do programa, é uma variável global (permitido)
                    break
    
    def _uses_variable_in_expression(self, expr, var_name):
        """Verifica recursivamente se uma expressão usa uma variável específica."""
        if isinstance(expr, Var):
            return expr.name == var_name
        elif isinstance(expr, BinOp):
            return (self._uses_variable_in_expression(expr.left, var_name) or 
                   self._uses_variable_in_expression(expr.right, var_name))
        elif isinstance(expr, UnaryOp):
            return self._uses_variable_in_expression(expr.expr, var_name)
        elif isinstance(expr, Call):
            # Verifica se o callee usa a variável
            if isinstance(expr.callee, Expr):
                if self._uses_variable_in_expression(expr.callee, var_name):
                    return True
            # Verifica se os parâmetros usam a variável
            for param in expr.params:
                if self._uses_variable_in_expression(param, var_name):
                    return True
        elif isinstance(expr, Getattr):
            return self._uses_variable_in_expression(expr.obj, var_name)
        elif isinstance(expr, Setattr):
            return (self._uses_variable_in_expression(expr.obj, var_name) or 
                   self._uses_variable_in_expression(expr.value, var_name))
        elif isinstance(expr, Assign):
            return self._uses_variable_in_expression(expr.value, var_name)
        elif isinstance(expr, (Literal, This, Super)):
            return False
        return False


@dataclass
class If(Stmt):
    """
    Representa uma instrução condicional.

    Ex.: if (x > 0) { ... } else { ... }
    """
    cond: Expr
    then: Stmt
    orelse: Stmt

    def eval(self, ctx: Ctx):
        cond = self.cond.eval(ctx)
        if is_lox_true(cond):
            self.then.eval(ctx)
        else:
            self.orelse.eval(ctx)





@dataclass
class While(Stmt):
    """
    Representa um laço de repetição.

    Ex.: while (x > 0) { ... }
    """
    cond: Expr
    body: Stmt

    def eval(self, ctx: Ctx):
        cond = self.cond.eval(ctx)
        if is_lox_true(cond):
            self.body.eval(ctx)
            self.eval(ctx)


@dataclass
class Block(Stmt):
    """
    Representa bloco de comandos.

    Ex.: { var x = 42; print x;  } 
    """

    stmts: list[Stmt]

    def eval(self, ctx: Ctx):
        # Cria um novo contexto-filho para o bloco
        child_ctx = ctx.child()
        for stmt in self.stmts:
            stmt.eval(child_ctx)
    
    def validate_self(self, cursor: Cursor):
        """
        Valida que não há declarações de variáveis duplicadas no bloco.
        """
        var_names = []
        for stmt in self.stmts:
            if isinstance(stmt, VarDef):
                var_names.append(stmt.name)
        
        # Verifica se há nomes duplicados
        if len(var_names) != len(set(var_names)):
            # Encontra o primeiro nome duplicado
            seen = set()
            for name in var_names:
                if name in seen:
                    raise SemanticError(f"Already a variable with this name in this scope.", token=name)
                seen.add(name)

@dataclass
class LoxFunction:
    """
    Representa uma função lox em tempo de execução
    """

    name: str
    arg_names: list[str]
    body: list[Stmt]
    ctx: Ctx

    def __call__(self, *values):
        """
        self.__call__(*args) <==> self(*args)
        """
        names = self.arg_names
        if len(names) != len(values):
            msg = f"esperava {len(names)} argumentos, recebeu {len(values)}"
            raise TypeError(msg)

        # Associa cada nome em names ao valor correspondente em values
        scope = dict(zip(names, values))

        # Avalia cada comando no corpo da função dentro do escopo local
        ctx = Ctx(scope, self.ctx)
        try:
            for stmt in self.body:
                stmt.eval(ctx)
        except LoxReturn as e:
            return e.value
    
    def bind(self, obj: "Value") -> "LoxFunction":
        """
        Associa essa função a um 'this' específico.
        """
        # Criar um novo contexto que tem 'this' no escopo
        bound_ctx = self.ctx.child()
        bound_ctx.var_def("this", obj)
        
        # Retornar uma nova LoxFunction com o contexto modificado
        return LoxFunction(self.name, self.arg_names, self.body, bound_ctx)
    
    def __str__(self):
        return f"<fn {self.name}>"

class LoxReturn(Exception):
    value: Value

    def __init__(self, value):
        self.value = value
        super().__init__()

@dataclass
class Function(Stmt):
    """
    Representa uma função.

    Ex.: fun f(x, y) { ... }
    """
    name: str
    arg_names: list[str]
    body: list[Stmt]

    def eval(self, ctx: Ctx):
        func = LoxFunction(self.name, self.arg_names, self.body, ctx)
        ctx.var_def(self.name, func)
        return func
    
    def validate_self(self, cursor: Cursor):
        """
        Valida que não há parâmetros duplicados e que parâmetros não são palavras reservadas.
        Também verifica se variáveis locais não colidem com parâmetros.
        """
        # Verifica parâmetros duplicados
        if len(self.arg_names) != len(set(self.arg_names)):
            # Encontra o primeiro nome duplicado
            seen = set()
            for name in self.arg_names:
                if name in seen:
                    raise SemanticError(f"Already a variable with this name in this scope.", token=name)
                seen.add(name)
        
        # Verifica se parâmetros são palavras reservadas
        for param in self.arg_names:
            if param in RESERVED_WORDS:
                raise SemanticError(f"Expect variable name.", token=param)
        
        # Verifica se variáveis locais colidem com parâmetros
        param_set = set(self.arg_names)
        self._check_vardefs_in_body(self.body, param_set)
    
    def _check_vardefs_in_body(self, stmts: list[Stmt], param_set: set[str]):
        """
        Verifica recursivamente se há declarações de variáveis que colidem com parâmetros.
        """
        for stmt in stmts:
            if isinstance(stmt, VarDef):
                if stmt.name in param_set:
                    raise SemanticError(f"Already a variable with this name in this scope.", token=stmt.name)
            elif isinstance(stmt, Block):
                self._check_vardefs_in_body(stmt.stmts, param_set)



@dataclass
class Class(Stmt):
    """
    Representa uma classe.

    Ex.: class B < A { ... }
    """
    name: str
    superclass: Optional[Expr] = None
    methods: list[Stmt] = field(default_factory=list)

    def eval(self, ctx: Ctx):
        # Carrega a superclasse, caso exista
        superclass = None
        if self.superclass is not None:
            try:
                superclass = self.superclass.eval(ctx)
                # Verifica se a superclasse é realmente uma classe
                if not isinstance(superclass, LoxClass):
                    raise RuntimeError("Superclass must be a class.")
            except RuntimeError:
                raise
            except:
                superclass = None
        
        class_name = self.name
        method_defs = self.methods
        
        # Criamos um escopo para os métodos possivelmente diferente do escopo 
        # onde a classe está declarada
        if superclass is None:
            method_ctx = ctx
        else:
            method_ctx = ctx.child()
            method_ctx.var_def("super", superclass)
        
        # Avaliamos cada método
        methods = {}
        for method in method_defs:
            # não podemos simplesmente avaliar method.eval(ctx) porque isso 
            # acrescentaria { method.name: method_impl } ao contexto de execução.
            method_name = method.name
            method_body = method.body
            method_args = method.arg_names
            method_impl = LoxFunction(method_name, method_args, method_body, method_ctx)
            methods[method_name] = method_impl

        lox_class = LoxClass(class_name, methods, superclass)
        ctx.var_def(self.name, lox_class)
        return lox_class

    def validate_self(self, cursor):
        # Validação: uma classe não pode herdar dela mesma
        if self.superclass is not None and isinstance(self.superclass, Var):
            if self.superclass.name == self.name:
                from .errors import SemanticError
                raise SemanticError("A class can't inherit from itself.", token=self.name)
        # Chama validação dos métodos
        for method in self.methods:
            method.validate_self(cursor)


def is_lox_true(value):
    from .runtime import truthy
    return truthy(value)

@dataclass
class LoxInstance:
    """
    Representa uma instância de uma classe Lox em tempo de execução.
    """
    lox_class: "LoxClass"
    fields: dict[str, "Value"] = field(default_factory=dict)
    
    def __str__(self):
        return f"{self.lox_class.name} instance"
    
    def __getattr__(self, name: str):
        """
        Permite acesso aos campos via atributos Python (u.x ao invés de u.get('x')).
        """
        if name in self.fields:
            return self.fields[name]
        raise AttributeError(f"'{self.lox_class.name} instance' object has no attribute '{name}'")
    
    def __setattr__(self, name: str, value):
        """
        Permite definir campos via atributos Python (u.x = 1 ao invés de u.set('x', 1)).
        """
        # Para atributos especiais da classe, use o comportamento padrão
        if name in ('lox_class', 'fields'):
            super().__setattr__(name, value)
        else:
            # Para outros atributos, armazene nos fields
            self.fields[name] = value
    
    def get(self, name: str):
        """
        Busca um campo ou método na instância.
        """
        # Primeiro, procura nos campos da instância
        if name in self.fields:
            return self.fields[name]
        
        # Tratamento especial para o método init
        if name == "init":
            try:
                self.lox_class.get_method("init")
                # Retorna um callable que sempre retorna a instância
                return lambda *args: self.init(*args)
            except:
                raise AttributeError(f"O objeto '{self}' não possui o atributo '{name}'")
        
        # Se não encontrar, procura nos métodos da classe
        try:
            method = self.lox_class.get_method(name)
            # Bind o método à instância e adiciona super se necessário
            bound_method = method.bind(self)
            
            # Se a classe tem superclasse, cria um wrapper que adiciona super ao contexto
            if self.lox_class.base is not None:
                original_call = bound_method.__call__
                def wrapped_call(*args):
                    # Criar um contexto que contém super
                    super_obj = LoxSuper(self.lox_class.base)
                    
                    # Modificar temporariamente o contexto do método para incluir super
                    old_ctx = bound_method.ctx
                    new_ctx = old_ctx.child()
                    new_ctx.var_def("super", super_obj)
                    bound_method.ctx = new_ctx
                    
                    try:
                        return original_call(*args)
                    finally:
                        bound_method.ctx = old_ctx
                
                bound_method.__call__ = wrapped_call
                
            return bound_method
        except:
            raise AttributeError(f"O objeto '{self}' não possui o atributo '{name}'")
    
    def set(self, name: str, value: "Value"):
        """
        Define um campo na instância.
        """
        self.fields[name] = value
    
    def init(self, *args):
        """
        Método especial para chamadas de init que sempre retorna a instância.
        """
        try:
            init_method = self.lox_class.get_method("init")
            bound_init = init_method.bind(self)
            bound_init(*args)
            return self  # Sempre retorna a instância, não o resultado de init
        except:
            # Se não há método init, apenas retorna a instância
            return self


@dataclass
class LoxClass:
    """
    Representa uma classe Lox em tempo de execução.
    """
    name: str
    methods: dict[str, "LoxFunction"]
    base: Optional["LoxClass"] = None
    
    def __str__(self):
        return self.name
    
    def __call__(self, *args):
        """
        self.__call__(x, y) <==> self(x, y)

        Em Lox, criamos instâncias de uma classe chamando-a como uma função.
        """
        instance = LoxInstance(self)
        
        # Verificar se há um método init e executá-lo automaticamente
        try:
            init_method = self.get_method("init")
            bound_init = init_method.bind(instance)
            bound_init(*args)
        except:
            # Se não há método init, apenas ignore (isso é válido)
            if args:
                # Mas se argumentos foram passados e não há init, é um erro
                raise TypeError(f"Classe {self.name} não possui método init mas recebeu {len(args)} argumentos")
        
        return instance
    
    def get_method(self, name: str) -> "LoxFunction":
        """
        Procura um método na classe atual ou nas suas superclasses.
        """
        # Procure o método na classe atual
        if name in self.methods:
            return self.methods[name]
        
        # Se não encontrar, procure nas bases
        if self.base is not None:
            return self.base.get_method(name)
        
        # Se não existir em nenhum dos dois lugares, levante uma exceção
        from .errors import SemanticError
        raise SemanticError(f"Método '{name}' não encontrado na classe '{self.name}'")

@dataclass
class LoxSuper:
    """
    Representa o objeto 'super' em tempo de execução.
    """
    superclass: "LoxClass"
    
    def __str__(self):
        return f"super"

