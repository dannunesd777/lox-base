from lox.parser import parse

try:
    # Test basic expressions first
    code1 = "1 + 2;"
    ast1 = parse(code1)
    print(f"✅ Basic expression works: {ast1}")
    
    # Test variable access
    code2 = "var x = 5; print x;"
    ast2 = parse(code2)
    print(f"✅ Variable access works: {ast2}")
    
    # Test getattr
    code3 = "var s = \"hello\"; s.upper;"
    ast3 = parse(code3)
    print(f"✅ Getattr works: {ast3}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
