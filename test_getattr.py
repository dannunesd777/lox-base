#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from lox.parser import parse
from lox.ctx import Ctx
import io
import contextlib

def test_getattr():
    code = '''
    var s = "hello world";
    print s.upper;
    '''
    
    print("Testing getattr...")
    print(f"Code: {code}")
    
    try:
        ast = parse(code)
        print(f"AST: {ast}")
        
        ctx = Ctx()
        ctx.set("s", "hello world")  # Set up a string object
        
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            result = ast.eval(ctx)
        
        output = f.getvalue()
        print(f"Output: {repr(output)}")
        print("✅ SUCCESS")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_getattr()
