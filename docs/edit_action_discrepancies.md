# Edit Action Window Discrepancies Report

## Missing Action Types in Edit Dialog

The following action types are not properly handled in the `_create_action_fields` method used by the Edit Action dialog:

1. **EXPAND_DIALOG** - Missing completely
2. **CHECK_QUEUE** - Missing completely  
3. **DOWNLOAD_FILE** - Missing completely
4. **REFRESH_PAGE** - Missing completely
5. **SWITCH_PANEL** - Missing completely
6. **TOGGLE_SETTING** - Missing completely
7. **STOP_AUTOMATION** - Missing completely

## Field Inconsistencies

### Input Field Types
- **Add Action Dialog**: Uses `tk.Text` widgets for multi-line input (better for long selectors)
- **Edit Action Dialog**: Uses `ttk.Entry` widgets (single line, may truncate long values)

### Missing Fields for Existing Action Types
All action types that require selector and/or value fields are not getting them properly in the Edit dialog when they don't match the specific cases handled.

## Required Fixes

### 1. Add Missing Action Types to `_create_action_fields`
- EXPAND_DIALOG - needs selector field
- CHECK_QUEUE - needs selector and value fields
- DOWNLOAD_FILE - needs selector field
- REFRESH_PAGE - no additional fields needed
- SWITCH_PANEL - needs selector field
- TOGGLE_SETTING - needs selector and boolean value field
- STOP_AUTOMATION - no additional fields needed

### 2. Update Field Widget Types
- Consider using Text widgets consistently for better UX with long selectors
- Or at minimum, increase Entry widget width for better visibility

### 3. Ensure Consistent Field Layout
- Match the field creation logic between Add and Edit dialogs
- Use the same helper methods for field creation where possible