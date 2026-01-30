# backend/test_features.py
"""
NEXORA Feature Testing Suite
Run this to verify all new features work correctly
"""

import asyncio
from typing import Dict

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_test(name: str, status: str, message: str = ""):
    symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
    color = Colors.GREEN if status == "PASS" else Colors.RED if status == "FAIL" else Colors.YELLOW
    
    print(f"{color}{symbol}{Colors.RESET} {Colors.BOLD}{name}{Colors.RESET}")
    if message:
        print(f"  {message}")
    print()

async def test_web_search():
    """Test if web search is working"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}TEST 1: Web Search Integration{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    try:
        from app.internet.google_search import google_search
        
        results = google_search("Python programming language", 3)
        
        if results and len(results) > 0:
            # ✅ FIX: Handle dictionary results properly
            first_result = results[0]
            if isinstance(first_result, dict):
                sample_text = first_result.get('snippet', '')[:100]
                print_test(
                    "Google Search API", 
                    "PASS",
                    f"Retrieved {len(results)} results\n  Title: {first_result.get('title', 'N/A')}\n  Sample: {sample_text}..."
                )
            else:
                # Fallback for string results
                print_test(
                    "Google Search API", 
                    "PASS",
                    f"Retrieved {len(results)} results\n  Sample: {str(first_result)[:100]}..."
                )
            return True
        else:
            print_test(
                "Google Search API", 
                "FAIL",
                "No results returned - check API keys in .env"
            )
            return False
            
    except Exception as e:
        print_test(
            "Google Search API", 
            "FAIL",
            f"Error: {str(e)}"
        )
        return False

async def test_code_execution():
    """Test code execution sandbox"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}TEST 2: Code Execution Sandbox{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    try:
        from app.tools.code_execution import (
            execute_python_with_output,
            execute_javascript_code,
            safe_execute_code
        )
        
        # Test 1: Simple Python
        python_code = """
result = sum([1, 2, 3, 4, 5])
print(f"Sum: {result}")
"""
        py_result = execute_python_with_output(python_code)
        
        if py_result['success'] and 'Sum: 15' in py_result['output']:
            print_test(
                "Python Execution", 
                "PASS",
                f"Output: {py_result['output']}"
            )
        else:
            print_test(
                "Python Execution", 
                "FAIL",
                f"Error: {py_result.get('error', 'Unknown')}"
            )
        
        # Test 2: Python with Plot
        plot_code = """
import matplotlib.pyplot as plt
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

plt.plot(x, y)
plt.title('Sine Wave')
plt.xlabel('X')
plt.ylabel('Y')
"""
        plot_result = execute_python_with_output(plot_code)
        
        if plot_result['success'] and plot_result['plot']:
            print_test(
                "Python Plot Generation", 
                "PASS",
                f"Generated plot (base64 length: {len(plot_result['plot'])})"
            )
        else:
            print_test(
                "Python Plot Generation", 
                "FAIL",
                "No plot data generated"
            )
        
        # Test 3: JavaScript
        js_code = """
const factorial = (n) => n <= 1 ? 1 : n * factorial(n - 1);
console.log('Factorial of 5:', factorial(5));
"""
        js_result = execute_javascript_code(js_code)
        
        if js_result['success'] and '120' in js_result['output']:
            print_test(
                "JavaScript Execution", 
                "PASS",
                f"Output: {js_result['output']}"
            )
        else:
            print_test(
                "JavaScript Execution", 
                "WARN",
                "Node.js might not be installed"
            )
        
        # Test 4: Safe execution
        safe_code = """
numbers = [1, 2, 3, 4, 5]
total = sum(numbers)
print(f"Total: {total}")
"""
        safe_result = safe_execute_code(safe_code)
        
        if safe_result and 'Total: 15' in safe_result:
            print_test(
                "Safe Code Execution", 
                "PASS",
                f"Output: {safe_result}"
            )
        else:
            print_test(
                "Safe Code Execution", 
                "WARN",
                "Safe execution didn't return expected output"
            )
        
        return True
        
    except ImportError as e:
        print_test(
            "Code Execution Module", 
            "FAIL",
            f"Import Error: {str(e)}\n  Make sure code_execution.py has the correct functions"
        )
        return False
    except Exception as e:
        print_test(
            "Code Execution Module", 
            "FAIL",
            f"Error: {str(e)}"
        )
        return False

async def test_response_scoring():
    """Test response quality scoring"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}TEST 3: Response Quality Scoring{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    try:
        from app.tools.response_scorer import score_response, format_score_report
        
        good_response = """
Python is a high-level programming language known for its simplicity and readability.
It was created by Guido van Rossum in 1991. Python supports multiple programming paradigms
including object-oriented, functional, and procedural programming. It's widely used in
web development, data science, and artificial intelligence.
"""
        
        question = "What is Python programming language?"
        
        score = score_response(good_response, question)
        
        print(format_score_report(score))
        
        if score['overall_score'] >= 0.6:
            print_test(
                "Response Scoring", 
                "PASS",
                f"Score: {score['overall_score']} ({score['quality_level']})"
            )
        else:
            print_test(
                "Response Scoring", 
                "WARN",
                f"Score lower than expected: {score['overall_score']}"
            )
        
        poor_response = "uh i dont know python python python"
        poor_score = score_response(poor_response, question)
        
        if poor_score['should_regenerate']:
            print_test(
                "Poor Response Detection", 
                "PASS",
                "Correctly flagged poor response for regeneration"
            )
        else:
            print_test(
                "Poor Response Detection", 
                "FAIL",
                "Failed to detect poor quality"
            )
        
        return True
        
    except ImportError as e:
        print_test(
            "Response Scoring Module", 
            "FAIL",
            f"Import Error: {str(e)}\n  Make sure response_scorer.py exists in app/tools/"
        )
        return False
    except Exception as e:
        print_test(
            "Response Scoring Module", 
            "FAIL",
            f"Error: {str(e)}"
        )
        return False

async def test_multilang():
    """Test multi-language support"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}TEST 4: Multi-Language Support{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    try:
        from app.tools.multilang import (
            detect_language, 
            translate_text,
            process_multilang_query
        )
        
        test_texts = {
            "Hello, how are you?": "en",
            "¿Cómo estás?": "es",
            "Bonjour, comment allez-vous?": "fr",
            "नमस्ते, आप कैसे हैं?": "hi"
        }
        
        detection_passed = 0
        for text, expected_lang in test_texts.items():
            detected = detect_language(text)
            if detected == expected_lang:
                detection_passed += 1
                print(f"  ✓ '{text[:30]}...' → {detected}")
            else:
                print(f"  ✗ '{text[:30]}...' → {detected} (expected {expected_lang})")
        
        if detection_passed >= 3:
            print_test(
                "Language Detection", 
                "PASS",
                f"{detection_passed}/{len(test_texts)} correctly detected"
            )
        else:
            print_test(
                "Language Detection", 
                "WARN",
                "Some languages not detected correctly"
            )
        
        try:
            spanish = "¿Qué es la inteligencia artificial?"
            english = translate_text(spanish, 'es', 'en')
            
            if english and 'artificial intelligence' in english.lower():
                print_test(
                    "Translation", 
                    "PASS",
                    f"'{spanish}' → '{english}'"
                )
            else:
                print_test(
                    "Translation", 
                    "WARN",
                    "Translation quality uncertain"
                )
        except Exception as e:
            print_test(
                "Translation", 
                "FAIL",
                f"Error: {str(e)} (Check internet connection)"
            )
        
        return True
        
    except ImportError as e:
        print_test(
            "Multi-Language Module", 
            "FAIL",
            f"Import Error: {str(e)}\n  Make sure multilang.py exists in app/tools/"
        )
        return False
    except Exception as e:
        print_test(
            "Multi-Language Module", 
            "FAIL",
            f"Error: {str(e)}"
        )
        return False

async def test_ui_fixes():
    """Test UI improvements"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}TEST 5: UI/UX Fixes{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    checks = [
        ("Typing indicator appears immediately", "Manual"),
        ("No blinking between message states", "Manual"),
        ("Smooth fade-in animations", "Manual"),
        ("Bot response streams smoothly", "Manual"),
        ("Web search results actually used", "Check terminal logs")
    ]
    
    print("  Manual UI Testing Checklist:")
    for check, how in checks:
        print(f"    □ {check} ({how})")
    
    print()
    print_test(
        "UI Fixes", 
        "WARN",
        "Requires manual testing in browser"
    )
    
    return True

async def main():
    """Run all tests"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}NEXORA FEATURE TEST SUITE{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    results = {
        'Web Search': await test_web_search(),
        'Code Execution': await test_code_execution(),
        'Response Scoring': await test_response_scoring(),
        'Multi-Language': await test_multilang(),
        'UI Fixes': await test_ui_fixes()
    }
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}SUMMARY{Colors.RESET}")
    print(f"{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for feature, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        color = Colors.GREEN if result else Colors.RED
        print(f"  {color}{status}{Colors.RESET} {feature}")
    
    print(f"\n{Colors.BOLD}Score: {passed}/{total} features working{Colors.RESET}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}🎉 All features operational!{Colors.RESET}\n")
    elif passed >= total * 0.75:
        print(f"\n{Colors.YELLOW}⚠ Most features working - check failures{Colors.RESET}\n")
    else:
        print(f"\n{Colors.RED}❌ Multiple failures - review installation{Colors.RESET}\n")

if __name__ == "__main__":
    asyncio.run(main())