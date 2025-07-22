#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from lox.parser import parse
from lox.ctx import Ctx

# Teste simples
code = """
for (var i = 0; i < 3; i = i + 1) {
    print i;
}
"""

try:
    ast = parse(code)
    print("AST criado com sucesso:", ast)
    
    ctx = Ctx()
    result = ast.eval(ctx)
    print("Execução concluída:", result)
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()
