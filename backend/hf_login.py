"""
HuggingFace Login Helper for SAM-3
Programmatically login with token
"""

from huggingface_hub import login
import os

def setup_huggingface_auth():
    """
    Setup HuggingFace authentication for SAM-3 access
    """
    print("🔐 HuggingFace Authentication Setup")
    print("=" * 50)
    print()
    print("Get your token from: https://huggingface.co/settings/tokens")
    print()
    print("Steps:")
    print("1. Click 'Create new token'")
    print("2. Name: SAM3-Project")
    print("3. Type: Read")
    print("4. Copy the token")
    print()
    
    # Option 1: Environment variable
    hf_token = os.getenv("HF_TOKEN")
    
    if hf_token:
        print("✅ Found HF_TOKEN in environment")
        try:
            login(token=hf_token)
            print("✅ Logged in successfully!")
            return True
        except Exception as e:
            print(f"❌ Login failed: {e}")
            return False
    
    # Option 2: Interactive input
    print("Enter your HuggingFace token:")
    token = input("> ").strip()
    
    if not token:
        print("❌ No token provided")
        return False
    
    try:
        login(token=token)
        print("✅ Logged in successfully!")
        print("🔒 Token saved to ~/.cache/huggingface/token")
        return True
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return False


def test_sam3_access():
    """
    Test if SAM-3 model can be accessed
    """
    print()
    print("🧪 Testing SAM-3 access...")
    
    try:
        from transformers import AutoImageProcessor, AutoModel
        
        print("📥 Loading SAM-3 model (first time: ~2GB download)...")
        processor = AutoImageProcessor.from_pretrained("facebook/sam3")
        model = AutoModel.from_pretrained("facebook/sam3")
        
        print("✅ SAM-3 model loaded successfully!")
        print(f"✅ Model type: {type(model).__name__}")
        return True
        
    except Exception as e:
        print(f"❌ Error accessing SAM-3: {e}")
        return False


if __name__ == "__main__":
    # Login
    if setup_huggingface_auth():
        # Test access
        test_sam3_access()
    else:
        print()
        print("❌ Setup failed. Please try again.")
        print()
        print("Alternative: Set environment variable")
        print("  export HF_TOKEN=your_token_here")
        print("  python hf_login.py")
