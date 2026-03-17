
import os
import re

def sanitize_file(filepath):
    try:
        with open(filepath, 'rb') as f:
            content = f.read().decode('utf-8', errors='ignore')
        
        # Normalize line endings to LF
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove non-ASCII characters
        sanitized = "".join(c for c in content if ord(c) < 128)
        
        # Specific structural fixes if any known issues remain
        # (Already handled in previous surgical fixes, but good to be safe)
        
        with open(filepath, 'w', newline='\n', encoding='ascii') as f:
            f.write(sanitized)
        return True
    except Exception as e:
        print(f"Error sanitizing {filepath}: {e}")
        return False

py_files = []
for root, dirs, files in os.walk('.'):
    if '.git' in dirs:
        dirs.remove('.git')
    for file in files:
        if file.endswith('.py'):
            py_files.append(os.path.join(root, file))

print(f"Sanitizing {len(py_files)} files...")
for py_file in py_files:
    if sanitize_file(py_file):
        print(f"  [CLEAN] {py_file}")

import py_compile
print("\nFinal Syntax Check:")
errors = 0
for py_file in py_files:
    try:
        py_compile.compile(py_file, doraise=True)
        print(f"  [OK] {py_file}")
    except py_compile.PyCompileError as e:
        print(f"  [FAIL] {py_file}: {e}")
        errors += 1

if errors == 0:
    print("\nALL FILES ARE SYNTACTICALLY VALID AND SANITIZED.")
else:
    print(f"\nCOMPILATION FAILED: {errors} errors found.")
