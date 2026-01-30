# backend/test_rag_detailed.py
"""
Detailed RAG Testing - Verify document retrieval works
"""

import asyncio
from app.core.rag import create_collection, query_collection, delete_collection, get_collection_info

async def test_rag_comprehensive():
    print("\n" + "="*70)
    print("COMPREHENSIVE RAG TEST")
    print("="*70)
    
    # Sample documents with clear, testable content
    sample_files = [
        {
            "filename": "ml_basics.txt",
            "content": b"""Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that focuses on algorithms 
that can learn from data and make predictions without being explicitly programmed.

Deep learning is a specialized type of machine learning that uses neural networks 
with multiple layers to process complex patterns in data.

Common applications of machine learning include:
- Image recognition and computer vision
- Natural language processing and text analysis
- Recommendation systems
- Fraud detection
- Autonomous vehicles"""
        },
        {
            "filename": "python_frameworks.txt",
            "content": b"""Python Machine Learning Frameworks

TensorFlow is an open-source machine learning framework developed by Google.
It is widely used for deep learning applications and neural network training.

PyTorch is another popular deep learning framework developed by Facebook.
It is known for its dynamic computation graphs and ease of use.

Scikit-learn is a traditional machine learning library that provides
simple and efficient tools for data analysis and modeling.

Data preprocessing is a crucial step in the machine learning pipeline.
It involves cleaning, transforming, and preparing raw data for model training.

Training machine learning models requires:
1. Large datasets with quality labeled examples
2. Sufficient computational resources (CPU/GPU)
3. Proper validation and testing procedures"""
        }
    ]
    
    collection_id = None
    
    try:
        # Step 1: Create collection
        print("\n📦 STEP 1: Creating collection...")
        print("-" * 70)
        collection_id = create_collection(sample_files)
        print(f"✅ Collection created: {collection_id}")
        
        # Get collection info
        info = get_collection_info(collection_id)
        print(f"📊 Collection info: {info}")
        
        # Step 2: Test various queries
        print("\n🔍 STEP 2: Testing queries...")
        print("-" * 70)
        
        test_queries = [
            {
                "question": "What is machine learning?",
                "expected_keywords": ["machine learning", "artificial intelligence", "algorithms", "data"],
                "description": "Definition query"
            },
            {
                "question": "Which frameworks are mentioned?",
                "expected_keywords": ["TensorFlow", "PyTorch", "Scikit-learn"],
                "description": "Specific information query"
            },
            {
                "question": "What is required for training?",
                "expected_keywords": ["datasets", "computational", "validation"],
                "description": "List/enumeration query"
            },
            {
                "question": "Tell me about deep learning",
                "expected_keywords": ["deep learning", "neural networks", "layers"],
                "description": "Conceptual query"
            }
        ]
        
        passed = 0
        failed = 0
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n  Query {i}: {test_case['description']}")
            print(f"  Question: \"{test_case['question']}\"")
            
            results = query_collection(collection_id, test_case['question'], k=5)
            
            if results:
                print(f"  ✅ Found {len(results)} results")
                
                # Check if expected keywords appear in results
                all_content = " ".join([r['content'].lower() for r in results])
                
                found_keywords = []
                missing_keywords = []
                
                for keyword in test_case['expected_keywords']:
                    if keyword.lower() in all_content:
                        found_keywords.append(keyword)
                    else:
                        missing_keywords.append(keyword)
                
                if found_keywords:
                    print(f"  ✅ Found keywords: {', '.join(found_keywords)}")
                
                if missing_keywords:
                    print(f"  ⚠️  Missing keywords: {', '.join(missing_keywords)}")
                
                # Show top result
                print(f"\n  Top result (score: {results[0]['score']}):")
                print(f"    Source: {results[0]['source']}")
                print(f"    Content: {results[0]['content'][:150]}...")
                
                # Consider it a pass if we found at least 50% of keywords
                if len(found_keywords) >= len(test_case['expected_keywords']) * 0.5:
                    print(f"  ✅ PASS")
                    passed += 1
                else:
                    print(f"  ❌ FAIL - Too few relevant keywords")
                    failed += 1
            else:
                print(f"  ❌ No results found")
                failed += 1
        
        # Summary
        print("\n" + "="*70)
        print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_queries)} queries")
        print("="*70)
        
        if passed == len(test_queries):
            print("\n🎉 All RAG tests passed!")
            return True
        elif passed >= len(test_queries) * 0.75:
            print("\n⚠️  Most tests passed, but some queries need improvement")
            return True
        else:
            print("\n❌ RAG system needs fixes")
            return False
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup
        if collection_id:
            print(f"\n🧹 Cleaning up collection {collection_id}...")
            delete_collection(collection_id)


if __name__ == "__main__":
    success = asyncio.run(test_rag_comprehensive())
    exit(0 if success else 1)