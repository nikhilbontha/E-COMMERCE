import requests
import sys
import json
from datetime import datetime

class ElectroMartAPITester:
    def __init__(self, base_url="https://45f387d2-a8b8-4ede-8376-a9f01a081d72.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_user_email = f"test_user_{datetime.now().strftime('%H%M%S')}@test.com"
        self.test_user_password = "TestPass123!"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        test_headers = {'Content-Type': 'application/json'}
        
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and len(str(response_data)) < 500:
                        print(f"   Response: {response_data}")
                    elif isinstance(response_data, list):
                        print(f"   Response: List with {len(response_data)} items")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error: {error_data}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API Endpoint", "GET", "", 200)

    def test_user_registration(self):
        """Test user registration with welcome bonus"""
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data={
                "name": "Test User",
                "email": self.test_user_email,
                "password": self.test_user_password,
                "phone": "9876543210"
            }
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            
            # Check welcome bonus
            if response['user']['loyalty_points'] == 100:
                print("✅ Welcome bonus of 100 points awarded correctly")
            else:
                print(f"❌ Welcome bonus incorrect: {response['user']['loyalty_points']} points")
            
            # Check initial tier
            if response['user']['loyalty_tier'] == 'bronze':
                print("✅ Initial loyalty tier set to Bronze correctly")
            else:
                print(f"❌ Initial loyalty tier incorrect: {response['user']['loyalty_tier']}")
                
            return True
        return False

    def test_user_login(self):
        """Test user login"""
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={
                "email": self.test_user_email,
                "password": self.test_user_password
            }
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response['user']['id']
            return True
        return False

    def test_get_products(self):
        """Test getting all products"""
        success, response = self.run_test("Get Products", "GET", "products", 200)
        
        if success and isinstance(response, list):
            print(f"✅ Found {len(response)} products")
            
            # Check if products have required fields and Indian pricing
            for product in response[:2]:  # Check first 2 products
                required_fields = ['id', 'name', 'price', 'brand', 'category', 'image_url']
                missing_fields = [field for field in required_fields if field not in product]
                
                if missing_fields:
                    print(f"❌ Product missing fields: {missing_fields}")
                else:
                    print(f"✅ Product '{product['name']}' has all required fields")
                    print(f"   Price: ₹{product['price']} (Brand: {product['brand']})")
            
            return True
        return False

    def test_get_categories(self):
        """Test getting all categories"""
        success, response = self.run_test("Get Categories", "GET", "categories", 200)
        
        if success and isinstance(response, list):
            print(f"✅ Found {len(response)} categories")
            
            expected_categories = ["Smartphones", "Headphones", "Smartwatches", "Chargers & Power Banks"]
            found_categories = [cat['name'] for cat in response]
            
            for expected in expected_categories:
                if expected in found_categories:
                    print(f"✅ Category '{expected}' found")
                else:
                    print(f"❌ Category '{expected}' missing")
            
            return True
        return False

    def test_loyalty_status(self):
        """Test loyalty status endpoint (requires authentication)"""
        if not self.token:
            print("❌ No token available for loyalty status test")
            return False
            
        success, response = self.run_test("Loyalty Status", "GET", "loyalty/status", 200)
        
        if success:
            required_fields = ['points', 'tier', 'total_spent', 'benefits']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                print(f"❌ Loyalty status missing fields: {missing_fields}")
                return False
            else:
                print(f"✅ Loyalty status complete:")
                print(f"   Points: {response['points']}")
                print(f"   Tier: {response['tier']}")
                print(f"   Total Spent: ₹{response['total_spent']}")
                
                # Check if benefits structure is correct
                benefits = response['benefits']
                expected_tiers = ['bronze', 'silver', 'gold', 'platinum']
                
                for tier in expected_tiers:
                    if tier in benefits:
                        print(f"✅ {tier.capitalize()} tier benefits available")
                    else:
                        print(f"❌ {tier.capitalize()} tier benefits missing")
                
                return True
        return False

    def test_get_orders(self):
        """Test getting user orders (requires authentication)"""
        if not self.token:
            print("❌ No token available for orders test")
            return False
            
        success, response = self.run_test("Get User Orders", "GET", "orders", 200)
        
        if success:
            if isinstance(response, list):
                print(f"✅ Orders endpoint working - {len(response)} orders found")
                return True
            else:
                print("❌ Orders response is not a list")
                return False
        return False

    def test_recommendations(self):
        """Test recommendations endpoint (requires authentication)"""
        if not self.token:
            print("❌ No token available for recommendations test")
            return False
            
        success, response = self.run_test("Get Recommendations", "GET", "recommendations", 200)
        
        if success and isinstance(response, list):
            print(f"✅ Recommendations working - {len(response)} products recommended")
            return True
        return False

    def test_invalid_auth(self):
        """Test endpoints with invalid authentication"""
        # Save current token
        original_token = self.token
        self.token = "invalid_token_123"
        
        success, _ = self.run_test("Invalid Auth Test", "GET", "loyalty/status", 401)
        
        # Restore original token
        self.token = original_token
        return success

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting ElectroMart API Tests")
        print("=" * 50)
        
        # Test basic endpoints
        self.test_root_endpoint()
        self.test_get_products()
        self.test_get_categories()
        
        # Test authentication
        if self.test_user_registration():
            print("\n📝 Registration successful, testing authenticated endpoints...")
            self.test_loyalty_status()
            self.test_get_orders()
            self.test_recommendations()
            
            # Test login with same user
            print("\n🔐 Testing login with registered user...")
            self.test_user_login()
        
        # Test invalid authentication
        self.test_invalid_auth()
        
        # Print final results
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed! Backend API is working correctly.")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed. Please check the issues above.")
            return 1

def main():
    tester = ElectroMartAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())