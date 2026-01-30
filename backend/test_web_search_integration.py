"""
Test if web search results are actually being used in responses
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.llm_inference import generate_chat_response
from app.internet.google_search import google_search


async def test_search_integration():
    print("\n" + "="*70)
    print("TESTING WEB SEARCH INTEGRATION")
    print("="*70)
    
    # Test 1: Direct Google Search
    print("\n🔍 TEST 1: Direct Google Search")
    print("-" * 70)
    
    query = "current US president 2025"
    print(f"Query: {query}")
    
    results = google_search(query, max_results=3)
    
    if results:
        print(f"\n✅ Retrieved {len(results)} results:")
        for i, result in enumerate(results, 1):
            if isinstance(result, dict):
                print(f"\n  Result {i}:")
                print(f"    Title: {result.get('title', 'N/A')}")
                print(f"    Link: {result.get('link', 'N/A')}")
                print(f"    Snippet: {result.get('snippet', 'N/A')[:100]}...")
            else:
                print(f"\n  Result {i}: {str(result)[:100]}...")
    else:
        print("❌ No search results returned")
        return False
    
    # Test 2: Chat Response with Web Search
    print("\n\n🤖 TEST 2: Chat Response Using Web Search")
    print("-" * 70)
    
    question = "Who is the current president of the United States in 2025?"
    print(f"Question: {question}")
    print("\nGenerating response with web search enabled...")
    
    response = await generate_chat_response(
        question=question,
        user_id="test_user",
        enable_web_search=True,
        response_style="balanced"
    )
    
    print("\n" + "="*70)
    print("RESPONSE:")
    print("="*70)
    print(response)
    print("="*70)
    
    # Check if response contains current info
    if "Trump" in response or "Donald" in response:
        print("\n✅ PASS: Response contains current information from search")
        return True
    elif "Biden" in response or "Joe" in response:
        print("\n⚠️  WARNING: Response might be using old training data")
        print("   Expected: Trump (2025)")
        print("   Got: Biden (from training data)")
        return False
    else:
        print("\n❌ FAIL: Response doesn't contain expected information")
        print("   Search results might not be reaching the LLM")
        return False


async def test_grounding_gate():
    """Test if the grounding gate is working"""
    print("\n\n" + "="*70)
    print("TESTING GROUNDING GATE")
    print("="*70)
    
    test_cases = [
        {
            "question": "What is the current price of Bitcoin?",
            "should_search": True,
            "description": "Real-time price query"
        },
        {
            "question": "Explain how recursion works in programming",
            "should_search": False,
            "description": "Procedural/educational query"
        },
        {
            "question": "Who is the current CEO of Google?",
            "should_search": True,
            "description": "Current status query"
        }
    ]
    
    from app.core.llm_inference import should_search_web
    
    all_passed = True
    
    for case in test_cases:
        print(f"\n📝 Test: {case['description']}")
        print(f"   Question: {case['question']}")
        
        needs_search, search_query = should_search_web(case['question'])
        
        print(f"   Should search: {needs_search}")
        print(f"   Search query: {search_query if needs_search else 'N/A'}")
        
        if needs_search == case['should_search']:
            print("   ✅ PASS")
        else:
            print(f"   ❌ FAIL - Expected should_search={case['should_search']}")
            all_passed = False
    
    return all_passed


async def test_context_formatting():
    """Test if search results are being formatted correctly for the LLM"""
    print("\n\n" + "="*70)
    print("TESTING CONTEXT FORMATTING")
    print("="*70)
    
    # Simulate what happens in chat_router.py
    from app.internet.google_search import google_search
    
    query = "Python programming language"
    raw_results = google_search(query, max_results=3)
    
    print(f"\n🔍 Raw search results: {len(raw_results)} items")
    
    # This is what chat_router.py should be doing
    contexts = []
    for result in raw_results:
        if isinstance(result, dict):
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            link = result.get('link', '')
            
            formatted = f"**{title}**\n{snippet}\nSource: {link}"
            contexts.append(formatted)
            
            print(f"\n  ✅ Formatted result:")
            print(f"     {formatted[:100]}...")
        else:
            contexts.append(str(result))
            print(f"\n  ⚠️  String result (fallback):")
            print(f"     {str(result)[:100]}...")
    
    if contexts:
        print(f"\n✅ Successfully formatted {len(contexts)} contexts")
        print(f"\nExample combined context:\n")
        print("-" * 70)
        print("\n\n".join(contexts[:2]))
        print("-" * 70)
        return True
    else:
        print("\n❌ No contexts generated")
        return False


async def main():
    print("\n" + "█"*70)
    print("█" + " "*20 + "WEB SEARCH DIAGNOSTICS" + " "*27 + "█")
    print("█"*70)
    
    results = {}
    
    # Test 1: Integration
    results['Search Integration'] = await test_search_integration()
    
    # Test 2: Grounding Gate
    results['Grounding Gate'] = await test_grounding_gate()
    
    # Test 3: Context Formatting
    results['Context Formatting'] = await test_context_formatting()
    
    # Summary
    print("\n\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 Web search is fully integrated and working!")
    else:
        print("\n⚠️  Some tests failed. Debugging tips:")
        print("   1. Check that GOOGLE_API_KEY and GOOGLE_CX are set in .env")
        print("   2. Verify chat_router.py is extracting dict fields correctly")
        print("   3. Check that grounded context is being injected into messages")
        print("   4. Look at terminal logs when asking questions in the UI")


if __name__ == "__main__":
    asyncio.run(main())