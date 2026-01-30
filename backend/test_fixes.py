# backend/test_fixes.py
import asyncio
from app.core.llm_inference import generate_chat_response, is_greeting
from app.core.rag import create_collection, query_collection, delete_collection

async def test_greeting_detection():
    """Test that greetings are detected instantly without LLM"""
    print("\n" + "="*60)
    print("TESTING GREETING DETECTION")
    print("="*60)
    
    greetings = [
        "hi",
        "hello",
        "hey there",  # This should now work!
        "hi there",
        "good morning",
        "who are you",
        "what is your name",
        "who made you"
    ]
    
    passed = 0
    failed = 0
    
    for greeting in greetings:
        print(f"\n🧪 Testing: '{greeting}'")
        
        # Check detection
        is_detected = is_greeting(greeting)
        print(f"   Detected as greeting: {is_detected}")
        
        if not is_detected:
            print(f"   ❌ FAIL - Not detected as greeting")
            failed += 1
            continue
        
        # Get response
        import time
        start = time.time()
        response = await generate_chat_response(greeting, user_id="test_user")
        elapsed = time.time() - start
        
        print(f"   Response time: {elapsed:.3f}s")
        print(f"   Response: {response[:100]}...")
        
        # Should be instant (< 0.1s)
        if elapsed < 0.1:
            print("   ✅ PASS - Instant response (no LLM)")
            passed += 1
        else:
            print(f"   ❌ FAIL - Too slow ({elapsed:.2f}s), probably used LLM")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60)


async def test_rag_functionality():
    """Test RAG with sample documents"""
    print("\n" + "="*60)
    print("TESTING RAG FUNCTIONALITY")
    print("="*60)
    
    # Create sample documents
    sample_files = [
        {
            "filename": "document1.txt",
            "content": b"""Machine learning is a subset of artificial intelligence.
It focuses on algorithms that can learn from data and make predictions.
Deep learning uses neural networks with multiple layers.
Common applications include image recognition and natural language processing."""
        },
        {
            "filename": "document2.txt",
            "content": b"""Python is a popular programming language for AI.
TensorFlow and PyTorch are leading deep learning frameworks.
Data preprocessing is crucial for model performance.
Training requires large datasets and computational resources."""
        }
    ]
    
    try:
        # Test 1: Create collection
        print("\n🧪 Test 1: Creating collection...")
        collection_id = create_collection(sample_files)
        print(f"   ✅ Collection created: {collection_id}")
        
        # Test 2: Query collection
        print("\n🧪 Test 2: Querying collection...")
        questions = [
            "What is machine learning?",
            "Which frameworks are mentioned?",
            "What is required for training?"
        ]
        
        for question in questions:
            print(f"\n   Question: {question}")
            results = query_collection(collection_id, question, k=3)
            
            if results:
                print(f"   ✅ Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    print(f"      {i}. Score: {result['score']} | Source: {result['source']}")
                    print(f"         Content: {result['content'][:80]}...")
            else:
                print("   ❌ No results found")
        
        # Test 3: Cleanup
        print("\n🧪 Test 3: Deleting collection...")
        success = delete_collection(collection_id)
        if success:
            print("   ✅ Collection deleted")
        else:
            print("   ❌ Deletion failed")
    
    except Exception as e:
        print(f"   ❌ ERROR: {str(e)}")
    
    print("\n" + "="*60)


async def test_non_greeting_queries():
    """Test that regular questions still work with search"""
    print("\n" + "="*60)
    print("TESTING NON-GREETING QUERIES")
    print("="*60)
    
    queries = [
        "What is the weather today?",
        "Explain quantum computing",
        "Write a Python function to sort a list"
    ]
    
    for query in queries:
        print(f"\n🧪 Testing: '{query}'")
        
        # Should NOT be detected as greeting
        is_detected = is_greeting(query)
        print(f"   Detected as greeting: {is_detected}")
        
        if is_detected:
            print("   ❌ FAIL - Incorrectly detected as greeting")
        else:
            print("   ✅ PASS - Correctly identified as non-greeting")
    
    print("\n" + "="*60)


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("NEXORA FIX VALIDATION TESTS")
    print("="*60)
    
    await test_greeting_detection()
    await test_non_greeting_queries()
    await test_rag_functionality()
    
    print("\n" + "="*60)
    print("ALL TESTS COMPLETE")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())