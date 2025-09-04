# Start From Feature Guide

## Overview

The `start_from` feature allows you to begin generation downloads from a specific datetime, rather than starting from the beginning of the gallery. This is particularly useful when you want to:

- Resume downloads from a specific point after interruption
- Download only generations created after a certain time
- Skip older content and focus on newer generations
- Start downloads from a known generation datetime

## How It Works

The `start_from` feature searches through the gallery containers to find a generation with the specified creation datetime. When found:

1. **Target Location**: The system positions itself at the generation with the specified datetime
2. **Next Generation Start**: Downloads begin from the **next generation** after the target
3. **Enhanced Search**: Uses the same robust container detection as boundary scanning
4. **Extensive Scrolling**: Supports up to 100 scroll attempts to find the target datetime

## Usage

### Command Line Interface

```bash
# Basic usage with start_from
python3.11 scripts/fast_generation_downloader.py --start-from "03 Sep 2025 16:15:18"

# Combined with SKIP mode
python3.11 scripts/fast_generation_downloader.py --mode skip --start-from "03 Sep 2025 16:15:18"

# With custom config file
python3.11 scripts/fast_generation_downloader.py --config my_config.json --start-from "03 Sep 2025 16:15:18"
```

### GUI Interface

1. **Add Action**: Create a "Start Generation Downloads" action
2. **Fill Form Fields**:
   - Max Downloads: Set desired limit
   - Downloads Folder: Choose destination directory
   - Completed Task Selector: Set selector for navigation
   - **Start From Datetime**: Enter target datetime (optional)
3. **Format**: Use the exact format shown: `DD MMM YYYY HH:MM:SS`
4. **Example**: `03 Sep 2025 16:15:18`

### Configuration File

```json
{
  "actions": [
    {
      "type": "start_generation_downloads",
      "value": {
        "max_downloads": 100,
        "downloads_folder": "/path/to/downloads",
        "completed_task_selector": "div[id$='__8']",
        "start_from": "03 Sep 2025 16:15:18"
      }
    }
  ]
}
```

## DateTime Format Requirements

### Strict Format
- **Pattern**: `DD MMM YYYY HH:MM:SS`
- **Example**: `03 Sep 2025 16:15:18`

### Format Breakdown
- `DD` - Day (01-31, with or without leading zero)
- `MMM` - Month abbreviation (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug, Sep, Oct, Nov, Dec)
- `YYYY` - Full year (e.g., 2025)
- `HH:MM:SS` - Time in 24-hour format

### Valid Examples
```
03 Sep 2025 16:15:18
1 Jan 2025 09:30:45
15 Dec 2024 23:59:59
```

### Invalid Examples
```
2025-09-03 16:15:18    ❌ Wrong date format
Sep 03 2025 16:15:18   ❌ Wrong order
03 September 2025      ❌ Full month name
03 Sep 25 16:15        ❌ Short year, missing seconds
```

## Search Process

### 1. Validation
- Checks datetime format before starting search
- Returns error immediately if format is invalid

### 2. Container Scanning  
- Scans existing containers on the gallery page
- Extracts metadata using enhanced extraction methods
- Compares creation times for exact matches

### 3. Scrolling Search
- If target not found in visible containers
- Scrolls down to load more containers
- Supports up to 100 scroll attempts
- Waits for DOM updates between scrolls

### 4. Target Found
- Clicks the target container to position gallery
- System is ready to download from next generation
- Logs success with container index and details

### 5. Target Not Found
- Logs warning after exhausting search attempts
- Falls back to starting from beginning of gallery
- Downloads proceed normally from default start position

## Integration with Other Features

### SKIP Mode Compatibility
```bash
# Start from specific datetime and skip duplicates
python3.11 scripts/fast_generation_downloader.py --mode skip --start-from "03 Sep 2025 16:15:18"
```

### FINISH Mode Compatibility  
```bash
# Start from specific datetime and stop on duplicates
python3.11 scripts/fast_generation_downloader.py --mode finish --start-from "03 Sep 2025 16:15:18"
```

### Enhanced Boundary Detection
- Uses same robust container detection as boundary scanning
- Benefits from enhanced metadata extraction
- Includes retry logic for failed extractions
- Supports DOM timing and wait strategies

## Logging and Debugging

### Success Messages
```
🎯 START_FROM MODE: Searching for generation with datetime '03 Sep 2025 16:15:18'
   🔍 Using enhanced container detection for start_from search...
   📊 Initial containers found: 20
   🎯 TARGET FOUND: Container 45 matches '03 Sep 2025 16:15:18'
      📝 Prompt: The camera begins with a low-angle medium shot, framing the...
   🖱️ Clicking target container to position gallery...
✅ START_FROM: Successfully positioned at target generation
```

### Warning Messages
```
⚠️ START_FROM: Could not find generation with datetime '03 Sep 2025 16:15:18'
   Will start from the beginning of the gallery instead
```

### Error Messages
```
❌ START_FROM: Invalid datetime format '2025-09-03 16:15:18'
   Expected format: 'DD MMM YYYY HH:MM:SS' (e.g., '03 Sep 2025 16:15:18')
```

## Performance Considerations

### Search Efficiency
- **Container Scanning**: Fast metadata extraction using enhanced methods
- **Scrolling Strategy**: Optimized scroll timing with DOM wait periods
- **Memory Usage**: Minimal - processes containers incrementally
- **Network Impact**: Standard page loading, no additional API calls

### Large Galleries
- **Extensive Search**: Up to 100 scroll attempts to find target
- **Progress Tracking**: Logs container scan progress
- **Timeout Handling**: Graceful degradation if target not found
- **Resource Management**: Efficient handling of large galleries

### Search Limits
- **Maximum Scrolls**: 100 attempts (covers very large galleries)
- **Container Limit**: No hard limit - searches until found or exhausted
- **Time Limit**: Depends on gallery size and network speed
- **Fallback**: Always falls back to default start if target not found

## Troubleshooting

### Common Issues

#### 1. Invalid Format Error
**Problem**: `❌ START_FROM: Invalid datetime format`
**Solution**: Check datetime format matches `DD MMM YYYY HH:MM:SS`

#### 2. Generation Not Found
**Problem**: `⚠️ START_FROM: Could not find generation with datetime`
**Solutions**:
- Verify the datetime exists in the gallery
- Check for typos in the datetime string
- Ensure you're on the correct gallery/account
- Try a datetime that's closer to the beginning of the gallery

#### 3. Search Takes Too Long
**Problem**: Search scrolls extensively without finding target
**Solutions**:
- Use a more recent datetime (closer to gallery start)
- Check if gallery is very large (3000+ generations)
- Consider using a datetime from the log file for accuracy

#### 4. Container Click Fails
**Problem**: Target found but click fails
**Solutions**:
- Search still succeeds (system positioned correctly)
- Downloads will proceed from approximate position
- Check browser console for any JavaScript errors

### Best Practices

#### 1. Use Accurate Datetimes
- Copy datetimes from generation_downloads.txt log file
- Use datetimes from generations you know exist
- Verify format exactly matches requirements

#### 2. Combine with Other Features
- Use with SKIP mode for flexible duplicate handling
- Combine with specific max_downloads for targeted collections
- Use with enhanced logging for detailed progress tracking

#### 3. Test with Recent Generations
- Start with recent generations for faster searches
- Use generations from the first few pages when possible
- Test the feature with known good datetimes first

#### 4. Monitor Progress
- Watch logs for search progress and success/failure
- Use debug logging to see container scanning details
- Check for warning messages about fallback behavior

## Examples

### Basic Start From Usage
```bash
# Start downloads from a specific generation
python3.11 scripts/fast_generation_downloader.py --start-from "03 Sep 2025 16:15:18"
```

### Advanced Usage Scenarios
```bash
# Resume interrupted downloads from specific point
python3.11 scripts/fast_generation_downloader.py --mode skip --start-from "03 Sep 2025 16:15:18"

# Download only recent generations (last 100 after specific time)
python3.11 scripts/fast_generation_downloader.py --start-from "04 Sep 2025 08:00:00" --config limited_download.json

# Targeted download with custom config
python3.11 scripts/fast_generation_downloader.py --config custom.json --start-from "03 Sep 2025 16:15:18" --mode finish
```

### Configuration Examples
```json
{
  "actions": [
    {
      "type": "start_generation_downloads",
      "description": "Resume downloads from afternoon of Sep 3rd",
      "value": {
        "max_downloads": 200,
        "downloads_folder": "/home/user/automaton/downloads/vids",
        "completed_task_selector": "div[id$='__8']",
        "start_from": "03 Sep 2025 16:15:18",
        "duplicate_mode": "skip",
        "stop_on_duplicate": false
      }
    }
  ]
}
```

## Technical Implementation Details

### Search Algorithm
1. **Format Validation**: Regex pattern matching for datetime format
2. **Container Discovery**: Query for all thumbnail containers on page
3. **Metadata Extraction**: Enhanced extraction using multiple strategies
4. **Exact Matching**: String comparison of extracted vs target datetime
5. **Progressive Scrolling**: Load more containers if target not found
6. **Position Management**: Click target container to position gallery

### Enhanced Features Integration
- **Boundary Detection Logic**: Reuses proven container detection methods
- **Metadata Extraction**: Uses same enhanced extraction as boundary scanning
- **Error Recovery**: Graceful fallback when target not found
- **Logging Integration**: Comprehensive logging with debugging information

### Performance Optimizations
- **Incremental Processing**: Processes containers as they're found
- **DOM Timing**: Proper wait periods for dynamic content loading
- **Memory Efficient**: No storage of unnecessary container data
- **Early Termination**: Stops searching immediately when target found

This feature provides a powerful way to start generation downloads from any specific point in your gallery, with robust search capabilities and comprehensive error handling.