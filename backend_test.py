#!/usr/bin/env python3
"""
Plant Health Scanner Backend API Tests
Tests the complete backend API functionality including:
1. GET /api/ - Welcome endpoint
2. POST /api/analyze-plant - Plant analysis with OpenAI GPT-5.2 
3. GET /api/scan-history - Scan history retrieval
"""

import requests
import base64
import json
import sys
from PIL import Image
from io import BytesIO
import os

# Backend URL from environment
BACKEND_URL = "https://green-health-shop.preview.emergentagent.com/api"

def create_test_plant_image():
    """Create a simple test plant image for API testing"""
    # Create a 300x300 green image that represents a leaf
    img = Image.new('RGB', (300, 300), color='white')
    pixels = img.load()
    
    # Create a simple leaf-like pattern with green colors
    for x in range(300):
        for y in range(300):
            # Create a gradient effect to simulate a leaf
            center_x, center_y = 150, 150
            dist = ((x - center_x) ** 2 + (y - center_y) ** 2) ** 0.5
            
            if dist < 120:  # Leaf area
                green_intensity = max(50, min(255, int(255 - dist * 1.5)))
                if 100 < x < 200 and 50 < y < 250:  # Main leaf body
                    pixels[x, y] = (30, green_intensity, 50)
                elif 140 < x < 160:  # Leaf vein
                    pixels[x, y] = (20, int(green_intensity * 0.7), 30)
                else:
                    pixels[x, y] = (40, int(green_intensity * 0.9), 60)
    
    # Convert to base64
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    img_bytes = buffer.getvalue()
    return base64.b64encode(img_bytes).decode('utf-8')

def test_welcome_endpoint():
    """Test GET /api/ endpoint"""
    print("Testing GET /api/ - Welcome endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "Plant Health Scanner" in data["message"]:
                print("✅ Welcome endpoint working correctly")
                return True
            else:
                print("❌ Welcome endpoint returned unexpected message")
                return False
        else:
            print(f"❌ Welcome endpoint failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing welcome endpoint: {str(e)}")
        return False

def test_analyze_plant_endpoint():
    """Test POST /api/analyze-plant endpoint"""
    print("\nTesting POST /api/analyze-plant - Plant analysis endpoint...")
    
    try:
        # Create test plant image
        plant_image_base64 = create_test_plant_image()
        
        # Prepare request
        payload = {
            "image_base64": plant_image_base64
        }
        
        headers = {
            "Content-Type": "application/json"
        }
        
        print("Sending plant analysis request...")
        response = requests.post(f"{BACKEND_URL}/analyze-plant", 
                               json=payload, 
                               headers=headers,
                               timeout=60)  # Longer timeout for LLM processing
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response keys: {list(data.keys())}")
            
            # Check required fields
            required_fields = ["id", "health_status", "issues", "remedies", 
                             "detailed_analysis", "image_base64", "timestamp"]
            
            missing_fields = []
            for field in required_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            # Validate field types and contents
            print(f"Health Status: {data['health_status']}")
            print(f"Issues Count: {len(data['issues'])}")
            print(f"Remedies Count: {len(data['remedies'])}")
            print(f"Analysis Length: {len(data['detailed_analysis'])} characters")
            
            # Check if OpenAI integration is working
            if data['health_status'] != "Unknown" or len(data['detailed_analysis']) > 50:
                print("✅ Plant analysis endpoint working with OpenAI integration")
                return True
            else:
                print("⚠️ Plant analysis endpoint responding but OpenAI integration may not be working properly")
                print(f"Detailed analysis: {data['detailed_analysis'][:200]}...")
                return False
                
        else:
            print(f"❌ Plant analysis failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Response text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing plant analysis endpoint: {str(e)}")
        return False

def test_scan_history_endpoint():
    """Test GET /api/scan-history endpoint"""
    print("\nTesting GET /api/scan-history - Scan history endpoint...")
    
    try:
        response = requests.get(f"{BACKEND_URL}/scan-history")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Scan history count: {len(data)}")
            
            if len(data) > 0:
                # Check first scan structure
                first_scan = data[0]
                required_fields = ["id", "health_status", "issues", "remedies", 
                                 "detailed_analysis", "image_base64", "timestamp"]
                
                missing_fields = []
                for field in required_fields:
                    if field not in first_scan:
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"❌ Scan history items missing fields: {missing_fields}")
                    return False
                
                print("✅ Scan history endpoint working correctly")
                return True
            else:
                print("✅ Scan history endpoint working (no scans yet)")
                return True
                
        else:
            print(f"❌ Scan history failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"Error details: {error_detail}")
            except:
                print(f"Response text: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing scan history endpoint: {str(e)}")
        return False

def test_invalid_requests():
    """Test error handling with invalid requests"""
    print("\nTesting error handling...")
    
    # Test empty image
    try:
        payload = {"image_base64": ""}
        response = requests.post(f"{BACKEND_URL}/analyze-plant", json=payload)
        if response.status_code == 400:
            print("✅ Proper error handling for empty image")
        else:
            print(f"⚠️ Unexpected status for empty image: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Error testing empty image: {str(e)}")
    
    # Test invalid base64
    try:
        payload = {"image_base64": "invalid_base64_data"}
        response = requests.post(f"{BACKEND_URL}/analyze-plant", json=payload)
        if response.status_code in [400, 500]:
            print("✅ Proper error handling for invalid base64")
        else:
            print(f"⚠️ Unexpected status for invalid base64: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Error testing invalid base64: {str(e)}")

def run_all_tests():
    """Run all backend tests"""
    print("=" * 60)
    print("PLANT HEALTH SCANNER BACKEND API TESTS")
    print("=" * 60)
    print(f"Backend URL: {BACKEND_URL}")
    print("")
    
    results = {
        "welcome_endpoint": False,
        "analyze_plant_endpoint": False, 
        "scan_history_endpoint": False
    }
    
    # Test all endpoints
    results["welcome_endpoint"] = test_welcome_endpoint()
    results["analyze_plant_endpoint"] = test_analyze_plant_endpoint()  
    results["scan_history_endpoint"] = test_scan_history_endpoint()
    
    # Test error handling
    test_invalid_requests()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(results.values())
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Backend API is working correctly!")
        return True
    else:
        print("⚠️ SOME TESTS FAILED - Check logs above for details")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)