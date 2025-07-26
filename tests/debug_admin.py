#!/usr/bin/env python3
"""
Debug admin password functionality
Run this to verify the password is working
"""

import streamlit as st

def debug_admin_form():
    """Create a minimal admin form for testing"""
    
    st.title("🔐 Admin Password Debug")
    st.markdown("---")
    
    # Initialize session state
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    if 'show_vector_admin' not in st.session_state:
        st.session_state.show_vector_admin = False
    
    # Admin login form
    st.markdown("### 🔧 Admin Access Test")
    
    admin_password = st.text_input("Enter admin password:", type="password", key="admin_pass")
    
    if st.button("🔐 Test Admin Access"):
        st.markdown("**Debug Info:**")
        st.write(f"Password entered: '{admin_password}'")
        st.write(f"Password length: {len(admin_password)}")
        st.write(f"Expected password: 'vector_admin_2024'")
        st.write(f"Passwords match: {admin_password == 'vector_admin_2024'}")
        
        if admin_password == "vector_admin_2024":
            st.session_state.show_vector_admin = True
            st.session_state.admin_authenticated = True
            st.success("✅ Admin access granted!")
            st.balloons()
        elif admin_password:
            st.error("❌ Invalid password")
            st.write("❗ Hint: Check for typos, case sensitivity, or extra spaces")
        else:
            st.warning("⚠️ Please enter a password")
    
    # Show current status
    st.markdown("---")
    st.markdown("### 📊 Current Status")
    st.write(f"Admin authenticated: {st.session_state.get('admin_authenticated', False)}")
    st.write(f"Show admin interface: {st.session_state.get('show_vector_admin', False)}")
    
    if st.session_state.get('admin_authenticated', False):
        st.success("🔓 Admin mode is active!")
        if st.button("🚪 Logout Admin"):
            st.session_state.show_vector_admin = False
            st.session_state.admin_authenticated = False
            st.rerun()
    else:
        st.info("🔒 Admin mode not active")
    
    # Quick test buttons
    st.markdown("---")
    st.markdown("### 🧪 Quick Tests")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Test Correct Password"):
            st.session_state.test_password = "vector_admin_2024"
            st.rerun()
    
    with col2:
        if st.button("❌ Test Wrong Password"):
            st.session_state.test_password = "wrong_password"
            st.rerun()
    
    # Auto-fill for testing
    if 'test_password' in st.session_state:
        st.info(f"Auto-filled password: '{st.session_state.test_password}'")
        st.markdown("👆 **Now click the 'Test Admin Access' button above**")

if __name__ == "__main__":
    debug_admin_form()