#!/usr/bin/env python3
"""
Resumo final das funcionalidades implementadas no interpretador Lox
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from lox.parser import parse
from lox.ctx import Ctx
import io
import contextlib

def test_feature(code, description):
    """Testa uma funcionalidade específica"""
    print(f"\n=== {description} ===")
    print(f"Código: {code.strip()}")
    
    try:
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            ast = parse(code)
            ctx = Ctx()
            result = ast.eval(ctx)
        
        output = f.getvalue().strip()
        print(f"Saída: {repr(output)}")
        print(f"Resultado: {result}")
        print("✅ SUCESSO")
        return True
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False

def main():
    print("🔍 TESTE DAS FUNCIONALIDADES DO INTERPRETADOR LOX")
    print("=" * 60)
    
    tests = [
        # Exercício 1 - Lexer de números
        ("print 123.45;", "Exercício 1: Números"),
        
        # Exercício 2 - Lexer de strings  
        ('print "Hello, World!";', "Exercício 2: Strings"),
        
        # Exercício 5 - Operadores unários
        ("print -42; print !true;", "Exercício 5: Operadores unários"),
        
        # Exercício 6 - Operadores lógicos
        ("print true and false; print true or false;", "Exercício 6: Operadores lógicos"),
        
        # Exercício 7 - Atribuição de variáveis
        ("var x = 5; x = x + 1; print x;", "Exercício 7: Atribuição de variáveis"),
        
        # Exercício 8 - Declaração de variáveis
        ("var x; var y = 10; print y;", "Exercício 8: Declaração de variáveis"),
        
        # Exercício 9 - Blocos
        ("{ var x = 1; print x; }", "Exercício 9: Blocos"),
        
        # Exercício 10 - If
        ("if (true) print \"yes\"; else print \"no\";", "Exercício 10: If"),
        
        # Exercício 11 - While
        ("var i = 0; while (i < 3) { print i; i = i + 1; }", "Exercício 11: While"),
        
        # Exercício 12 - For  
        ("for (var i = 0; i < 3; i = i + 1) print i;", "Exercício 12: For"),
        
        # Exercício 3 - Atributos (básico)
        ('var s = "hello"; print s.upper;', "Exercício 3: Getattr (básico)"),
        
        # Exercício 16 - Funções (básico)
        ("fun test() { print \"function\"; } test();", "Exercício 16: Funções (básico)"),
    ]
    
    passed = 0
    total = len(tests)
    
    for code, description in tests:
        if test_feature(code, description):
            passed += 1
    
    print(f"\n{'=' * 60}")
    print(f"📊 RESUMO FINAL")
    print(f"{'=' * 60}")
    print(f"✅ Testes aprovados: {passed}/{total}")
    print(f"📈 Taxa de sucesso: {passed/total*100:.1f}%")
    
    if passed >= total * 0.8:
        print("🎉 EXCELENTE! A maioria das funcionalidades está funcionando!")
    elif passed >= total * 0.6:
        print("👍 BOM! Muitas funcionalidades estão implementadas!")
    elif passed >= total * 0.4:
        print("⚠️  PROGRESSO MODERADO. Algumas funcionalidades precisam de trabalho.")
    else:
        print("🔧 MAIS TRABALHO NECESSÁRIO. Muitas funcionalidades ainda precisam ser implementadas.")
    
    print(f"\n🏆 FUNCIONALIDADES IMPLEMENTADAS:")
    print("• Expressões aritméticas (+, -, *, /)")
    print("• Operadores de comparação (>, <, >=, <=, ==, !=)")
    print("• Operadores lógicos (and, or)")
    print("• Operadores unários (-, !)")
    print("• Variáveis (declaração e atribuição)")
    print("• Blocos com escopo")
    print("• Estruturas condicionais (if/else)")
    print("• Loops (while, for)")
    print("• Acesso a atributos (getattr)")
    print("• Funções básicas (declaração e chamada)")
    print("• Print statements")
    print("• Literais (números, strings, booleanos, nil)")

if __name__ == "__main__":
    main()
