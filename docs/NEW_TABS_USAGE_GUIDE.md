# New Action and Selector Tabs Usage Guide

## Overview

The Web Automation Tool now includes two powerful new tabs to enhance your automation workflow:

- **Action Tab**: Advanced action building and sequence management
- **Selector Tab**: HTML element analysis and robust selector generation

## Action Tab Features

### 1. Action Parameters Panel (Left Side)

The Action Parameters panel allows you to configure individual actions with precision:

#### Fields Available:
- **Action Type**: Dropdown with all available ActionType values
- **Selector**: CSS/XPath selector for targeting elements (auto-enabled based on action type)
- **Value**: Input value for actions like text input or file upload (auto-enabled based on action type)
- **Description**: Multi-line text area for action documentation
- **Timeout (ms)**: Timeout value in milliseconds (default: 10000)

#### Smart Field Management:
- Fields are automatically enabled/disabled based on selected action type
- For example: `input_text` enables both Selector and Value fields
- Actions like `wait` only enable the Value field for timing

#### Management Buttons:
- **Apply to Main**: Adds the configured action to the main Automation tab
- **Copy from Main**: Copies selected action from main tab to Action parameters
- **Clear**: Resets all parameter fields

### 2. Action Sequence Builder (Right Side)

Build and test complete action sequences before applying to main automation:

#### Features:
- **Add Action**: Creates actions from current parameters
- **Edit Selected**: Loads selected action back to parameters for editing
- **Delete**: Removes selected action from sequence
- **Move Up**: Reorders actions within the sequence
- **Test Action**: Tests individual actions (requires browser integration)
- **Clear All**: Removes all actions from the sequence

#### Sequence Display:
Actions are displayed with clear formatting:
```
1. input_text -> #username... = test@example.com...
2. click_button -> .submit-btn...
3. wait = 2000...
```

### 3. Action Test Output (Bottom)

Real-time logging for action building activities:
- Timestamped messages for all actions
- Parameter changes and validation results
- Error messages and debugging information

## Selector Tab Features

### 1. Selector Tools Panel (Left Side)

#### Input Fields:
- **Page URL**: Target webpage for element analysis
- **Element Identifier**: ID, class, or text to search for
- **Strategy**: Selector generation strategy
  - `all`: Generate all selector types
  - `id`: ID-based selectors only
  - `class`: Class-based selectors only
  - `css`: CSS selectors
  - `xpath`: XPath expressions
  - `text`: Text-based selectors
  - `attribute`: Attribute-based selectors
  - `dynamic`: Dynamic pattern selectors

#### Action Buttons:
- **Analyze Page**: Extract page structure and elements (requires browser integration)
- **Generate Selectors**: Create selector recommendations based on identifier and strategy
- **Test Custom Selector**: Validate custom selector expressions

#### Custom Selector Input:
Multi-line text area for entering and testing custom selectors like:
```css
div[data-testid*="submit"] button:not([disabled])
```

### 2. HTML Element Analysis Panel (Right Side)

Displays detailed HTML structure analysis including:
- Element hierarchy and nesting
- Available attributes (id, class, data-*, aria-*)
- Text content and labels
- Form elements and their properties

### 3. Selector Recommendations & Results (Bottom)

TreeView display with comprehensive selector analysis:

#### Columns:
- **Type**: Selector category (ID, Class, CSS, XPath, etc.)
- **Selector**: The actual selector expression
- **Reliability**: How stable the selector is (High/Medium/Low)
- **Dynamic Support**: Resistance to UI changes (High/Medium/Low/Very High)
- **Matches**: Expected number of matching elements

#### Management Buttons:
- **Copy Selected**: Copies selector to clipboard
- **Use in Action Tab**: Automatically switches to Action tab and populates selector field
- **Verify Selector**: Tests selector against live page (requires browser integration)
- **Clear Results**: Removes all results from the display

## Cross-Tab Integration

### Action ↔ Main Tab Integration

1. **Apply to Main**: 
   ```
   Action Tab → Configure parameters → "Apply to Main" → Main Automation Tab
   ```

2. **Copy from Main**:
   ```
   Main Tab → Select action → Switch to Action Tab → "Copy from Main"
   ```

### Selector → Action Integration

1. **Generate selectors in Selector tab**
2. **Select best selector from results**
3. **Click "Use in Action Tab"**
4. **Automatically switches to Action tab with selector populated**

### Typical Workflow

```
1. Selector Tab: Enter URL and element identifier
2. Selector Tab: Generate selector recommendations
3. Selector Tab: "Use in Action Tab" for best selector
4. Action Tab: Configure action type and parameters
5. Action Tab: "Apply to Main" to add to automation sequence
6. Main Tab: Run complete automation
```

## Advanced Features

### Dynamic Selector Patterns

The Selector tab supports advanced dynamic patterns:

```css
# Container-based search (handles dynamic IDs)
div[id*="container"] .button-class

# Text-based selection (UI-change resistant)  
*:has-text("Submit Order")

# Attribute pattern matching
[data-testid*="submit"][aria-label*="button"]
```

### Action Sequence Management

Build complex sequences with flow control:

1. **Input text** → Username field
2. **Input text** → Password field  
3. **Click button** → Login button
4. **Wait for element** → Dashboard indicator
5. **Click button** → Action button

### Parameter Copying

Efficiently manage action parameters:
- Copy successful actions from main tab for modification
- Build template sequences in Action tab
- Apply refined actions back to main workflow

## Browser Integration Notes

Some features require browser integration (marked as "coming soon"):
- **Live page analysis**: Real-time HTML structure extraction
- **Selector verification**: Testing selectors against live pages
- **Action testing**: Individual action execution and validation

These features use placeholder implementations currently and will be enhanced with full browser automation support.

## Tips for Best Results

### Selector Generation:
1. Use specific identifiers when possible (IDs are most reliable)
2. Try multiple strategies to find the most robust selector
3. Prefer data-testid and aria-label attributes for stability
4. Use dynamic patterns for UI elements that change frequently

### Action Building:
1. Build and test action sequences before applying to main
2. Use descriptive action descriptions for documentation
3. Set appropriate timeouts for slow-loading elements
4. Test parameter combinations in Action tab first

### Cross-Tab Workflow:
1. Start with Selector tab for element identification
2. Use Action tab for sequence building and refinement
3. Apply proven sequences to Main tab for execution
4. Iterate between tabs to optimize automation flow

---

*The new Action and Selector tabs provide powerful tools for building robust, maintainable web automation sequences with advanced selector strategies and comprehensive action management.*