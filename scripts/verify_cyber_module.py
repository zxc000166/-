
import unittest
from unittest.mock import MagicMock, patch
import json
import os
from src.integrations.cyber_client import CyberIndustrialDesignClient

class TestCyberModule(unittest.TestCase):
    def setUp(self):
        self.client = CyberIndustrialDesignClient(auth_token="test_token")
        
    def test_missing_fields(self):
        """Test validation for missing required fields"""
        with self.assertRaises(ValueError) as cm:
            self.client.generate_design({"project_id": "123"})
        self.assertIn("Missing required fields", str(cm.exception))
        
    def test_invalid_data_type(self):
        """Test validation for invalid data types"""
        with self.assertRaises(ValueError) as cm:
            self.client.generate_design("not a dict")
        self.assertIn("Request data must be a dictionary", str(cm.exception))

    @patch('requests.Session.post')
    def test_api_success(self, mock_post):
        """Test successful API call with real HTTP mocking"""
        # Switch to non-example URL to bypass internal mock
        client = CyberIndustrialDesignClient(api_url="https://api.real-service.com", auth_token="token")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "success", "data": "123"}
        mock_post.return_value = mock_response
        
        result = client.generate_design({
            "project_id": "p1", 
            "style": "s1", 
            "parameters": {}
        })
        
        self.assertEqual(result["status"], "success")
        mock_post.assert_called_once()
        
    @patch('requests.Session.post')
    def test_api_failure(self, mock_post):
        """Test API failure handling"""
        client = CyberIndustrialDesignClient(api_url="https://api.real-service.com", auth_token="token")
        
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        
        with self.assertRaises(Exception): # Expect HTTPError or generic Exception
            client.generate_design({
                "project_id": "p1", 
                "style": "s1", 
                "parameters": {}
            })

if __name__ == "__main__":
    print("========================================")
    print("Starting Cyber Module Verification")
    print("========================================")
    
    # Run Unit Tests
    suite = unittest.TestLoader().loadTestsFromTestCase(TestCyberModule)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    
    if not result.wasSuccessful():
        exit(1)
        
    print("\n----------------------------------------")
    print("Verifying Logs")
    print("----------------------------------------")
    if os.path.exists("cyber_integration.log"):
        with open("cyber_integration.log", "r") as f:
            logs = f.readlines()
            print(f"Log file found with {len(logs)} entries.")
            print("Last 3 logs:")
            for line in logs[-3:]:
                print(line.strip())
    else:
        print("❌ Log file not found!")
        exit(1)
        
    print("\n✅ All Cyber Module checks passed successfully.")
