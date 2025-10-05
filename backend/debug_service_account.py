#!/usr/bin/env python3
"""
Debug script to extract project ID from service account JSON
"""

import json
import os
from dotenv import load_dotenv

load_dotenv()

def debug_service_account():
    """Extract project ID from service account file"""
    service_account_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_KEY_PATH')
    print(f"🔍 Service account path from env: {service_account_path}")
    
    if service_account_path:
        # Handle relative paths
        if not os.path.isabs(service_account_path):
            if service_account_path.startswith('backend/'):
                service_account_path = service_account_path[8:]  # Remove 'backend/'
            service_account_path = os.path.join(os.path.dirname(__file__), service_account_path)
            service_account_path = os.path.abspath(service_account_path)
        
        print(f"🔍 Looking for file at: {service_account_path}")
        print(f"🔍 File exists: {os.path.exists(service_account_path)}")
        
        if os.path.exists(service_account_path):
            try:
                with open(service_account_path, 'r') as f:
                    service_account_info = json.load(f)
                
                project_id = service_account_info.get('project_id')
                client_email = service_account_info.get('client_email')
                
                print(f"✅ Service account file loaded successfully!")
                print(f"📧 Client email: {client_email}")
                print(f"🆔 Project ID: {project_id}")
                
                return project_id
                
            except Exception as e:
                print(f"❌ Error reading service account file: {e}")
        else:
            print("❌ Service account file not found!")
            print("💡 Make sure the file path in .env is correct")
    else:
        print("❌ GOOGLE_SERVICE_ACCOUNT_KEY_PATH not set in .env")
    
    return None

if __name__ == "__main__":
    print("🔍 BloomWatch Service Account Debug")
    print("=" * 40)
    project_id = debug_service_account()
    
    if project_id:
        print(f"\n✅ Use this project ID in your .env:")
        print(f"GOOGLE_CLOUD_PROJECT={project_id}")
    else:
        print(f"\n❌ Could not extract project ID")
        print("💡 Check your service account file path and contents")
