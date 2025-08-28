# Generation Download Automation Guide

## Overview

The Generation Download Automation system provides comprehensive functionality for automatically downloading generated content (videos, images, etc.) from web platforms with metadata tracking and file organization.

## 🚀 New Features (August 2024)

### 🛑 **Duplicate Detection System** ([Guide](DUPLICATE_DETECTION_GUIDE.md)) 
- Intelligent detection prevents re-downloading existing content
- Compares both date/time AND prompt text for accuracy
- Automatic termination when reaching previously downloaded boundary
- Configurable stop or skip behavior

### 🔄 **Infinite Scroll Support** ([Guide](INFINITE_SCROLL_GUIDE.md))
- Advanced gallery pre-loading with multiple scroll strategies
- Automatically reveals all thumbnails beyond initial viewport
- Handles Playwright-specific scroll limitations
- Processes 80%+ more content than basic scrolling

### 🎯 **Start-From Navigation** 
- Begin downloads from any specified thumbnail number
- Navigate directly to desired starting position
- Efficient for incremental downloads
- Works with landmark-based navigation

### 🏷️ **Enhanced Descriptive Naming** ([Guide](ENHANCED_NAMING_GUIDE.md))
- Replace sequential numbers with descriptive filenames
- Format: `{media_type}_{creation_date}_{unique_id}.{extension}`
- Automatic media type detection (vid/img/aud)
- Flexible date formatting and project identifiers

### 🎯 **Text-Based Element Detection** ([Guide](ENHANCED_GENERATION_DOWNLOAD_GUIDE.md))
- Robust element finding using text landmarks
- Handles dynamic CSS classes and changing selectors
- Multiple fallback strategies for reliability
- Full prompt text extraction without truncation

### 👍 **Overlay Handling**
- Automatic closure of thumbs-up feedback overlays
- Prevents automation blocking from popup dialogs
- Smart detection and dismissal strategies

## Core Features

### ✅ **Automated Download Process**
- Navigate to completed generation tasks
- Iterate through thumbnail galleries with infinite scroll
- Extract metadata (date, full prompt) from each generation
- Download without watermarks
- Enhanced descriptive or sequential file naming

### ✅ **Intelligent File Management**
- Descriptive naming: `vid_2025-08-24-14-35-22_project.mp4`
- Legacy sequential IDs: `#000000001.mp4` (optional)
- Download verification and integrity checking
- Organized folder structure with project identifiers
- Duplicate handling with automatic numbering

### ✅ **Comprehensive Logging**
- Structured text logs with generation metadata
- Track generation date, full prompt text, file ID, and download timestamp
- Progress monitoring with scroll statistics
- Status tracking across sessions

### ✅ **Error Handling & Recovery**
- Retry mechanisms for failed downloads
- Graceful error handling with scroll failures
- Stop conditions and user control
- Resume capability with state preservation

## Quick Start

### 1. Basic Configuration

```json
{
  "name": "Generation Download Automation",
  "url": "https://your-generation-platform.com",
  "actions": [
    {
      "type": "login",
      "value": {
        "username": "your_username",
        "password": "your_password",
        "username_selector": "#username",
        "password_selector": "#password",
        "submit_selector": "#login-button"
      },
      "timeout": 30000,
      "description": "Login to platform"
    },
    {
      "type": "start_generation_downloads",
      "value": {
        "max_downloads": 50,
        "downloads_folder": "/path/to/downloads",
        "completed_task_selector": "div[id$='__9']"
      },
      "timeout": 300000,
      "description": "Start automated downloads"
    }
  ]
}
```

### 2. Enhanced Configuration with New Features

```json
{
  "name": "Enhanced Generation Download",
  "actions": [{
    "type": "start_generation_downloads",
    "value": {
      "max_downloads": 100,
      "downloads_folder": "/path/to/downloads",
      
      "_comment": "Enhanced Naming Configuration",
      "use_descriptive_naming": true,
      "unique_id": "project_alpha",
      "naming_format": "{media_type}_{creation_date}_{unique_id}",
      "date_format": "%Y-%m-%d-%H-%M-%S",
      
      "_comment": "Infinite Scroll Configuration",
      "scroll_batch_size": 10,
      "scroll_amount": 600,
      "scroll_wait_time": 2000,
      
      "_comment": "Text-Based Element Finding",
      "image_to_video_text": "Image to video",
      "creation_time_text": "Creation Time",
      "download_no_watermark_text": "Download without Watermark",
      
      "_comment": "Duplicate Detection Configuration",
      "duplicate_check_enabled": true,
      "stop_on_duplicate": true,
      "creation_time_comparison": true,
      
      "_comment": "Start-From Navigation",
      "start_from_thumbnail": 1
    }
  }]
}
```

### 3. Run via GUI
1. Open the Automaton GUI
2. Create a new automation configuration
3. Add "Start Generation Downloads" action
4. Configure download settings with enhanced naming
5. Enable infinite scroll for large galleries
6. Run the automation

### 4. Run via CLI
```bash
# Basic demo
python3.11 examples/generation_download_demo.py

# Test enhanced naming
python3.11 examples/test_enhanced_naming.py

# Test infinite scroll
python3.11 examples/test_infinite_scroll.py
```

## Action Types

### START_GENERATION_DOWNLOADS

Starts the automated generation download process with enhanced features.

**Core Configuration:**
- `max_downloads`: Maximum number of files to download (default: 50)
- `downloads_folder`: Target folder for downloaded files
- `logs_folder`: Folder for log files (default: `/logs`)
- `download_timeout`: Timeout for individual downloads (default: 120000ms)
- `verification_timeout`: Timeout for file verification (default: 30000ms)
- `retry_attempts`: Number of retry attempts for failed downloads (default: 3)

**Enhanced Naming Options:**
- `use_descriptive_naming`: Enable descriptive filenames (default: true)
- `unique_id`: Project/batch identifier (default: "gen")
- `naming_format`: Filename template (default: `"{media_type}_{creation_date}_{unique_id}"`)
- `date_format`: Date formatting (default: `"%Y-%m-%d-%H-%M-%S"`)

**Infinite Scroll Options:**
- `scroll_batch_size`: Downloads before scrolling (default: 10)
- `scroll_amount`: Pixels to scroll (default: 600)
- `scroll_wait_time`: Wait after scroll in ms (default: 2000)
- `max_scroll_attempts`: Max scroll retries (default: 5)

**Selectors (customize for your platform):**
- `thumbnail_container_selector`: Container for thumbnails (default: `".thumsInner"`)
- `thumbnail_selector`: Individual thumbnails (default: `".thumbnail-item, .thumsItem"`)
- `completed_task_selector`: Completed tasks section (default: `"div[id$='__8']"`)
- `download_no_watermark_selector`: Selector for "no watermark" option
- `generation_date_selector`: Selector for generation date element
- `prompt_selector`: Selector for prompt text element

### STOP_GENERATION_DOWNLOADS

Stops the currently running generation download process.

### CHECK_GENERATION_STATUS

Returns the current status of generation downloads including:
- Number of downloads completed
- Current thumbnail index
- Whether the process should stop
- Log file path and downloads folder

## File Organization

### Download Structure
```
/downloads/vids/
├── #000000001.mp4
├── #000000002.mp4
├── #000000003.mp4
└── ...
```

### Log File Structure
```
/logs/generation_downloads.txt

#000000001
2025-08-21 03:16:29
[Text of the prompt used for generation]
========================================
#000000002
2025-08-21 03:17:15
[Another prompt text]
========================================
```

## Platform Integration

### Required Selectors

To use this system with your platform, you need to identify the correct CSS selectors:

1. **Completed Task Selector**: Element that navigates to completed generations
   - Example: `"div[id$='__8']"` (9th item with ID ending in `__8`)

2. **Thumbnail Elements**: Individual thumbnail containers
   - Example: `".thumbnail-item"`, `".generation-thumb"`

3. **Download Button**: Primary download button
   - Example: `"[data-spm-anchor-id='a2ty_o02.30365920.0.i1.6daf47258YB5qi']"`

4. **No Watermark Option**: Button for watermark-free download
   - Example: `"[data-spm-anchor-id='a2ty_o02.30365920.0.i2.6daf47258YB5qi']"`

5. **Metadata Elements**:
   - Generation date: `".sc-eWXuyo.gwshYN"`
   - Prompt text: `"span[aria-describedby]"`

### Customizing for Your Platform

1. **Inspect Elements**: Use browser developer tools to find correct selectors
2. **Update Configuration**: Modify selectors in your automation config
3. **Test Individual Elements**: Verify each selector works independently
4. **Adjust Timeouts**: Set appropriate timeouts for your platform's response times

## Advanced Usage

### Custom Download Manager

```python
from utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig

# Custom configuration
config = GenerationDownloadConfig(
    downloads_folder="/custom/path",
    max_downloads=100,
    download_timeout=180000,  # 3 minutes
    verification_timeout=60000,  # 1 minute
    retry_attempts=5
)

manager = GenerationDownloadManager(config)
```

### Programmatic Usage

```python
import asyncio
from core.engine import WebAutomationEngine, AutomationConfig, Action, ActionType

async def run_downloads():
    config = AutomationConfig(
        name="Custom Download",
        url="https://platform.com",
        actions=[
            Action(
                type=ActionType.START_GENERATION_DOWNLOADS,
                value={
                    "max_downloads": 25,
                    "downloads_folder": "/downloads",
                    "completed_task_selector": "your-selector"
                },
                timeout=300000
            )
        ]
    )
    
    engine = WebAutomationEngine(config)
    results = await engine.run_automation()
    return results

# Run the automation
results = asyncio.run(run_downloads())
```

## Error Handling

### Common Issues

1. **Selector Not Found**: Update selectors to match current page structure
2. **Download Timeout**: Increase `download_timeout` for large files
3. **File Verification Failed**: Check download folder permissions
4. **Login Required**: Ensure login action precedes download action

### Debugging

1. **Enable Verbose Logging**: Set logging level to DEBUG
2. **Test Selectors**: Use browser console to test CSS selectors
3. **Check Network**: Monitor network activity during downloads
4. **Verify Permissions**: Ensure write access to download folders

## Stop Conditions

### Automatic Stop Conditions
- Maximum downloads reached
- No more thumbnails available
- Critical error encountered
- User-requested stop

### Manual Stop
```json
{
  "type": "stop_generation_downloads",
  "description": "Stop downloads"
}
```

## Browser Configuration & Performance

### 🚫 **Download Popup & Shelf Suppression** (ENHANCED)
The system now provides comprehensive suppression of ALL download UI interference:

**Chromium Launch Arguments:**
```bash
--disable-download-notification         # Disable download notification popup
--disable-notifications                # Disable all notifications  
--disable-popup-blocking               # Allow downloads without popup interference
--disable-features=DownloadBubble,DownloadBubbleV2  # Disable new download bubble UI
--disable-features=DownloadShelf       # Disable download shelf at bottom
--disable-infobars                     # Disable info bars
--no-first-run                        # Skip first run experience
```

**Chrome DevTools Protocol (CDP) Integration:**
- Sets download behavior to silent mode
- Disables download events and UI notifications
- Configures automatic download acceptance

**Active Shelf Closing Methods:**
1. **Keyboard shortcuts** - Automated Ctrl+Shift+J toggle
2. **Click dismissal** - Clicks outside download area
3. **Escape key** - Closes any open popups
4. **Element targeting** - Finds and clicks close buttons
5. **JavaScript hiding** - Dynamically hides download UI elements

**Post-Download Cleanup:**
- Automatically closes download shelf after each download
- Clears any residual download notifications
- Maintains clean browser interface throughout automation

**Benefits:**
✅ **Complete UI suppression** - No download shelf, no popups, no notifications  
✅ **Recent Downloads eliminated** - The persistent "Recent Downloads" popup is actively closed  
✅ **Uninterrupted automation** - Downloads proceed without ANY visual interference  
✅ **Clean browser UI** - Browser stays focused on content, not download management  
✅ **Professional experience** - Seamless automation without distracting UI elements

### Performance Optimization

### Best Practices
- Use reasonable `max_downloads` limits
- Set appropriate timeouts for your network speed
- Monitor disk space in download folder
- Use SSD storage for better file I/O performance
- Browser popup suppression ensures smooth download flow

### Resource Management
- Downloads are processed sequentially to avoid overwhelming the server
- File verification happens immediately after download
- Memory usage is optimized for long-running operations
- Download popups are automatically suppressed to prevent interruptions

## Security Considerations

### File Safety
- All downloads are verified for integrity
- Files are renamed using sequential IDs to prevent conflicts
- Download paths are validated to prevent directory traversal

### Platform Compliance
- Respects server rate limits
- Uses appropriate delays between requests
- Downloads only user-accessible content

## Troubleshooting

### Download Popup & Shelf Issues (ENHANCED)
**Problem:** "Recent Downloads" popup still appearing at bottom of browser
**Solution:** Enhanced shelf suppression is now implemented:
1. Browser launches with `--disable-features=DownloadShelf` argument
2. CDP protocol configures silent download mode
3. Active shelf closing after each download with multiple methods
4. JavaScript actively hides download UI elements
5. If still visible, automation will automatically close it

**Problem:** Downloads interrupted by browser popups or notifications
**Solution:** Comprehensive popup suppression is enabled:
1. Multiple Chrome flags disable all download UI
2. Keyboard shortcuts automatically close popups
3. Click dismissal and Escape key automation
4. Use headless mode for complete UI elimination

**Problem:** Downloads prompt for location or confirmation
**Solution:** The system configures automatic acceptance:
1. Browser context has `accept_downloads=True`
2. CDP sets download behavior to "allowAndName"
3. JavaScript overrides dialog functions
4. Download path is explicitly configured

### Download Failures
1. Check network connectivity
2. Verify login credentials
3. Update selectors if page structure changed
4. Increase timeout values
5. Check download folder permissions
6. **NEW:** Verify popup suppression is working properly

### Browser Configuration Issues (NEW)
**Problem:** Browser not launching with correct arguments
**Solution:** Check browser launch configuration:
1. Verify Chromium/Chrome installation
2. Check Playwright browser installation: `playwright install chromium`
3. Restart automation if browser settings not applied
4. Review console logs for launch argument errors

### Log Issues
1. Verify logs folder exists and is writable
2. Check for disk space in logs directory
3. Ensure proper file encoding (UTF-8)

### Performance Issues
1. Reduce `max_downloads` for testing
2. Increase timeout values
3. Check system resources (CPU, memory, disk)
4. Monitor network bandwidth usage
5. **NEW:** Popup suppression reduces browser overhead

## API Reference

### GenerationDownloadConfig
- `downloads_folder`: Target download directory
- `logs_folder`: Log file directory  
- `max_downloads`: Maximum files to download
- `download_timeout`: Individual download timeout
- `verification_timeout`: File verification timeout
- `retry_attempts`: Number of retry attempts

### GenerationMetadata
- `file_id`: Sequential file identifier
- `generation_date`: Date from platform
- `prompt`: Generation prompt text
- `download_timestamp`: When download completed
- `file_path`: Local file path
- `file_size`: File size in bytes

### Status Information
- `downloads_completed`: Number completed
- `current_thumbnail_index`: Current position
- `should_stop`: Stop flag status
- `max_downloads`: Configured maximum
- `log_file_path`: Path to log file
- `downloads_folder`: Download directory

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review log files for error details
3. Test with reduced `max_downloads` first
4. Verify all selectors are current