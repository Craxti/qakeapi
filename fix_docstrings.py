#!/usr/bin/env python3
"""Script to add blank lines after docstrings"""
import re
import os
from pathlib import Path

def fix_docstring_blank_lines(file_path):
    """Add blank line after docstring if missing"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Pattern: docstring followed immediately by non-blank line
        # Match: """..."""\n[non-whitespace]
        pattern = r'("""[\s\S]*?""")\n([^\n\s])'
        
        def replace_func(match):
            docstring = match.group(1)
            next_char = match.group(2)
            return f'{docstring}\n\n{next_char}'
        
        new_content = re.sub(pattern, replace_func, content)
        
        if new_content != content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Process all Python files"""
    directories = ['examples', 'qakeapi', 'tests']
    fixed_count = 0
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    if fix_docstring_blank_lines(file_path):
                        print(f"Fixed: {file_path}")
                        fixed_count += 1
    
    print(f"\nFixed {fixed_count} files")

if __name__ == '__main__':
    main()

