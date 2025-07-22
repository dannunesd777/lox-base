from lox.parser import parse_expr
from lox.ast import Getattr

# Test parsing of getattr
try:
    code = "obj.attr"
    ast = parse_expr(code)
    print(f"Parsed: {ast}")
    print(f"Type: {type(ast)}")
    
    if isinstance(ast, Getattr):
        print(f"✅ obj: {ast.obj}")
        print(f"✅ attr: {ast.attr} (type: {type(ast.attr)})")
        
        # Check if attr is a string
        if isinstance(ast.attr, str):
            print("✅ Attribute name is stored as string")
        else:
            print(f"❌ Attribute name should be string, got {type(ast.attr)}")
    else:
        print(f"❌ Expected Getattr, got {type(ast)}")
        
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
