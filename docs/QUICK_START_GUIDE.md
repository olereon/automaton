# Quick Start Guide

Get up and running with Automaton in 5 minutes!

## 🚀 Installation (2 minutes)

### 1. Clone and Enter Directory
```bash
git clone https://github.com/yourusername/automaton.git
cd automaton
```

### 2. Quick Setup Script
```bash
# Run this single command to set up everything
python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && playwright install chromium
```

### 3. Verify Installation
```bash
python3.11 -c "import playwright; print('✅ Ready to automate!')"
```

## 🎯 Your First Automation (3 minutes)

### Option 1: GUI Mode (Easiest)

1. **Start the GUI:**
```bash
python3.11 automaton-gui.py
```

2. **Create Your First Automation:**
   - Enter Name: "My First Task"
   - Enter URL: "https://example.com"
   - Click "Add Action"
   - Select "Wait" → Enter 2000 (2 seconds)
   - Click "Add Action" 
   - Select "Log Message" → Enter "Hello Automaton!"
   - Click "Run Automation"

3. **Watch it Run!** The browser will open and execute your actions.

### Option 2: CLI Mode (Fastest)

1. **Create a Simple Config:**
```bash
cat > first_automation.json << 'EOF'
{
  "name": "Hello Automaton",
  "url": "https://example.com",
  "headless": false,
  "actions": [
    {
      "type": "wait",
      "value": 2000,
      "description": "Wait 2 seconds"
    },
    {
      "type": "log_message",
      "value": {
        "message": "Hello from Automaton!"
      },
      "description": "Log greeting"
    }
  ]
}
EOF
```

2. **Run It:**
```bash
python3.11 automaton-cli.py run -c first_automation.json --show-browser
```

## 📝 Common First Automations

### 1. Form Filler
```json
{
  "name": "Form Filler",
  "url": "https://example.com/form",
  "actions": [
    {
      "type": "input_text",
      "selector": "#name",
      "value": "John Doe"
    },
    {
      "type": "input_text",
      "selector": "#email",
      "value": "john@example.com"
    },
    {
      "type": "click_button",
      "selector": "#submit"
    }
  ]
}
```

### 2. Login Automation
```json
{
  "name": "Auto Login",
  "url": "https://example.com/login",
  "actions": [
    {
      "type": "login",
      "value": {
        "username": "your_username",
        "password": "your_password",
        "username_selector": "#username",
        "password_selector": "#password",
        "submit_selector": "#login-btn"
      }
    }
  ]
}
```

### 3. Data Scraper
```json
{
  "name": "Price Checker",
  "url": "https://shop.example.com/product",
  "actions": [
    {
      "type": "wait_for_element",
      "selector": ".price"
    },
    {
      "type": "check_element",
      "selector": ".price",
      "check_type": "less",
      "expected_value": "100"
    },
    {
      "type": "if_begin",
      "value": {"condition": "check_result == true"}
    },
    {
      "type": "log_message",
      "value": {"message": "Good price! Under $100"}
    },
    {
      "type": "if_end"
    }
  ]
}
```

## 🎮 GUI Quick Tips

### Adding Actions
1. Click "Add Action" button
2. Select action type from dropdown
3. Fill in required fields (selector, value, etc.)
4. Add description (optional but helpful)
5. Click "Add" to confirm

### Editing Actions
- Double-click any action in the list to edit
- Right-click for more options
- Drag to reorder actions

### Saving & Loading
- **Save**: File → Save Configuration
- **Load**: File → Load Configuration
- Configs are saved as JSON files

### Running Automation
- Click "Run Automation" to start
- Click "Stop" to gracefully terminate
- Check logs panel for execution details

## 💻 CLI Quick Commands

### Run Automation
```bash
# Basic run
python3.11 automaton-cli.py run -c config.json

# With visible browser
python3.11 automaton-cli.py run -c config.json --show-browser

# Continue on errors
python3.11 automaton-cli.py run -c config.json --continue-on-error
```

### Create Config
```bash
# Interactive creation
python3.11 automaton-cli.py create -n "Task Name" -u "https://site.com" --interactive

# Save to file
python3.11 automaton-cli.py create -n "Task" -u "URL" -o config.json
```

### List Actions
```bash
# See all available action types
python3.11 automaton-cli.py list-actions
```

## 🔍 Finding Selectors

### Browser DevTools Method
1. Right-click element in browser
2. Select "Inspect"
3. Right-click HTML in DevTools
4. Select "Copy" → "Copy selector"

### Common Selector Patterns
- **ID**: `#element-id`
- **Class**: `.class-name`
- **Attribute**: `[data-test="value"]`
- **Combination**: `div.container #submit-btn`

### Test Your Selector
In browser console:
```javascript
document.querySelector("#your-selector")  // Should return the element
```

## 🆘 Quick Troubleshooting

### "Element not found"
- Check selector is correct
- Add `wait_for_element` before the action
- Increase timeout value

### "Browser not found"
```bash
playwright install chromium
```

### Stop button not working
- Wait a moment - stops at next action
- Use Ctrl+C in terminal as backup

### Automation too fast
- Add `wait` actions between steps
- Use `wait_for_element` for dynamic content

## 📚 Next Steps

### Learn More
- [Full Documentation](../README.md)
- [Action Types Reference](ACTION_TYPES_REFERENCE.md)
- [Examples Directory](../examples/)

### Try Examples
```bash
# Queue management demo
python3.11 examples/queue_management_example.py

# While loop demo
python3.11 examples/while_loop_demo.py

# Generation download demo
python3.11 examples/generation_download_demo.py
```

### Advanced Features
- [Conditional Flow](conditional_flow_guide.md)
- [While Loops](WHILE_LOOP_AUTOMATION_GUIDE.md)
- [Generation Downloads](GENERATION_DOWNLOAD_GUIDE.md)
- [Scheduler](AUTOMATION_SCHEDULER_GUIDE.md)

## 💡 Pro Tips

1. **Start Simple**: Begin with basic actions, add complexity gradually
2. **Use Descriptions**: Help future you understand the automation
3. **Test Incrementally**: Run after adding a few actions
4. **Save Often**: Save configurations for reuse
5. **Check Logs**: Logs panel shows detailed execution info
6. **Use Variables**: Store and reuse values with `set_variable`
7. **Handle Errors**: Use IF/ELSE for error recovery

---

**Need Help?** 
- Check [Troubleshooting Guide](../README.md#troubleshooting)
- Review [Examples](../examples/)
- Read [Full Documentation](../README.md)

*You're now ready to automate! 🎉*