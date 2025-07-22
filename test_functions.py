#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from lox.parser import parse
from lox.ctx import Ctx
import io
import contextlib

def test_functions():
    # Test function declaration
    code1 = '''
    fun test() {
        print "hello";
    }
    test();
    '''
    
    print("=== Testing function declaration and call ===")
    print(f"Code: {code1}")
    
    try:
        ast = parse(code1)
        print(f"✅ Parsed successfully: {ast}")
        
        ctx = Ctx()
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            result = ast.eval(ctx)
        
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        print("✅ Function test passed")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_functions()
