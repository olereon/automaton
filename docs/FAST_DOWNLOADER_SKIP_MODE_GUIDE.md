# Fast Generation Downloader - SKIP Mode Guide

## 📋 Overview

The `fast_generation_downloader.py` script now supports **SKIP mode** for handling duplicate generations. This allows you to choose between two behaviors when the automation encounters previously downloaded content.

## 🔄 Duplicate Handling Modes

### 1. **FINISH Mode** (Default)
- **Behavior**: Stops automation when reaching previously downloaded content
- **Use Case**: Download only new content since last run
- **Best For**: Daily/regular downloads where you want to stop at the boundary

### 2. **SKIP Mode** (New)
- **Behavior**: Skips duplicates and continues searching for new generations
- **Use Case**: Gallery may have mixed old/new content throughout
- **Best For**: Galleries with interspersed new content, or when resuming after interruptions

## 🚀 Usage Examples

### Basic Usage (FINISH Mode - Default)
```bash
# Run with default behavior (stops on duplicates)
python3.11 scripts/fast_generation_downloader.py

# Explicitly specify FINISH mode
python3.11 scripts/fast_generation_downloader.py --mode finish
```

### SKIP Mode Usage
```bash
# Run with SKIP mode (continues past duplicates)
python3.11 scripts/fast_generation_downloader.py --mode skip

# Use custom config with SKIP mode
python3.11 scripts/fast_generation_downloader.py --config custom_config.json --mode skip

# Short form
python3.11 scripts/fast_generation_downloader.py -m skip -c custom_config.json
```

### Scan Only Mode
```bash
# Just scan existing files without downloading (useful for debugging)
python3.11 scripts/fast_generation_downloader.py --scan-only
python3.11 scripts/fast_generation_downloader.py -s
```

## 📁 Configuration Files

### Default Configuration Files
1. **`fast_generation_config.json`** - FINISH mode configuration
2. **`fast_generation_skip_config.json`** - Pre-configured SKIP mode

### Manual Configuration
To create a SKIP mode config manually, add these parameters to your `start_generation_downloads` action:

```json
{
  "type": "start_generation_downloads",
  "value": {
    "_comment_skip_mode_settings": "SKIP MODE: Continue past duplicates",
    "stop_on_duplicate": false,
    "duplicate_mode": "skip", 
    "skip_duplicates": true,
    "duplicate_check_enabled": true,
    "creation_time_comparison": true,
    
    "max_downloads": 100,
    "downloads_folder": "/path/to/downloads",
    "logs_folder": "/path/to/logs"
  }
}
```

## 🎯 Command Line Arguments

```
usage: fast_generation_downloader.py [-h] [--config CONFIG] [--mode {skip,finish}] [--scan-only]

Fast Generation Downloader with SKIP/FINISH mode support

optional arguments:
  -h, --help            show this help message and exit
  --config CONFIG, -c CONFIG
                        Path to configuration file (default: fast_generation_config.json)
  --mode {skip,finish}, -m {skip,finish}
                        Duplicate handling mode: "skip" continues past duplicates, "finish" stops on duplicates (default: finish)
  --scan-only, -s       Only scan existing files and exit (useful for debugging)
```

## 🔧 How It Works

### Automatic Configuration Modification
When you specify `--mode skip`, the script automatically modifies your configuration:

```python
# These settings are applied automatically:
"stop_on_duplicate": False     # Don't stop on duplicates
"duplicate_mode": "skip"       # Use SKIP mode
"skip_duplicates": True        # Skip over duplicates
```

### File Scanning
The script scans your downloads folder for existing files and extracts creation times:
```
🔍 Scanning existing files in: /downloads/vids
   📄 Found: video_2025-08-27-02-20-06_gen_#000000001.mp4 -> 2025-08-27-02-20-06
   📄 Found: video_2025-08-27-05-15-30_gen_#000000002.mp4 -> 2025-08-27-05-15-30
✅ Found 45 existing files
```

### Duplicate Detection
- **FINISH Mode**: Automation stops when it encounters a duplicate
- **SKIP Mode**: Automation logs the duplicate and continues to next generation

## 📊 Output Examples

### FINISH Mode Output
```
🔄 Duplicate Mode: FINISH
📌 Will stop when reaching previously downloaded content
🛑 STOPPING: Duplicate creation time detected (27 Aug 2025 02:20:06)
🔄 All newer files have already been downloaded
✅ Automation completed in 45.2s!
```

### SKIP Mode Output
```
🔄 Duplicate Mode: SKIP
📌 Will skip duplicates and continue searching for new generations
⏭️  SKIPPING: Duplicate detected, continuing search for new generations
📥 New generation found: 27 Aug 2025 08:30:15
🎉 Downloaded 12 new files, skipped 8 duplicates!
✅ Automation completed in 78.5s!
```

## 🎯 Use Cases

### Daily Downloads (FINISH Mode)
```bash
# Perfect for regular daily downloads
python3.11 scripts/fast_generation_downloader.py --mode finish
```
- Downloads new content since last run
- Stops efficiently when reaching old content
- Faster execution for regular maintenance

### Recovery/Resume Downloads (SKIP Mode)
```bash
# Perfect when resuming after interruptions
python3.11 scripts/fast_generation_downloader.py --mode skip
```
- Continues past already downloaded content
- Finds new generations interspersed with old ones
- Ideal for galleries with mixed chronology

### Debugging/Analysis (Scan Only)
```bash
# Check what files you already have
python3.11 scripts/fast_generation_downloader.py --scan-only
```
- Shows existing files and creation times
- No downloads performed
- Useful for understanding current state

## 🔍 Configuration Integration

The SKIP mode integrates seamlessly with existing configuration features:
- ✅ **Chronological Logging**: Entries still sorted by Creation Time
- ✅ **Enhanced Naming**: File naming conventions preserved
- ✅ **Placeholder IDs**: `#999999999` for new entries
- ✅ **Metadata Extraction**: Full prompt and metadata capture
- ✅ **Error Handling**: Robust duplicate detection and recovery

## 📈 Performance Comparison

| Mode | Speed | Use Case | Best For |
|------|-------|----------|----------|
| **FINISH** | ⚡ Fast | Regular downloads | Daily maintenance |
| **SKIP** | 🔄 Thorough | Recovery downloads | Mixed galleries |

## 🚨 Important Notes

1. **Backup First**: Always backup your logs folder before switching modes
2. **Config Compatibility**: Both modes work with existing configuration files
3. **Log Format**: Both modes use the same chronological log format
4. **Performance**: SKIP mode takes longer but finds more scattered content

## 📚 Related Documentation

- [Chronological Logging Guide](CHRONOLOGICAL_LOGGING_GUIDE.md)
- [Generation Download Guide](GENERATION_DOWNLOAD_GUIDE.md)
- [Duplicate Detection Guide](DUPLICATE_DETECTION_GUIDE.md)

---

*Last Updated: August 2025*
*Version: 2.0.0*
*Status: Production Ready*