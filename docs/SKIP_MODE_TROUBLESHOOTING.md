# SKIP Mode Troubleshooting Guide

## 🚨 Common Issues and Solutions

### Issue 1: Script Running in FINISH Mode Instead of SKIP Mode

**Symptom**: 
```
🔄 Duplicate mode: FINISH
📌 FINISH mode: Will stop when reaching previously downloaded content
```

**Cause**: The command-line argument defaults to FINISH mode and overrides the config file setting.

**Solution**: Always specify `--mode skip` explicitly:
```bash
# CORRECT - Explicitly set SKIP mode
python3.11 scripts/fast_generation_downloader.py --config scripts/fast_generation_skip_config.json --mode skip

# WRONG - Will default to FINISH mode
python3.11 scripts/fast_generation_downloader.py --config scripts/fast_generation_skip_config.json
```

### Issue 2: Fast-Forward Not Finding Checkpoint (Metadata Extraction Failing)

**Symptom**:
```
⏩ Fast-forward mode: Will check metadata after clicking landmark_thumbnail_1
⏩ Not checkpoint, continuing fast-forward
```
Repeats for every thumbnail without finding checkpoint.

**Possible Causes**:

#### A. Page Structure Changed
The website may have updated their HTML structure, breaking the selectors.

**Solution**: Run the metadata extraction test script:
```bash
python3.11 scripts/test_metadata_extraction.py
```
This will show which selectors work and which don't.

#### B. Metadata Panel Not Loading
The metadata panel might not be appearing after clicking thumbnails.

**Solution**: Increase wait time in `_extract_metadata_after_click`:
```python
# Change from:
await page.wait_for_timeout(1500)
# To:
await page.wait_for_timeout(3000)
```

#### C. Wrong Checkpoint Format
The checkpoint time format might not match what's displayed.

**Check**: Look at your log file:
```bash
head -5 /home/olereon/workspace/github.com/olereon/automaton/logs/generation_downloads.txt
```

The date should be in format: `29 Aug 2025 16:34:18`

### Issue 3: Downloads Not Starting After Checkpoint Found

**Symptom**: Checkpoint is found but downloads don't start.

**Solution**: Ensure the checkpoint detection properly sets flags:
- `self.checkpoint_found = True`
- `self.fast_forward_mode = False`

### Issue 4: Exit-Scan-Return Strategy Alternative

If traditional fast-forward continues to fail, enable the Exit-Scan-Return strategy which is more reliable:

**In your config file**, set:
```json
{
  "use_exit_scan_strategy": true,
  "duplicate_mode": "skip"
}
```

**Benefits**:
- Doesn't rely on metadata being visible in gallery
- 50-70x faster than traditional fast-forward
- More reliable checkpoint detection

## 🔧 Quick Fixes

### 1. Command Line Fix
Always use the complete command:
```bash
python3.11 scripts/fast_generation_downloader.py \
  --config scripts/fast_generation_skip_config.json \
  --mode skip
```

### 2. Config File Fix
Ensure your config has:
```json
{
  "duplicate_mode": "skip",
  "duplicate_check_enabled": true,
  "stop_on_duplicate": false,
  "use_exit_scan_strategy": true  // Enable for better reliability
}
```

### 3. Fallback to Exit-Scan-Return
If metadata extraction keeps failing, the Exit-Scan-Return strategy bypasses the issue entirely:
```json
"use_exit_scan_strategy": true
```

## 📊 Debugging Steps

### Step 1: Verify Mode
Check the output shows SKIP mode:
```
🔄 Duplicate mode: SKIP
📌 SKIP mode: Will continue searching past duplicate generations
```

### Step 2: Check Checkpoint Loading
Look for:
```
🔖 Last downloaded checkpoint found:
   📅 Creation Time: 29 Aug 2025 16:34:18
```

### Step 3: Monitor Metadata Extraction
With debug logging enabled, you should see:
```
📊 Extracted metadata: Time='29 Aug 2025 16:34:18', Prompt='The camera begins...'
🎯 Checkpoint target: Time='29 Aug 2025 16:34:18', Prompt='The camera begins...'
```

### Step 4: Watch for Checkpoint Match
Success looks like:
```
✅ CHECKPOINT FOUND: landmark_thumbnail_25
📅 Creation Time: 29 Aug 2025 16:34:18
🔗 Matches checkpoint - switching to download mode for next items
```

## 🚀 Recommended Configuration

For maximum reliability and speed, use this configuration:

```json
{
  "type": "start_generation_downloads",
  "value": {
    "duplicate_mode": "skip",
    "duplicate_check_enabled": true,
    "stop_on_duplicate": false,
    "use_exit_scan_strategy": true,
    "enable_debug_logging": true,
    "creation_time_comparison": true,
    "_comment": "Exit-scan-return provides 50-70x faster checkpoint navigation"
  }
}
```

And run with:
```bash
python3.11 scripts/fast_generation_downloader.py \
  --config your_config.json \
  --mode skip
```

## 💡 Pro Tips

1. **Always use `--mode skip`** in the command line
2. **Enable `use_exit_scan_strategy`** for better performance
3. **Check log file exists** before running SKIP mode
4. **Use debug logging** to troubleshoot issues
5. **Test with small batches** first to verify it's working

## 🔗 Related Documentation

- [Enhanced SKIP Mode Guide](ENHANCED_SKIP_MODE_GUIDE.md)
- [Exit-Scan-Return Strategy Guide](EXIT_SCAN_RETURN_STRATEGY_GUIDE.md)
- [Fast-Forward Fix Guide](FAST_FORWARD_FIX_GUIDE.md)
- [Generation Download Guide](GENERATION_DOWNLOAD_GUIDE.md)

---

*Last Updated: August 2025*
*Version: 1.0.0*