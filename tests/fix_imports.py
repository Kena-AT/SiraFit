import re
import os

def deduplicate_imports(filepath):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove all lines containing 'import { test, expect } from "@playwright/test";'
    content = re.sub(r'import\s+\{\s*test,\s*expect\s*\}\s+from\s+[\'\"]@playwright/test[\'\"];?', '', content)
    
    # Put one at the very top
    content = 'import { test, expect } from "@playwright/test";\n\n' + content
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

deduplicate_imports(r'C:\Users\hp\Documents\Programming\Projects\SiraFit\tests\e2e_features.spec.ts')
deduplicate_imports(r'C:\Users\hp\Documents\Programming\Projects\SiraFit\tests\e2e_auth.spec.ts')
