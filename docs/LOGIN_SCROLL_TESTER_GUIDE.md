# Login and Scroll Testing Tool - User Guide

## Overview

The `login_scroll_tester.py` script is a comprehensive web automation testing tool that:
1. Logs into a website using provided credentials
2. Waits for successful login confirmation (e.g., sidebar element)
3. Detects all scrollable containers on the page
4. Tests 8 different scrolling methods
5. Asks for user confirmation after each test
6. Generates a performance-ranked report

## Prerequisites

- Python 3.11 or higher
- Playwright library (`pip install playwright`)
- Playwright browsers (`playwright install chromium`)

## Installation

```bash
# Install required packages
pip install playwright asyncio

# Install Playwright browsers
playwright install chromium
```

## Usage

### Basic Command

```bash
python3.11 scripts/login_scroll_tester.py \
  --url "https://example.com/login" \
  --email "your.email@example.com" \
  --password "yourpassword"
```

### With Verbose Logging

```bash
python3.11 scripts/login_scroll_tester.py \
  --url "https://example.com/login" \
  --email "your.email@example.com" \
  --password "yourpassword" \
  --verbose
```

## Scrolling Methods Tested

The tool tests 8 different scrolling methods and ranks them by performance:

1. **window.scrollBy()** - Direct window scrolling
2. **window.scrollTo(smooth)** - Smooth animated scrolling  
3. **Element.scrollIntoView()** - Scroll to specific elements
4. **container.scrollTop** - Direct container manipulation
5. **Keyboard (PageDown)** - Keyboard navigation
6. **Mouse Wheel** - Mouse wheel simulation
7. **documentElement.scrollTop** - Document-level scrolling
8. **Custom Scroll Event** - Event dispatch method

## Testing Process

1. **Login Phase**
   - Navigates to the provided URL
   - Finds and fills email/password fields
   - Clicks login button (supports variations: "Log In", "Log in", "LOGIN", etc.)
   - Waits for successful login indicator

2. **Container Detection**
   - Scans page for all scrollable elements
   - Identifies hidden scrollbars
   - Reports container properties (height, overflow, etc.)

3. **Scroll Testing**
   - Resets scroll position before each test
   - Executes scroll method
   - Measures scroll distance and execution time
   - **Prompts user for confirmation (y/n)**
   - Records all metrics

4. **Report Generation**
   - Ranks methods by combined score:
     - User confirmation (40 points)
     - Technical success (30 points)  
     - Scroll distance (10 points)
     - Speed (10 points)
     - Non-interference bonus (10 points)

## Output Files

The tool generates three output files:

### 1. `scroll_test_results.log`
Detailed execution log with timestamps and debug information.

### 2. `scroll_test_results.json`
Structured data with all test results:
```json
{
  "timestamp": "2024-08-15T10:30:00",
  "url": "https://example.com",
  "results": [...],
  "ranked_results": [...]
}
```

### 3. `scroll_test_report.txt`
Human-readable report with rankings and recommendations:
```
SCROLL METHOD TEST RESULTS SUMMARY
==================================
Rank #1: window.scrollBy()
  ✓ Success: True
  ✓ User Confirmed: True
  ✓ Scroll Distance: 800px
  ✓ Execution Time: 0.523s
  ✓ Requires Mouse: False
  ✓ Requires Keyboard: False
```

## User Interaction

During testing, you'll see prompts like:
```
============================================================
Method tested: window.scrollBy()
Did you observe scrolling on the page? (y/n): 
```

**Important**: Watch the browser window and confirm whether scrolling occurred.

## Security and Ethics

⚠️ **IMPORTANT NOTICES:**

1. **Authorization Required**: Only use on websites you own or have explicit permission to test
2. **Respect ToS**: Always check and comply with the website's Terms of Service
3. **Rate Limiting**: The tool includes delays to avoid overwhelming servers
4. **No Malicious Use**: Never use for unauthorized access or data scraping
5. **Credentials**: Never hardcode credentials; use command-line arguments or environment variables

## Troubleshooting

### Login Fails
- Check if the login button text matches expected values
- Verify email/password field selectors are correct
- Increase timeouts if the site loads slowly

### No Scrolling Detected
- Some sites use custom scroll implementations
- Check if the page has dynamic content loading
- Try the `--verbose` flag for detailed debugging

### Browser Doesn't Open
- Ensure Playwright browsers are installed: `playwright install chromium`
- Check system requirements for Playwright

## Customization

To add support for specific websites, you can modify:

1. **Login selectors** (lines 130-180): Add site-specific email/password field selectors
2. **Login button text** (lines 190-200): Add variations of login button text
3. **Success indicators** (lines 220-230): Add elements that indicate successful login
4. **Scroll methods**: Add custom scrolling implementations for specific frameworks

## Example Use Cases

### Testing Single-Page Applications
```bash
python3.11 scripts/login_scroll_tester.py \
  --url "https://spa-app.com/login" \
  --email "test@example.com" \
  --password "testpass"
```

### Testing Infinite Scroll Galleries
The tool is particularly useful for testing infinite scroll implementations in image galleries or feed-based applications.

### Accessibility Testing
Use the ranking system to identify which scroll methods work best with assistive technologies.

## Best Practices

1. **Run tests in a controlled environment**: Use staging/test servers when possible
2. **Document your findings**: Keep the generated reports for future reference
3. **Test multiple browsers**: Consider running tests in different browsers
4. **Respect rate limits**: Don't run tests repeatedly in quick succession
5. **Clean up**: Delete log files containing sensitive information after testing

## Support

For issues or questions about the automaton project, refer to the main project documentation or create an issue in the repository.