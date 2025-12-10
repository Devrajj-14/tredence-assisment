#!/usr/bin/env python3
import requests
import sys


def test_api():
    base_url = "http://localhost:8000"
    
    try:
        response = requests.get(f"{base_url}/graphs", timeout=2)
        if response.status_code != 200:
            print("Server not responding, skipping API tests")
            return
            
    except requests.exceptions.RequestException:
        print("Server not running, skipping API tests")
        return
    
    print("Testing API endpoints...")
    
    graphs = response.json()
    if not graphs['graphs']:
        print("No graphs available")
        return
        
    graph_id = graphs['graphs'][0]['graph_id']
    print(f"Found graph: {graph_id}")
    
    test_data = {
        "graph_id": graph_id,
        "input_data": {
            "text": "AI is changing the world. Machine learning helps computers learn. This technology is very powerful.",
            "max_length": 50
        }
    }
    
    response = requests.post(f"{base_url}/graph/run", json=test_data)
    
    if response.status_code == 200:
        result = response.json()
        final_summary = result['final_state']['refined_summary']
        print(f"API test passed!")
        print(f"Generated summary: {final_summary}")
        print(f"Length: {len(final_summary)} chars")
    else:
        print(f"API test failed: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    test_api()