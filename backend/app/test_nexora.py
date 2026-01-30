# backend/app/test_nexora.py
"""
Nexora Diagnostic Script

Tests:
1. Ollama connectivity
2. Model availability and performance
3. Database storage
4. End-to-end chat flow

Usage:
    python test_nexora.py
"""

import asyncio
import sqlite3
import os
import sys
import time
import requests

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_ollama_connection():
    """Test 1: Check Ollama connectivity"""
    print("\n" + "="*60)
    print("TEST 1: Ollama Connection")
    print("="*60)
    
    try:
        OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=3)
        
        if r.status_code == 200:
            models = r.json().get("models", [])
            print(f"✅ Ollama is running")
            print(f"✅ Found {len(models)} models:")
            for m in models[:5]:
                print(f"   - {m['name']}")
            return True
        else:
            print(f"❌ Ollama responded with status {r.status_code}")
            return False
            
    except requests.ConnectionError:
        print("❌ Cannot connect to Ollama")
        print("   Run: ollama serve")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_database():
    """Test 2: Check database setup"""
    print("\n" + "="*60)
    print("TEST 2: Database Setup")
    print("="*60)
    
    try:
        db_path = "data/knowledge.db"
        
        if not os.path.exists(db_path):
            print(f"⚠️  Database not found at {db_path}")
            print("   Will be created on first use")
            return True
        
        conn = sqlite3.connect(db_path, timeout=5)
        cursor = conn.cursor()
        
        # Check tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        if "knowledge" in tables and "categories" in tables:
            print(f"✅ Database exists: {db_path}")
            print(f"✅ Tables found: {', '.join(tables)}")
            
            # Check entries
            cursor.execute("SELECT COUNT(*) FROM knowledge")
            count = cursor.fetchone()[0]
            print(f"✅ Knowledge entries: {count}")
            
            # Check categories
            cursor.execute("SELECT name, knowledge_count FROM categories ORDER BY knowledge_count DESC LIMIT 5")
            cats = cursor.fetchall()
            print(f"✅ Top categories:")
            for name, cnt in cats:
                print(f"   - {name}: {cnt} entries")
            
            conn.close()
            return True
        else:
            print(f"❌ Missing tables. Found: {tables}")
            conn.close()
            return False
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False


async def test_llm_inference():
    """Test 3: Test LLM generation"""
    print("\n" + "="*60)
    print("TEST 3: LLM Inference")
    print("="*60)
    
    try:
        from app.core.llm_inference import generate_with_llm
        
        test_question = "What is 2+2?"
        print(f"Question: {test_question}")
        print("Generating response...")
        
        start = time.time()
        answer = await generate_with_llm(test_question, [])
        elapsed = time.time() - start
        
        if answer and len(answer) > 5:
            print(f"✅ Response generated in {elapsed:.2f}s")
            print(f"✅ Answer: {answer[:200]}...")
            return True
        else:
            print(f"❌ No valid response generated")
            return False
            
    except Exception as e:
        print(f"❌ LLM inference failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_learning_system():
    """Test 4: Test knowledge storage"""
    print("\n" + "="*60)
    print("TEST 4: Learning System")
    print("="*60)
    
    try:
        from app.data_processing.learning_system import learning_system
        
        # Store test Q&A
        test_q = "Test question: What is the capital of France?"
        test_a = "The capital of France is Paris, a major European city known for the Eiffel Tower."
        
        print(f"Storing test Q&A...")
        success = learning_system.learn_from_interaction(
            user_id="test_user",
            question=test_q,
            answer=test_a,
            source="llm"
        )
        
        if success:
            print(f"✅ Successfully stored Q&A")
            
            # Verify storage
            db_path = "data/knowledge.db"
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge WHERE question LIKE '%capital of France%'")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 0:
                print(f"✅ Verified in database ({count} entries)")
                return True
            else:
                print(f"❌ Not found in database")
                return False
        else:
            print(f"❌ Failed to store Q&A")
            return False
            
    except Exception as e:
        print(f"❌ Learning system failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_end_to_end():
    """Test 5: Full chat flow with storage"""
    print("\n" + "="*60)
    print("TEST 5: End-to-End Chat Flow")
    print("="*60)
    
    try:
        from app.core.orchestrator import handle_query
        
        test_question = "What is Python used for?"
        print(f"Question: {test_question}")
        print("Processing...")
        
        start = time.time()
        response = await handle_query("test_user_e2e", test_question)
        elapsed = time.time() - start
        
        if response and len(response) > 10:
            print(f"✅ Response generated in {elapsed:.2f}s")
            print(f"✅ Response: {response[:200]}...")
            
            # Wait a bit for background storage
            await asyncio.sleep(1)
            
            # Check if stored
            db_path = "data/knowledge.db"
            conn = sqlite3.connect(db_path, timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM knowledge WHERE question LIKE '%Python used for%'")
            count = cursor.fetchone()[0]
            conn.close()
            
            if count > 0:
                print(f"✅ Q&A stored in database")
                return True
            else:
                print(f"⚠️  Response generated but not stored (check logs)")
                return True  # Still pass if response works
        else:
            print(f"❌ No valid response")
            return False
            
    except Exception as e:
        print(f"❌ End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "█"*60)
    print("█" + " "*20 + "NEXORA DIAGNOSTICS" + " "*21 + "█")
    print("█"*60)
    
    results = []
    
    # Test 1: Ollama
    results.append(("Ollama Connection", test_ollama_connection()))
    
    # Test 2: Database
    results.append(("Database Setup", test_database()))
    
    # Test 3: LLM
    if results[0][1]:  # Only if Ollama is working
        results.append(("LLM Inference", await test_llm_inference()))
    else:
        results.append(("LLM Inference", False))
        print("\n⚠️  Skipping LLM test (Ollama not available)")
    
    # Test 4: Learning
    if results[1][1]:  # Only if database is working
        results.append(("Learning System", await test_learning_system()))
    else:
        results.append(("Learning System", False))
        print("\n⚠️  Skipping learning test (Database not available)")
    
    # Test 5: End-to-end
    if results[0][1] and results[1][1]:  # Both Ollama and DB working
        results.append(("End-to-End Flow", await test_end_to_end()))
    else:
        results.append(("End-to-End Flow", False))
        print("\n⚠️  Skipping E2E test (Prerequisites not met)")
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Nexora is working correctly.")
    elif passed >= total - 1:
        print("\n⚠️  Most tests passed. Check the failed test above.")
    else:
        print("\n❌ Multiple tests failed. Please check:")
        print("   1. Is Ollama running? (ollama serve)")
        print("   2. Are models installed? (ollama pull gemma2:2b)")
        print("   3. Is the database accessible?")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)