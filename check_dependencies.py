#!/usr/bin/env python3
import os
import re
import ast
import sys
from pathlib import Path

# Standard library modules to ignore
STDLIB_MODULES = {
    "abc", "argparse", "array", "asyncio", "base64", "collections", "concurrent", "contextlib",
    "copy", "csv", "datetime", "decimal", "enum", "functools", "glob", "hashlib", "http",
    "importlib", "inspect", "io", "itertools", "json", "logging", "math", "multiprocessing",
    "operator", "os", "pathlib", "pickle", "platform", "queue", "random", "re", "shutil",
    "signal", "socket", "sqlite3", "string", "struct", "subprocess", "sys", "tempfile",
    "threading", "time", "traceback", "types", "typing", "unittest", "urllib", "uuid",
    "warnings", "weakref", "xml", "zipfile", "ast"
}

# Internal modules to ignore (project-specific imports)
INTERNAL_MODULES = {
    "burmese_movies_crawler", "link_utils", "movies_spider"
}

# Required runtime dependencies to check
REQUIRED_RUNTIME_DEPS = {
    "scrapy", "selenium", "fuzzywuzzy", "beautifulsoup4", "pydantic", 
    "python-dotenv", "requests", "rich", "gql", "itemadapter", "pyyaml",
    "trafilatura", "lxml", "twisted", "zope.interface", "service_identity"
}

# Required dev tools to check
REQUIRED_DEV_TOOLS = {
    "black", "coverage", "isort", "pylint", "pytest", "pytest-cov", "ruff"
}

# Performance optimization packages
PERFORMANCE_PACKAGES = {
    "python-levenshtein": "Speeds up fuzzywuzzy string matching by 4-10x"
}

def extract_imports_from_file(file_path):
    """Extract all import statements from a Python file."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    imports = set()
    
    try:
        tree = ast.parse(content)
        for node in ast.walk(tree):
            # Handle 'import x' statements
            if isinstance(node, ast.Import):
                for name in node.names:
                    # Get the top-level package name
                    top_level = name.name.split('.')[0]
                    if top_level not in STDLIB_MODULES and top_level not in INTERNAL_MODULES:
                        imports.add(top_level)
            
            # Handle 'from x import y' statements
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Get the top-level package name
                    top_level = node.module.split('.')[0]
                    if top_level not in STDLIB_MODULES and top_level not in INTERNAL_MODULES:
                        imports.add(top_level)
    except SyntaxError:
        # If there's a syntax error, try a regex-based approach as fallback
        import_pattern = r'^import\s+([a-zA-Z0-9_.,\s]+)|^from\s+([a-zA-Z0-9_.]+)\s+import'
        for line in content.split('\n'):
            match = re.match(import_pattern, line.strip())
            if match:
                modules = match.group(1) or match.group(2)
                if modules:
                    for module in re.split(r',\s*', modules):
                        top_level = module.strip().split('.')[0]
                        if top_level not in STDLIB_MODULES and top_level not in INTERNAL_MODULES:
                            imports.add(top_level)
    
    return imports

def parse_requirements_file(file_path):
    """Parse requirements file and extract package names and versions."""
    requirements = {}
    
    if not os.path.exists(file_path):
        return requirements
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments, empty lines, and -r references
            if not line or line.startswith('#') or line.startswith('-r'):
                continue
            
            # Handle commented out packages
            if '#' in line:
                line = line.split('#')[0].strip()
                if not line:
                    continue
            
            # Extract package name and version
            package_name = None
            version = None
            
            if '==' in line:
                package_name, version = line.split('==', 1)
                version = f"=={version}"
            elif '>=' in line:
                package_name, version = line.split('>=', 1)
                version = f">={version}"
            elif '<=' in line:
                package_name, version = line.split('<=', 1)
                version = f"<={version}"
            elif '[' in line:
                # Handle packages with extras like 'psycopg[binary]'
                package_name = line.split('[', 1)[0].strip()
            else:
                # No version specified
                package_name = line
            
            if package_name:
                requirements[package_name.lower()] = version
    
    return requirements

def main():
    repo_root = Path('/home/kaungkk/Repositories/BRAWL-Burmese-movies-cRAWLer-')
    runtime_requirements_path = repo_root / 'requirements.txt'
    dev_requirements_path = repo_root / 'requirements-dev.txt'
    
    # Get all Python files excluding tests and docs for runtime dependencies
    runtime_files = []
    for root, dirs, files in os.walk(repo_root):
        # Skip tests, docs, and hidden directories
        if any(part.startswith('.') for part in Path(root).parts) or \
           'tests' in Path(root).parts or 'docs' in Path(root).parts:
            continue
        
        for file in files:
            if file.endswith('.py'):
                runtime_files.append(os.path.join(root, file))
    
    # Get test files for dev dependencies
    test_files = []
    for root, dirs, files in os.walk(repo_root / 'tests'):
        for file in files:
            if file.endswith('.py'):
                test_files.append(os.path.join(root, file))
    
    # Extract all imports from Python files
    runtime_imports = set()
    for file_path in runtime_files:
        imports = extract_imports_from_file(file_path)
        runtime_imports.update(imports)
    
    test_imports = set()
    for file_path in test_files:
        imports = extract_imports_from_file(file_path)
        test_imports.update(imports)
    
    # Parse requirements files
    runtime_requirements = parse_requirements_file(runtime_requirements_path)
    dev_requirements = parse_requirements_file(dev_requirements_path)
    
    # Normalize package names for comparison
    normalized_runtime_imports = {pkg.lower() for pkg in runtime_imports}
    normalized_test_imports = {pkg.lower() for pkg in test_imports}
    
    # Special case mappings for packages with different import names
    package_mappings = {
        'bs4': 'beautifulsoup4',
        'yaml': 'pyyaml',
        'PIL': 'pillow',
        'dotenv': 'python-dotenv',
    }
    
    # Apply mappings to runtime imports
    for import_name, req_name in package_mappings.items():
        if import_name.lower() in normalized_runtime_imports:
            normalized_runtime_imports.remove(import_name.lower())
            normalized_runtime_imports.add(req_name.lower())
    
    # Apply mappings to test imports
    for import_name, req_name in package_mappings.items():
        if import_name.lower() in normalized_test_imports:
            normalized_test_imports.remove(import_name.lower())
            normalized_test_imports.add(req_name.lower())
    
    # Check required runtime dependencies
    missing_runtime_deps = set()
    for dep in REQUIRED_RUNTIME_DEPS:
        if dep.lower() not in runtime_requirements:
            missing_runtime_deps.add(dep)
    
    # Check required dev tools
    missing_dev_tools = set()
    for tool in REQUIRED_DEV_TOOLS:
        if tool.lower() not in dev_requirements:
            missing_dev_tools.add(tool)
    
    # Check for incorrect version pinning in dev tools
    incorrect_pinning = set()
    for tool in REQUIRED_DEV_TOOLS:
        if tool.lower() in dev_requirements:
            version = dev_requirements[tool.lower()]
            if tool not in ["pytest", "pytest-cov"] and (not version or not version.startswith("==")):
                incorrect_pinning.add(f"{tool} (has {version or 'no version'}, should use ==)")
    
    # Find unused runtime packages
    unused_runtime_packages = set(runtime_requirements.keys()) - normalized_runtime_imports
    
    # Remove packages that are required but might not be directly imported
    required_but_not_imported = {
        'lxml',  # Used by beautifulsoup4 and scrapy
        'twisted',  # Used by scrapy
        'zope.interface',  # Used by twisted
        'service_identity',  # Used by twisted
        'python-levenshtein',  # Optional for fuzzywuzzy
    }
    
    unused_runtime_packages = {pkg for pkg in unused_runtime_packages 
                              if pkg.lower() not in {r.lower() for r in required_but_not_imported}}
    
    # Check for performance optimization packages
    missing_performance_packages = set()
    for pkg, reason in PERFORMANCE_PACKAGES.items():
        if pkg.lower() not in runtime_requirements and pkg.lower() not in dev_requirements:
            missing_performance_packages.add(f"{pkg} - {reason}")
    
    # Check for critical transitive dependencies that should be pinned
    critical_transitive = set()
    for dep in ["twisted", "lxml", "zope.interface", "service_identity"]:
        if dep.lower() not in runtime_requirements:
            critical_transitive.add(dep)
    
    # Print results
    all_accounted_for = not missing_runtime_deps and not missing_dev_tools and not incorrect_pinning
    
    print("✔️ All packages accounted for:", "Yes" if all_accounted_for else "No")
    
    if missing_runtime_deps:
        print("\n🚫 Missing runtime dependencies:")
        for pkg in sorted(missing_runtime_deps):
            print(f"  - {pkg}")
    
    if missing_dev_tools:
        print("\n🚫 Missing development tools:")
        for pkg in sorted(missing_dev_tools):
            print(f"  - {pkg}")
    
    if incorrect_pinning:
        print("\n⚠️ Development tools with incorrect version pinning:")
        for pkg in sorted(incorrect_pinning):
            print(f"  - {pkg}")
    
    if unused_runtime_packages:
        print("\n📦 Unused packages:")
        for pkg in sorted(unused_runtime_packages):
            print(f"  - {pkg} ({runtime_requirements.get(pkg) or 'no version specified'})")
    
    if missing_performance_packages:
        print("\n⚠️ Suggested performance optimizations:")
        for pkg in sorted(missing_performance_packages):
            print(f"  - {pkg}")
    
    if critical_transitive:
        print("\n📌 Recommendations to pin critical transitive dependencies:")
        for pkg in sorted(critical_transitive):
            print(f"  - {pkg} - Used by scrapy but not explicitly pinned")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())