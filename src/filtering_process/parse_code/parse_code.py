import ast
import re
import cssutils
import subprocess
import json

def extract_structure(code, file_type):
    if file_type == 'py':
        # Python file
        return extract_python_structure(code, file_type)
    elif file_type in ('js', 'jsx', 'ts', 'tsx', 'vue'):
        # JS family files
        return extract_js_structure(code, file_type)
    elif file_type == 'html':
        # HTML file
        return extract_html_structure(code, file_type)
    elif file_type == 'css':
        # CSS file
        return extract_css_structure(code)
    else:
        return None

def parse_python_code_flow(node, indent=0):
    result = []
    indent_str = ' ' * indent
    
    if isinstance(node, ast.Module):
        for stmt in node.body:
            result.extend(parse_python_code_flow(stmt, indent))
    elif isinstance(node, ast.FunctionDef):
        result.append(f"{indent_str}Function: {node.name}")
        for stmt in node.body:
            result.extend(parse_python_code_flow(stmt, indent + 2))
    elif isinstance(node, ast.For):
        result.append(f"{indent_str}For Loop")
        for stmt in node.body:
            result.extend(parse_python_code_flow(stmt, indent + 2))
    elif isinstance(node, ast.While):
        result.append(f"{indent_str}While Loop")
        for stmt in node.body:
            result.extend(parse_python_code_flow(stmt, indent + 2))
    elif isinstance(node, ast.If):
        result.append(f"{indent_str}If Statement")
        for stmt in node.body:
            result.extend(parse_python_code_flow(stmt, indent + 2))
        if node.orelse:
            result.append(f"{indent_str}else:")
            for stmt in node.orelse:
                result.extend(parse_python_code_flow(stmt, indent + 2))
    else:
        # Capture other statements without details
        result.append(f"{indent_str}{node.__class__.__name__}")
    return result

def extract_python_structure(code, file_type):
    tree = ast.parse(code)
    flow_representation = parse_python_code_flow(tree)
    return flow_representation

def extract_js_structure(code, file_type):
    structure = []
    
    if file_type == 'vue':
        # Extract structure for Vue files using regular expressions (re)
        tags_and_other = re.findall(r'(<[^\s>]+.*?>|<\/[^\s>]+>)|(\bexport\b|\bimport\b|\bdata\b|\bmethods\b|\bcomputed\b|\blifecycle\b|\bwatch\b|\bprops\b|\bcomponents\b|\btemplate\b)', code)
        structure = [' '.join(item).strip() for item in tags_and_other if any(item)]
    else:
        # Invoke parse.js for JavaScript and TypeScript files
        process = subprocess.Popen(['node', './parse_js.js', code], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        
        if stderr:
            print(f"Error encountered while parsing: {stderr.decode('utf-8')}")
            return structure
        
        try:
            # Parse JSON output from parse.js
            structure = json.loads(stdout.decode('utf-8'))
            
            
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON output from parse.js: {e}")
    
    structure = json.dumps(structure)
    return structure


def extract_html_structure(html_code):
    # Execute Node.js script to parse HTML code from stdin
    process = subprocess.Popen(['node', './parse_html.js'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate(input=html_code.encode('utf-8'))

    # Check for errors
    if stderr:
        print(f"Error encountered: {stderr.decode('utf-8')}")
    else:
        # Parse the result from JSON output (if applicable)
        result = json.loads(stdout.decode('utf-8'))

        # Print parsed result
        return json.dumps(result, indent=2)

def extract_css_structure(css_code, file_type):
    parser = cssutils.CSSParser()
    stylesheet = parser.parseString(css_code)
    
    structure = []
    for rule in stylesheet:
        if isinstance(rule, cssutils.css.CSSStyleRule):
            selectors = [selector.strip() for selector in rule.selectorText.split(",")]
            structure.extend(selectors)
    
    return structure