
import sys
import os

try:
    from core import ai_content
    print("SUCCESS: core.ai_content imported without syntax errors.")
    
    # Test a function
    prompt = ai_content.get_system_prompt("short")
    if "RULE #1" in prompt:
        print("SUCCESS: get_system_prompt returned expected content.")
    else:
        print("FAILURE: get_system_prompt returned unexpected content.")
        
    # Test fix_description
    desc = ai_content.fix_description("test  content")
    if "" in desc:
         print("SUCCESS: fix_description handles emojis correctly.")
    else:
         print("FAILURE: fix_description failed to handle emojis or markers.")

except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
    sys.exit(1)
except Exception as e:
    print(f"IMPORT ERROR: {e}")
    sys.exit(1)
