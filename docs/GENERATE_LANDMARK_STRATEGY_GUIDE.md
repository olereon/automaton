# Generate Landmark Strategy Guide

## 🎯 Updated Workflow Strategy

This guide explains the new approach for navigating to the Generate page and detecting queue status using more reliable selectors.

---

## 🔍 Key Changes Made

### 1. **Generate Page Navigation**

**Old Strategy:**
```json
// Used class-based selectors that might change
"selector": ".sc-cmdOMZ.jZnOHe"
```

**New Strategy:**
```json
// Use text landmark for reliable navigation
"selector": "text=\"Generate\""
```

**Benefits:**
- ✅ Text content rarely changes
- ✅ More reliable than CSS classes
- ✅ Human-readable and maintainable
- ✅ Works even if CSS styling changes

### 2. **Queue Number Detection**

**Old Strategy:**
```json
// Used different class selectors
"selector": ".sc-dMmcxd.cZTIpi"
```

**New Strategy:**
```json
// Use the specific queue number div
"selector": ".sc-fGqoZs.fWNdKz"
```

**Benefits:**
- ✅ More specific to queue number element
- ✅ Targets the actual number container
- ✅ Better for conditional logic

---

## 📋 Complete Selector Strategy

### Generate Button Detection Options

```json
// Option 1: Text landmark (RECOMMENDED)
{
  "type": "click_button",
  "selector": "text=\"Generate\"",
  "description": "Navigate using Generate text"
}

// Option 2: SVG icon targeting
{
  "type": "click_button", 
  "selector": "use[xlink:href=\"#icon-icon_daohang_24px_Generate\"]",
  "description": "Navigate using SVG icon"
}

// Option 3: Parent div with text
{
  "type": "click_button",
  "selector": ".sc-fstJre.eFrNiR:has-text(\"Generate\")",
  "description": "Navigate using parent div containing Generate text"
}

// Option 4: Combined approach
{
  "type": "click_button",
  "selector": "div:has(use[xlink:href*=\"Generate\"]):has-text(\"Generate\")",
  "description": "Navigate using combined SVG + text detection"
}
```

### Queue Number Detection Options

```json
// Option 1: Direct div selector (RECOMMENDED)
{
  "type": "check_queue",
  "selector": ".sc-fGqoZs.fWNdKz",
  "value": {
    "check": "less",
    "value": "8",
    "attribute": "text"
  }
}

// Option 2: Parent container approach
{
  "type": "check_queue",
  "selector": ".sc-fstJre.eFrNiR .sc-fGqoZs.fWNdKz",
  "value": {
    "check": "less", 
    "value": "8",
    "attribute": "text"
  }
}

// Option 3: XPath approach for more precision
{
  "type": "check_queue",
  "selector": "xpath=//div[contains(@class, 'sc-fGqoZs') and contains(@class, 'fWNdKz') and text()]",
  "value": {
    "check": "less",
    "value": "8", 
    "attribute": "text"
  }
}
```

---

## 🔧 Enhanced Workflow Features

### 1. **Robust Navigation**
- Uses text landmarks instead of fragile CSS classes
- Multiple fallback strategies for element detection
- Better error handling and retry mechanisms

### 2. **Smart Queue Management**
- Initial queue check before starting automation
- Continuous queue monitoring during loop
- Proper break conditions when queue fills up

### 3. **Improved Error Handling**
- Early detection of full queue conditions
- Graceful loop termination with break statements
- Comprehensive logging for debugging

### 4. **Better Loop Structure**
```json
// Initial queue check
"check_queue" → "if_begin" (queue full) → "stop_automation" → "if_end"

// Main processing loop
"while_begin" (queue has space) →
  "task_creation_steps" →
  "check_for_popup" → "break_if_full" →
  "check_queue_again" → "break_if_full" →
"while_end"
```

---

## 🎯 Implementation Strategy

### Phase 1: Basic Implementation
1. Use `text="Generate"` for navigation
2. Use `.sc-fGqoZs.fWNdKz` for queue detection
3. Add initial queue check before main loop

### Phase 2: Enhanced Robustness
1. Add fallback selectors for Generate button
2. Implement retry logic for queue detection
3. Add more comprehensive error handling

### Phase 3: Advanced Features
1. Dynamic selector switching based on page state
2. Machine learning-based element detection
3. Self-healing selector mechanisms

---

## 📊 Selector Reliability Comparison

| Strategy | Reliability | Maintainability | Performance | Recommended |
|----------|-------------|-----------------|-------------|-------------|
| Text landmarks | ★★★★★ | ★★★★★ | ★★★★☆ | ✅ Yes |
| CSS classes | ★★☆☆☆ | ★★☆☆☆ | ★★★★★ | ❌ No |
| SVG icons | ★★★☆☆ | ★★★☆☆ | ★★★★☆ | 🔄 Maybe |
| Combined approach | ★★★★☆ | ★★★☆☆ | ★★★☆☆ | ✅ Yes |

---

## 🧪 Testing Recommendations

### Test Cases to Validate

1. **Generate Navigation Test**
   ```bash
   # Test text landmark approach
   python3.11 automaton-cli.py run -c workflows/run-08-18-1-updated.json --show-browser
   ```

2. **Queue Detection Test**
   ```python
   # Verify queue number extraction
   await page.locator('.sc-fGqoZs.fWNdKz').text_content()
   ```

3. **Fallback Strategy Test**
   ```python
   # Test multiple selector approaches
   selectors = [
       'text="Generate"',
       '.sc-fstJre.eFrNiR:has-text("Generate")', 
       'use[xlink:href*="Generate"]'
   ]
   ```

### Expected Results
- ✅ Successfully navigate to Generate page
- ✅ Correctly detect queue number (0-8)  
- ✅ Proper conditional logic execution
- ✅ Graceful handling of queue full scenarios

---

## 🔍 Troubleshooting Guide

### Generate Button Not Found
```json
// Add multiple selector attempts
{
  "type": "wait_for_element",
  "selector": "text=\"Generate\", .sc-fstJre.eFrNiR, use[xlink:href*=\"Generate\"]",
  "description": "Wait for Generate element using multiple strategies"
}
```

### Queue Number Not Detected
```json
// Enhanced queue detection with fallbacks
{
  "type": "check_element",
  "selector": ".sc-fGqoZs.fWNdKz, [class*=\"fWNdKz\"], div:has-text(\"^[0-8]$\")",
  "description": "Detect queue number using multiple approaches"
}
```

### CSS Classes Changed
```json
// Use more stable selectors
{
  "type": "click_button",
  "selector": "[aria-label*=\"Generate\"], button:has-text(\"Generate\"), text=\"Generate\"",
  "description": "Multiple fallback strategies for Generate button"
}
```

---

## 📋 Summary

The updated workflow (`run-08-18-1-updated.json`) implements:

✅ **Text-based Generate navigation** - More reliable than CSS classes  
✅ **Specific queue number detection** - Uses `.sc-fGqoZs.fWNdKz` selector  
✅ **Enhanced error handling** - Proper break conditions and logging  
✅ **Robust loop structure** - Initial checks and continuous monitoring  
✅ **Better maintainability** - Human-readable selectors and descriptions  

This approach should provide much more reliable automation with better error recovery and easier maintenance when the website UI changes.

---

*Updated: August 25, 2025*  
*Compatible with: Automaton Framework v2.0+*