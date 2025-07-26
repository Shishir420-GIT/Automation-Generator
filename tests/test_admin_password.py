#!/usr/bin/env python3
"""
Test admin password functionality
"""

def test_password_logic():
    """Test the password logic used in the app"""
    
    # Simulate the password logic from the app
    test_cases = [
        ("vector_admin_2024", "correct"),
        ("wrong_password", "wrong"),
        ("", "empty"),
        ("Vector_Admin_2024", "case_sensitive"),
        ("vector_admin_2024 ", "with_space")
    ]
    
    print("🧪 Testing Admin Password Logic")
    print("=" * 40)
    
    for password_input, test_type in test_cases:
        print(f"\nTest: {test_type}")
        print(f"Input: '{password_input}'")
        
        # This is the exact logic from the app
        if password_input == "vector_admin_2024":
            result = "✅ Admin access granted!"
        elif password_input:
            result = "❌ Invalid password"
        else:
            result = "⚠️ Please enter a password"
        
        print(f"Result: {result}")
    
    print("\n" + "=" * 40)
    print("✅ Password logic test complete!")

if __name__ == "__main__":
    test_password_logic()