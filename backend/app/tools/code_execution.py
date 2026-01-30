# app/tools/code_execution.py - ENHANCED VERSION
import io
import sys
import subprocess
import tempfile
import os
import json
import re
from contextlib import redirect_stdout
from typing import Dict, Optional
import base64

def safe_execute_code(code: str) -> str:
    """
    Safe code execution in restricted namespace (EXISTING FUNCTION - KEPT)
    """
    restricted_globals = {
        "__builtins__": {
            "print": print,
            "range": range,
            "len": len,
            "int": int,
            "str": str,
            "float": float,
            "list": list,
            "dict": dict,
            "set": set,
            "tuple": tuple,
            "sum": sum,
            "max": max,
            "min": min,
            "abs": abs,
            "round": round,
            "sorted": sorted,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
        }
    }
    
    output = io.StringIO()
    with redirect_stdout(output):
        try:
            exec(code, restricted_globals)
        except Exception as e:
            print(f"Execution error: {str(e)}")
    
    return output.getvalue().strip()


# ============================================================================
# NEW ENHANCED FUNCTIONS BELOW
# ============================================================================

def execute_python_with_output(code: str, timeout: int = 10) -> Dict:
    """
    Execute Python code with output capture and visualization support
    More powerful than safe_execute_code - supports matplotlib, numpy, etc.
    """
    try:
        # Check if matplotlib is needed
        needs_matplotlib = any(lib in code for lib in ['matplotlib', 'plt.', 'pyplot'])
        
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Build wrapper code
            wrapper_parts = [
                "import sys",
                "import io",
            ]
            
            if needs_matplotlib:
                wrapper_parts.extend([
                    "import matplotlib",
                    "matplotlib.use('Agg')",
                    "import matplotlib.pyplot as plt",
                    "import base64"
                ])
            
            wrapper_parts.extend([
                "",
                "# Capture stdout",
                "old_stdout = sys.stdout",
                "sys.stdout = captured_output = io.StringIO()",
                "",
                "try:"
            ])
            
            # Add user code (indented)
            wrapper_parts.extend(['    ' + line for line in code.split('\n')])
            
            if needs_matplotlib:
                wrapper_parts.extend([
                    "",
                    "    # Capture any plots",
                    "    plot_data = None",
                    "    if len(plt.get_fignums()) > 0:",
                    "        buf = io.BytesIO()",
                    "        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')",
                    "        buf.seek(0)",
                    "        plot_data = base64.b64encode(buf.read()).decode('utf-8')",
                    "        plt.close('all')",
                    "    ",
                    "    if plot_data:",
                    "        print('__PLOT_DATA__:', plot_data)"
                ])
            
            wrapper_parts.extend([
                "",
                "except Exception as e:",
                "    print(f'Error: {type(e).__name__}: {e}')",
                "finally:",
                "    sys.stdout = old_stdout",
                "    output = captured_output.getvalue()",
                "    print('__OUTPUT_START__')",
                "    print(output)",
                "    print('__OUTPUT_END__')"
            ])
            
            wrapped_code = '\n'.join(wrapper_parts)
            f.write(wrapped_code)
            temp_file = f.name
        
        # Execute with timeout - Windows compatible
        # Try python3 first, fallback to python (for Windows)
        python_cmd = 'python3' if os.name != 'nt' else 'python'
        
        result = subprocess.run(
            [python_cmd, temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        # Parse output
        output = result.stdout
        error = result.stderr
        
        # Extract plot data
        plot_match = re.search(r'__PLOT_DATA__: (.+)', output)
        plot_base64 = plot_match.group(1) if plot_match and plot_match.group(1) != "None" else None
        
        # Extract text output
        text_match = re.search(r'__OUTPUT_START__\n(.*)\n__OUTPUT_END__', output, re.DOTALL)
        text_output = text_match.group(1).strip() if text_match else output
        
        # Remove plot marker from text output
        if plot_base64:
            text_output = re.sub(r'__PLOT_DATA__:.*', '', text_output).strip()
        
        return {
            'success': result.returncode == 0,
            'output': text_output,
            'error': error if error else None,
            'plot': plot_base64,
            'return_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': f'Code execution timed out after {timeout} seconds',
            'plot': None,
            'return_code': -1
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': f'Execution error: {str(e)}',
            'plot': None,
            'return_code': -1
        }
    finally:
        # Cleanup
        try:
            if 'temp_file' in locals():
                os.unlink(temp_file)
        except:
            pass


def execute_javascript_code(code: str, timeout: int = 10) -> Dict:
    """
    Execute JavaScript code using Node.js
    """
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
            # Wrap code to capture console output
            wrapped_code = f"""
const originalLog = console.log;
let output = [];
console.log = (...args) => {{
    output.push(args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
    ).join(' '));
}};

try {{
{chr(10).join('    ' + line for line in code.split(chr(10)))}
}} catch(e) {{
    console.log('Error:', e.message);
}}

console.log = originalLog;
console.log(output.join('\\n'));
"""
            f.write(wrapped_code)
            temp_file = f.name
        
        result = subprocess.run(
            ['node', temp_file],
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        return {
            'success': result.returncode == 0,
            'output': result.stdout.strip(),
            'error': result.stderr if result.stderr else None,
            'return_code': result.returncode
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': '',
            'error': f'Code execution timed out after {timeout} seconds',
            'return_code': -1
        }
    except FileNotFoundError:
        return {
            'success': False,
            'output': '',
            'error': 'Node.js is not installed. Install it to run JavaScript code.',
            'return_code': -1
        }
    except Exception as e:
        return {
            'success': False,
            'output': '',
            'error': f'Execution error: {str(e)}',
            'return_code': -1
        }
    finally:
        try:
            if 'temp_file' in locals():
                os.unlink(temp_file)
        except:
            pass


def detect_code_in_response(text: str) -> Optional[Dict]:
    """
    Detect code blocks in LLM response and extract them
    """
    # Match ```python or ```javascript code blocks
    patterns = [
        (r'```python\n(.*?)\n```', 'python'),
        (r'```py\n(.*?)\n```', 'python'),
        (r'```javascript\n(.*?)\n```', 'javascript'),
        (r'```js\n(.*?)\n```', 'javascript'),
    ]
    
    for pattern, lang in patterns:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return {
                'code': match.group(1),
                'language': lang,
                'full_match': match.group(0)
            }
    
    return None


def should_execute_code(question: str) -> bool:
    """
    Determine if the question requires code execution
    """
    keywords = [
        'calculate', 'compute', 'plot', 'graph', 'visualize', 'chart',
        'run this code', 'execute', 'show output', 'what does this print',
        'solve using code', 'write and run', 'test this code',
        'run the code', 'execute the code', 'show me the output',
        'what will this print', 'trace this code', 'debug this'
    ]
    
    q_lower = question.lower()
    return any(kw in q_lower for kw in keywords)


def format_code_result(result: Dict, language: str = 'python') -> str:
    """
    Format code execution result for display
    """
    parts = []
    
    if result['success']:
        if result['output']:
            parts.append(f"**{language.capitalize()} Output:**")
            parts.append("```")
            parts.append(result['output'])
            parts.append("```")
        
        if result.get('plot'):
            parts.append("\n**Generated Plot:**")
            parts.append(f"![Plot](data:image/png;base64,{result['plot']})")
    else:
        parts.append(f"**Execution Error:**")
        parts.append("```")
        parts.append(result.get('error', 'Unknown error'))
        parts.append("```")
    
    return "\n".join(parts)


# ============================================================================
# HELPER FUNCTIONS FOR INTEGRATION
# ============================================================================

def execute_code_from_question(question: str, llm_response: str) -> Optional[str]:
    """
    Complete workflow: detect if code should run, execute it, format result
    Use this function in your LLM integration
    """
    # Check if we should execute
    if not should_execute_code(question):
        return None
    
    # Detect code in LLM response
    code_block = detect_code_in_response(llm_response)
    if not code_block:
        return None
    
    # Execute based on language
    if code_block['language'] == 'python':
        result = execute_python_with_output(code_block['code'])
    elif code_block['language'] == 'javascript':
        result = execute_javascript_code(code_block['code'])
    else:
        return None
    
    # Format and return
    return format_code_result(result, code_block['language'])


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Test 1: Simple Python
    print("Test 1: Simple Python")
    print("=" * 60)
    code1 = """
result = sum([1, 2, 3, 4, 5])
print(f"Sum of 1-5: {result}")

for i in range(3):
    print(f"Loop {i}")
"""
    result1 = execute_python_with_output(code1)
    print("Success:", result1['success'])
    print("Output:", result1['output'])
    print()
    
    # Test 2: Python with Plot
    print("Test 2: Python with Matplotlib")
    print("=" * 60)
    code2 = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.figure(figsize=(8, 4))
plt.plot(x, y, 'b-', linewidth=2)
plt.title('Sine Wave')
plt.xlabel('X')
plt.ylabel('Y')
plt.grid(True, alpha=0.3)

print("Plot generated successfully!")
"""
    result2 = execute_python_with_output(code2)
    print("Success:", result2['success'])
    print("Output:", result2['output'])
    print("Has Plot:", bool(result2['plot']))
    if result2['plot']:
        print("Plot data length:", len(result2['plot']))
    print()
    
    # Test 3: JavaScript
    print("Test 3: JavaScript")
    print("=" * 60)
    code3 = """
const factorial = (n) => n <= 1 ? 1 : n * factorial(n - 1);

console.log('Factorial of 5:', factorial(5));
console.log('Factorial of 10:', factorial(10));

const arr = [1, 2, 3, 4, 5];
console.log('Sum:', arr.reduce((a, b) => a + b, 0));
"""
    result3 = execute_javascript_code(code3)
    print("Success:", result3['success'])
    print("Output:", result3['output'])
    print()
    
    # Test 4: Legacy safe_execute_code
    print("Test 4: Safe Execute (Legacy)")
    print("=" * 60)
    code4 = """
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
print(f"Total: {total}")
"""
    result4 = safe_execute_code(code4)
    print("Output:", result4)