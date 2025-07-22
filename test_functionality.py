#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from lox.parser import parse
from lox.ctx import Ctx
import io
import contextlib

def test_code(code, description):
    print(f"\n=== {description} ===")
    print(f"Code: {code}")
    
    try:
        # Capture stdout
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            ast = parse(code)
            ctx = Ctx()
            result = ast.eval(ctx)
        
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        print(f"Result: {result}")
        print("✅ SUCCESS")
        return True
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

# Test basic functionality
tests = [
    ("1 + 2 * 3;", "Basic arithmetic"),
    ("var x = 5; print x;", "Variable declaration and print"),
    ("var x = 5; x = x + 1; print x;", "Variable assignment"),
    ("if (true) print \"yes\"; else print \"no\";", "If statement"),
    ("{ var x = 1; print x; }", "Block scope"),
    ("var i = 0; while (i < 3) { print i; i = i + 1; }", "While loop"),
    ("for (var i = 0; i < 3; i = i + 1) print i;", "For loop"),
]

passed = 0
total = len(tests)

for code, desc in tests:
    if test_code(code, desc):
        passed += 1

print(f"\n=== SUMMARY ===")
print(f"Passed: {passed}/{total}")
print(f"Success rate: {passed/total*100:.1f}%")
