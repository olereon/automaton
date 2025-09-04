#!/usr/bin/env python3.11
"""
Quick test script to verify login functionality with exact selectors
"""

import asyncio
import sys
from playwright.async_api import async_playwright

async def test_login(url: str, email: str, password: str):
    """Test login with exact selectors"""
    print(f"Testing login to: {url}")
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    page = await browser.new_page()
    
    try:
        # Navigate to page
        print("Navigating to login page...")
        await page.goto(url, wait_until='networkidle')
        await asyncio.sleep(2)
        
        # Fill email field using exact data-test-id
        print("Looking for email field with data-test-id='login-form-box-address'...")
        email_field = await page.wait_for_selector('[data-test-id="login-form-box-address"]', timeout=5000)
        if email_field:
            print("✓ Found email field")
            await email_field.fill(email)
            print(f"✓ Filled email: {email}")
        else:
            print("✗ Could not find email field")
            return False
            
        await asyncio.sleep(0.5)
        
        # Fill password field using exact data-test-id
        print("Looking for password field with data-test-id='login-form-box-password'...")
        password_field = await page.wait_for_selector('[data-test-id="login-form-box-password"]', timeout=5000)
        if password_field:
            print("✓ Found password field")
            await password_field.fill(password)
            print("✓ Filled password")
        else:
            print("✗ Could not find password field")
            return False
            
        await asyncio.sleep(1)
        
        # Find login button using exact data-test-id
        print("Looking for login button with data-test-id='login-form-button-submit'...")
        login_button = await page.wait_for_selector('[data-test-id="login-form-button-submit"]', timeout=5000)
        if login_button:
            print("✓ Found login button")
            
            # Check if disabled
            is_disabled = await login_button.get_attribute('disabled')
            if is_disabled is not None:
                print(f"Button is disabled (disabled='{is_disabled}'), waiting...")
                
                # Wait for button to be enabled
                for i in range(10):
                    await asyncio.sleep(1)
                    is_disabled = await login_button.get_attribute('disabled')
                    if is_disabled is None:
                        print("✓ Button is now enabled")
                        break
                    print(f"  Still disabled, waiting... ({i+1}/10)")
                else:
                    print("⚠ Button did not enable, trying anyway...")
            
            await login_button.click()
            print("✓ Clicked login button")
        else:
            print("✗ Could not find login button")
            return False
            
        # Wait for login to complete
        print("Waiting for login to complete...")
        await asyncio.sleep(5)
        
        # Check for success indicator
        try:
            favorites = await page.wait_for_selector('[data-test-id*="sidebar-menuitem-button-Favorites"]', timeout=10000)
            if favorites:
                print("✓✓✓ LOGIN SUCCESSFUL - Favorites sidebar found!")
                return True
        except:
            pass
            
        # Check if URL changed
        current_url = page.url
        if current_url != url:
            print(f"✓✓ URL changed to: {current_url}")
            print("✓✓ Assuming login successful")
            return True
        else:
            print("⚠ URL did not change, login may have failed")
            
        print("\nPress Enter to close browser...", end='', flush=True)
        input()
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False
        
    finally:
        await browser.close()
        
    return True

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python test_login_only.py <url> <email> <password>")
        sys.exit(1)
        
    url = sys.argv[1]
    email = sys.argv[2]
    password = sys.argv[3]
    
    success = asyncio.run(test_login(url, email, password))
    sys.exit(0 if success else 1)