# Prompt Extraction Fix - September 2025

## 🐛 Issue Identified

**Problem**: Generation download automation fails to extract prompts while creation time extraction works correctly.

**Root Cause**: HTML structure changes broke existing CSS selectors for prompt extraction.

## 📊 Debug Analysis

From debug logs: `"prompt_extracted": false` consistently, while `"date_extracted": true` works fine.

### Old HTML Structure (Before):
```html
<div class="sc-jJRqov cxtNJi">
  <span aria-describedby="...">Prompt text here</span>
</div>
```

### New HTML Structure (September 2025):
```html
<div class="sc-fileXT gEIKhI">
  <div class="sc-eKQYOU bdGRCs">
    <span aria-describedby=":rvu:" data-spm-anchor-id="...">
      The camera begins with a low-angle medium shot of the Nightmare Wraith Rider...
    </span>...
  </div>
</div>
```

## 🔧 Fixes Applied

### 1. Updated Config File Selectors
**File**: `/scripts/fast_generation_skip_config.json`

```json
{
  "_comment_updated_selectors": "UPDATED: Fixed selectors for new HTML structure September 2025",
  "generation_date_selector": ".sc-hAYgFD.fLPdud",
  "prompt_selector": ".sc-eKQYOU.bdGRCs span[aria-describedby]",
  "prompt_class_selector": ".sc-eKQYOU.bdGRCs",
  "prompt_container_selector": ".sc-fileXT.gEIKhI"
}
```

### 2. Updated Core Extraction Settings
**File**: `/src/utils/generation_download_manager.py`

**Changes**:
- `prompt_class_selector`: `"div.sc-dDrhAi.dnESm"` → `".sc-eKQYOU.bdGRCs"`
- `prompt_selector`: `".sc-jJRqov.cxtNJi span[aria-describedby]"` → `".sc-eKQYOU.bdGRCs span[aria-describedby]"`
- `min_prompt_length`: `150` → `50` (better detection sensitivity)

### 3. Enhanced Fallback Strategy
**Multiple selector support with priority order**:

```python
prompt_selectors = [
    # NEW (September 2025)
    ".sc-eKQYOU.bdGRCs span[aria-describedby]",  # Primary
    ".sc-fileXT.gEIKhI .sc-eKQYOU.bdGRCs span",  # With context
    ".sc-eKQYOU.bdGRCs span:first-child",        # First span
    
    # LEGACY (Fallback support)
    ".sc-dDrhAi.dnESm span:first-child",         # Old structure
    ".sc-jJRqov.cxtNJi span[aria-describedby]",  # Old specific
    
    # GENERIC (Last resort)
    "span[aria-describedby]",                    # Any aria spans
    "xpath=//span[@aria-describedby]"            # XPath fallback
]
```

## 🎯 Key Selector Mappings

| Element | Old Selector | New Selector | Status |
|---------|-------------|--------------|--------|
| **Prompt Container** | `div.sc-dDrhAi.dnESm` | `.sc-eKQYOU.bdGRCs` | ✅ Fixed |
| **Prompt Text** | `.sc-jJRqov.cxtNJi span[aria-describedby]` | `.sc-eKQYOU.bdGRCs span[aria-describedby]` | ✅ Fixed |
| **Date Container** | `.sc-eJlwcH.gjlyBM span.sc-cSMkSB.hUjUPD:nth-child(2)` | `.sc-hAYgFD.fLPdud` | ✅ Fixed |
| **Main Container** | N/A | `.sc-fileXT.gEIKhI` | ✅ Added |

## 🧪 Testing Commands

```bash
# Test the updated extraction with debug logging
python3.11 scripts/fast_generation_downloader.py --config scripts/fast_generation_skip_config.json --mode skip --max-downloads 2

# Check debug logs for prompt extraction success
tail -f logs/debug_generation_downloads_*.json | grep "prompt_extracted"

# Verify extracted prompts in the log file
cat logs/generation_downloads_*.txt | grep -A1 "Prompt:"
```

## 📋 Expected Results

**Before Fix**:
- ❌ `"prompt_extracted": false`
- ❌ Downloads succeed but missing prompt metadata
- ❌ Log files show empty or truncated prompt fields

**After Fix**:
- ✅ `"prompt_extracted": true`
- ✅ Full prompt text captured in logs
- ✅ Proper filename generation with prompt content

## 🔄 Backward Compatibility

The fix maintains **backward compatibility** through:
1. **Multiple selector support**: New selectors first, old selectors as fallbacks
2. **Graceful degradation**: If new selectors fail, system tries legacy selectors
3. **Configuration override**: Custom configs can still specify their own selectors

## 🚨 Monitoring

**Key metrics to monitor**:
- Debug log: `"prompt_extracted": true`
- Log file: Prompt text appears and is not truncated
- Filenames: Include proper prompt-based naming
- Extraction time: Should remain fast with new selectors

## 📈 Impact Assessment

**High Impact Fix**:
- **Critical**: Prompt extraction was completely broken
- **User Experience**: Downloads now include complete metadata
- **Data Quality**: Full prompt text preservation
- **Automation Success**: Improved success rate for metadata extraction

---

**Status**: ✅ **COMPLETE** - Ready for production testing  
**Priority**: 🔴 **CRITICAL** - Essential for metadata collection  
**Compatibility**: ✅ **BACKWARD COMPATIBLE** - Legacy fallbacks included