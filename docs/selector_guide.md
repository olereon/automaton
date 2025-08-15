# 🎯 CSS Selector Guide for Web Automation

## Quick Start: Finding Selectors

### Method 1: Use the Selector Finder Tool (Recommended)
```bash
cd /home/olereon/workspace/github.com/olereon/automaton
python3 examples/selector_finder.py
```

This tool will:
- ✅ Open your target website in a browser
- ✅ Automatically find all input fields, buttons, and forms
- ✅ Suggest the best CSS selectors for each element
- ✅ Let you test selectors interactively

### Method 2: Browser Developer Tools

1. **Right-click** on the element you want to interact with
2. Select **"Inspect"** or **"Inspect Element"**
3. In the developer tools:
   - **Right-click** on the highlighted HTML element
   - Choose **"Copy"** → **"Copy selector"**
   - Paste this selector into your automation config

### Method 3: Manual Selector Creation

## 🔧 CSS Selector Types

### 1. ID Selectors (Most Reliable)
```css
#username          /* Element with id="username" */
#login-button      /* Element with id="login-button" */
```

### 2. Name Attribute Selectors
```css
input[name="email"]     /* Input with name="email" */
button[name="submit"]   /* Button with name="submit" */
```

### 3. Type Selectors
```css
input[type="password"]  /* Password input field */
input[type="email"]     /* Email input field */
button[type="submit"]   /* Submit button */
```

### 4. Class Selectors
```css
.login-form            /* Element with class="login-form" */
.btn-primary           /* Element with class="btn-primary" */
```

### 5. Placeholder Selectors
```css
input[placeholder*="username"]  /* Input with "username" in placeholder */
input[placeholder*="password"]  /* Input with "password" in placeholder */
```

### 6. Text Content Selectors (Playwright)
```css
button:has-text("Login")     /* Button containing "Login" text */
button:has-text("Sign In")   /* Button containing "Sign In" text */
```

### 7. Partial Match Selectors
```css
[id*="user"]           /* Any element with "user" in ID */
[class*="login"]       /* Any element with "login" in class */
[name*="email"]        /* Any element with "email" in name */
```

## 🎯 Common Login Page Patterns

### Username/Email Fields
```css
/* Try these selectors in order: */
input[name="username"]
input[name="email"]  
input[type="email"]
input[id="username"]
input[id="email"]
input[placeholder*="username"]
input[placeholder*="email"]
#username
#email
.username
.email
```

### Password Fields
```css
/* Try these selectors in order: */
input[type="password"]
input[name="password"]
input[id="password"]
input[placeholder*="password"]
#password
.password
```

### Login/Submit Buttons
```css
/* Try these selectors in order: */
button[type="submit"]
input[type="submit"]
button:has-text("Login")
button:has-text("Sign In")
button:has-text("Submit")
button[name*="login"]
button[id*="login"]
#login
#submit
.login-btn
.submit-btn
```

## 🔍 Selector Testing

### In Browser Console
Open browser dev tools (F12) and test selectors:
```javascript
// Test if selector finds elements
document.querySelectorAll('input[name="username"]')

// Test if element is visible and clickable
document.querySelector('#login-button').click()
```

### Using the Selector Finder Tool
```bash
python3 examples/selector_finder.py
```

## 🚨 Common Issues & Solutions

### Issue 1: "Element not found"
**Causes:**
- Wrong selector syntax
- Element loads after page load (dynamic content)
- Element is inside an iframe

**Solutions:**
```css
/* Instead of: */
#username

/* Try: */
input[name*="user"]     /* Partial match */
[id*="user"]           /* Any element containing "user" */
```

### Issue 2: "Element not clickable"
**Causes:**
- Element is hidden
- Element is behind another element
- Element needs focus first

**Solutions:**
- Add `wait_for_element` action before clicking
- Try clicking a parent element
- Add a small `wait` action before clicking

### Issue 3: "Selector works in browser but not in automation"
**Causes:**
- Timing issues
- Element state changes
- JavaScript modifies the page

**Solutions:**
- Increase timeout values
- Add wait actions between steps
- Use more specific selectors

## 💡 Best Practices

### 1. Selector Priority Order
1. **ID selectors** - Most reliable: `#username`
2. **Name attributes** - Very reliable: `input[name="email"]`
3. **Type + attributes** - Good: `input[type="password"]`
4. **Class selectors** - Less reliable: `.login-form`
5. **Complex selectors** - Last resort: `div > form > input:nth-child(2)`

### 2. Make Selectors Robust
```css
/* Good - specific but not fragile */
input[name="username"]
button[type="submit"]

/* Avoid - too specific, likely to break */
body > div:nth-child(3) > form > div:nth-child(1) > input
```

### 3. Test with Multiple Pages
- Test selectors on different pages of the same site
- Some sites have different forms for different sections

### 4. Use the Automation's Visible Mode
Set `headless: false` in your config to watch what happens:
```json
{
  "headless": false,
  "actions": [...]
}
```

## 🛠️ Debugging Workflow

1. **Run the selector finder tool** on your target site
2. **Copy the suggested selectors** from the analysis
3. **Test selectors** in the interactive mode
4. **Update your automation config** with working selectors
5. **Run automation in visible mode** to verify
6. **Check logs** if actions still fail

## 📋 Example: Login Automation

```json
{
  "name": "Website Login",
  "url": "https://yoursite.com/login",
  "headless": false,
  "actions": [
    {
      "type": "wait_for_element",
      "selector": "input[name='username']",
      "timeout": 10000,
      "description": "Wait for username field"
    },
    {
      "type": "input_text", 
      "selector": "input[name='username']",
      "value": "your_username",
      "description": "Enter username"
    },
    {
      "type": "input_text",
      "selector": "input[type='password']", 
      "value": "your_password",
      "description": "Enter password"
    },
    {
      "type": "click_button",
      "selector": "button[type='submit']",
      "description": "Click login button"
    }
  ]
}
```

Remember: **Start with the selector finder tool** - it will save you time and show you exactly what selectors work on your specific website!