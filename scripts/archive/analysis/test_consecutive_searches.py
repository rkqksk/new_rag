import subprocess
import json
import time

def create_session():
    """Create a new session"""
    url = "http://localhost:8001/chat/create_session"
    cmd = ["curl", "-s", "-X", "POST", url, "-H", "Content-Type: application/json", "-d", "{}"]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        response = json.loads(result.stdout)
        session_id = response.get('session_id')
        print(f"✓ Session created: {session_id}")
        return session_id
    else:
        print(f"✗ Failed to create session: {result.stderr}")
        return None

def test_search(session_id, query, search_num):
    """Test a single search query with session"""
    print(f"\n{'='*80}")
    print(f"Search #{search_num}: '{query}'")
    print('='*80)
    
    url = "http://localhost:8001/chat/query"
    payload = {
        "session_id": session_id,
        "query": query
    }
    
    cmd = [
        "curl", "-s", "-X", "POST",
        url,
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]
    
    print(f"Payload: {json.dumps(payload, ensure_ascii=False)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            try:
                response = json.loads(result.stdout)
                print(f"\n✓ Response received:")
                
                if 'products' in response:
                    products = response['products']
                    print(f"  Products count: {len(products)}")
                    
                    if len(products) > 0:
                        print(f"  ✓ PRODUCTS FOUND!")
                        print(f"  First product: {products[0].get('product_name', 'N/A')}")
                        print(f"    - Code: {products[0].get('product_code', 'N/A')}")
                        print(f"    - Score: {products[0].get('recommendation_score', 0):.2f}")
                    else:
                        print(f"  ✗ EMPTY PRODUCTS ARRAY!")
                else:
                    print(f"  ⚠ No 'products' field in response")
                        
                if 'response' in response:
                    print(f"  Assistant message: {response['response'][:100]}...")
                    
                if 'matched_profile' in response:
                    print(f"  Matched profile: {response['matched_profile']}")
                
                if 'detail' in response:
                    print(f"  ✗ ERROR: {response['detail']}")
                
                return response
                
            except json.JSONDecodeError as e:
                print(f"  ✗ Failed to parse JSON response: {e}")
                print(f"  Raw output: {result.stdout[:500]}")
                return None
        else:
            print(f"  ✗ Request failed with return code: {result.returncode}")
            print(f"  Error: {result.stderr}")
            return None
            
    except subprocess.TimeoutExpired:
        print(f"  ✗ Request timed out after 30 seconds")
        return None
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        return None

# Main test
print("="*80)
print("CONSECUTIVE SEARCH TEST WITH SESSION")
print("="*80)

# Create session
session_id = create_session()
if not session_id:
    print("Cannot continue without session")
    exit(1)

print(f"\n✓ Using session: {session_id}\n")

# Perform 3 consecutive searches
searches = [
    "50미리 용기",
    "토너", 
    "세럼"
]

results = []
for i, query in enumerate(searches, 1):
    result = test_search(session_id, query, i)
    results.append({
        'search_num': i,
        'query': query,
        'response': result,
        'has_products': result and isinstance(result.get('products'), list) and len(result.get('products', [])) > 0 if result else False,
        'product_count': len(result.get('products', [])) if result and isinstance(result.get('products'), list) else 0
    })
    
    if i < len(searches):
        print(f"\n⏳ Waiting 2 seconds before next search...")
        time.sleep(2)

# Summary
print("\n" + "="*80)
print("TEST SUMMARY")
print("="*80)
print(f"Session ID: {session_id}\n")

for r in results:
    status = "✓ Products found" if r['has_products'] else "✗ NO PRODUCTS"
    print(f"Search {r['search_num']} ('{r['query']}'): {status} ({r['product_count']} products)")

# Diagnosis
first_search_ok = results[0]['has_products']
second_search_ok = results[1]['has_products']
third_search_ok = results[2]['has_products']

print("\n" + "="*80)
print("DIAGNOSIS")
print("="*80)
if first_search_ok and not second_search_ok:
    print("🚨 BUG CONFIRMED: First search works, second search fails!")
    print("   This is the reported issue: consecutive searches don't show products.")
    print("\n   Possible causes:")
    print("   1. Session state not cleared between queries")
    print("   2. Product list not being reset on frontend")
    print("   3. Cache issue with duplicate session queries")
    print("   4. displayProducts() function not being called")
elif all(r['has_products'] for r in results):
    print("✅ All searches returned products - API working correctly!")
    print("   If products don't show in browser, issue is in frontend JavaScript.")
    print("\n   Check:")
    print("   1. displayProducts() function is being called")
    print("   2. DOM manipulation is working")
    print("   3. Console logs in browser")
elif not any(r['has_products'] for r in results):
    print("❌ No searches returned products")
    print("   This is a backend/database issue, not frontend.")
else:
    print(f"⚠️  Mixed results: {sum(r['has_products'] for r in results)}/3 searches successful")

print("\n💾 Saving detailed results to /tmp/api_test_with_session.json")
with open('/tmp/api_test_with_session.json', 'w', encoding='utf-8') as f:
    json.dump({
        'session_id': session_id,
        'results': results
    }, f, indent=2, ensure_ascii=False)
print("✓ Results saved")
