# Download Management Guide

## Overview

The enhanced download management system provides comprehensive file download handling for automated web tasks. This system solves common download issues with Playwright/Chromium automation and ensures files are properly saved and accessible.

## The Problem

When using browser automation tools like Playwright, downloads often fail to work as expected:

1. **Download Interception**: Playwright intercepts downloads and requires explicit handling
2. **File Location**: Downloads don't go to the expected system Downloads folder
3. **File Access**: Downloaded files are often inaccessible or in temporary locations
4. **Organization**: No automatic file organization or management
5. **Monitoring**: No way to track download progress or completion

## The Solution

Our enhanced download management system addresses all these issues:

### ✅ **Proper File Location**
- Downloads go to `/home/olereon/workspace/github.com/olereon/automaton/downloads/vids` by default
- Configurable base download path
- Automatic directory creation

### ✅ **File Organization**
- Organize by date (YYYY-MM-DD folders)
- Organize by file type (videos, images, documents, etc.)
- Automatic duplicate filename handling

### ✅ **Download Tracking**
- Comprehensive download logging
- File integrity verification
- Download completion detection
- Progress monitoring

### ✅ **Error Handling**
- Fallback to basic download method
- Retry mechanisms
- Graceful error recovery

## Usage

### Basic Usage in Automation Config

```json
{
  "name": "Video Download Automation",
  "url": "https://your-site.com",
  "actions": [
    {
      "type": "download_file",
      "selector": ".download-button",
      "value": "my_video.mp4",
      "timeout": 60000,
      "description": "Download generated video"
    }
  ]
}
```

### Advanced Configuration

The download manager can be configured with custom settings:

```python
from utils.download_manager import DownloadManager, DownloadConfig

# Custom configuration
config = DownloadConfig(
    base_download_path="/home/olereon/Downloads/automaton_vids",
    organize_by_date=True,
    organize_by_type=True,
    max_wait_time=300,  # 5 minutes max wait
    auto_rename_duplicates=True,
    verify_downloads=True,
    create_download_log=True
)

download_manager = DownloadManager(config)
```

## Download Organization

### By Date (organize_by_date=True)
```
/home/olereon/Downloads/automaton_vids/
├── 2024-12-20/
│   ├── video1.mp4
│   └── image1.jpg
├── 2024-12-21/
│   └── document1.pdf
└── download_log.json
```

### By Type (organize_by_type=True)
```
/home/olereon/Downloads/automaton_vids/
├── videos/
│   ├── video1.mp4
│   └── video2.avi
├── images/
│   └── image1.jpg
├── documents/
│   └── document1.pdf
└── other/
    └── unknown_file.bin
```

### Combined Organization
```
/home/olereon/Downloads/automaton_vids/
├── 2024-12-20/
│   ├── videos/
│   │   └── video1.mp4
│   ├── images/
│   │   └── image1.jpg
│   └── documents/
│       └── document1.pdf
└── download_log.json
```

## Download Actions

### Standard Download Action

```json
{
  "type": "download_file",
  "selector": ".download-btn",
  "timeout": 30000,
  "description": "Download file"
}
```

### Download with Custom Filename

```json
{
  "type": "download_file",
  "selector": ".download-btn",
  "value": "custom_filename.mp4",
  "timeout": 60000,
  "description": "Download with custom name"
}
```

### Download with Long Timeout

```json
{
  "type": "download_file",
  "selector": ".download-btn",
  "timeout": 300000,
  "description": "Download large file (5 min timeout)"
}
```

## Download Monitoring

### Download Log

The system automatically creates a download log at:
`/home/olereon/Downloads/automaton_vids/download_log.json`

Example log entry:
```json
{
  "filename": "video_2024-12-20_001.mp4",
  "original_filename": "generated_video.mp4",
  "file_path": "/home/olereon/Downloads/automaton_vids/2024-12-20/videos/video_2024-12-20_001.mp4",
  "file_size": 15728640,
  "download_time": "2024-12-20T14:30:45.123456",
  "source_url": "https://example.com/generate",
  "mime_type": "video/mp4",
  "checksum": "a1b2c3d4e5f6...",
  "status": "completed"
}
```

### Getting Download Summary

```python
# Get download summary
summary = engine.download_manager.get_downloads_summary()

print(f"Total downloads: {summary['total_downloads']}")
print(f"Completed: {summary['completed']}")
print(f"Failed: {summary['failed']}")
print(f"Total size: {summary['total_size_mb']} MB")
```

## Configuration Options

### DownloadConfig Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_download_path` | str | `/home/olereon/Downloads/automaton_vids` | Base directory for downloads |
| `organize_by_date` | bool | `True` | Create date-based subdirectories |
| `organize_by_type` | bool | `False` | Create file-type subdirectories |
| `max_wait_time` | int | `300` | Maximum wait time in seconds |
| `check_interval` | int | `1` | Download progress check interval |
| `auto_rename_duplicates` | bool | `True` | Automatically rename duplicate files |
| `verify_downloads` | bool | `True` | Verify download integrity |
| `create_download_log` | bool | `True` | Create detailed download logs |

## File Type Recognition

The system automatically recognizes file types:

### Video Files
- Extensions: `.mp4`, `.avi`, `.mkv`, `.mov`, `.wmv`, `.flv`
- MIME types containing: `video`

### Image Files
- Extensions: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg`
- MIME types containing: `image`

### Document Files
- Extensions: `.pdf`, `.doc`, `.docx`, `.txt`, `.rtf`
- MIME types containing: `document`, `text`

### Archive Files
- Extensions: `.zip`, `.rar`, `.7z`, `.tar`, `.gz`
- MIME types containing: `archive`, `compressed`

## Troubleshooting

### Common Issues

#### 1. Downloads Not Found
**Symptoms**: Download appears to succeed but file not found
**Solution**: Check the organized download path:
```bash
ls -la /home/olereon/Downloads/automaton_vids/$(date +%Y-%m-%d)/
```

#### 2. Permission Denied
**Symptoms**: Download fails with permission error
**Solution**: Ensure download directory has write permissions:
```bash
chmod 755 /home/olereon/Downloads/automaton_vids/
```

#### 3. Download Timeout
**Symptoms**: Large files fail to download
**Solution**: Increase timeout in action configuration:
```json
{
  "type": "download_file",
  "selector": ".download-btn",
  "timeout": 600000,  // 10 minutes
  "description": "Download large file"
}
```

#### 4. Duplicate Files
**Symptoms**: Downloads overwrite existing files
**Solution**: Enable auto-rename (default behavior):
```python
config = DownloadConfig(auto_rename_duplicates=True)
```

### Debug Information

Enable verbose logging to debug download issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check download manager status:
```python
if engine.download_manager:
    summary = engine.download_manager.get_downloads_summary()
    print(json.dumps(summary, indent=2))
```

### Fallback Behavior

If the enhanced download manager fails, the system automatically falls back to the basic download method:

1. Downloads go to project `downloads/` directory
2. Basic filename sanitization
3. No organization or advanced features
4. Still provides download completion

## Integration Examples

### CLI Usage

```bash
# Run automation with download
python automaton-cli.py run -c download_config.json

# Check downloads after completion
ls -la /home/olereon/Downloads/automaton_vids/$(date +%Y-%m-%d)/
```

### Programmatic Usage

```python
from core.engine import WebAutomationEngine, AutomationSequenceBuilder

# Build automation with download
builder = AutomationSequenceBuilder("Download Task", "https://example.com")
config = (builder
    .add_wait_for_element("#download-ready")
    .add_download_file(".download-btn", "my_file.mp4")
    .build())

# Run automation
engine = WebAutomationEngine(config)
results = await engine.run_automation()

# Check download results
if engine.download_manager:
    summary = engine.download_manager.get_downloads_summary()
    for download in summary['downloads']:
        print(f"Downloaded: {download['file_path']}")
```

### Scheduler Integration

```json
{
  "config_files": [
    "workflows/download_task1.json",
    "workflows/download_task2.json"
  ],
  "success_wait_time": 300,
  "scheduled_time": "02:00:00",
  "log_file": "logs/download_scheduler.log"
}
```

## Best Practices

### 1. Timeout Management
- Use appropriate timeouts based on expected file sizes
- Video files: 60-300 seconds
- Images: 10-30 seconds
- Documents: 10-60 seconds

### 2. File Organization
- Enable date organization for time-based tracking
- Enable type organization for large volumes of mixed files
- Use custom base paths for different projects

### 3. Error Handling
- Always check download status in automation results
- Implement retry logic for critical downloads
- Monitor download logs for patterns

### 4. Storage Management
- Regularly clean up old downloads
- Monitor disk space usage
- Implement archival strategies for long-term storage

### 5. Security
- Verify download checksums for critical files
- Scan downloaded files for malware
- Use secure download URLs (HTTPS)

## API Reference

### DownloadManager Class

```python
class DownloadManager:
    def __init__(self, config: DownloadConfig = None)
    
    async def handle_playwright_download(
        self, page, download_trigger_selector: str, 
        expected_filename: str = None, 
        timeout: int = None
    ) -> DownloadInfo
    
    async def handle_direct_download(
        self, page, download_url: str, 
        filename: str = None
    ) -> DownloadInfo
    
    def get_downloads_summary(self) -> Dict[str, Any]
    
    async def cleanup_failed_downloads(self)
```

### Factory Function

```python
def create_download_manager(
    base_path: str = None, 
    organize_by_date: bool = True,
    organize_by_type: bool = False
) -> DownloadManager
```

## Summary

The enhanced download management system provides:

- ✅ Reliable file downloads to accessible locations
- ✅ Automatic file organization and management
- ✅ Comprehensive download tracking and logging
- ✅ Robust error handling and fallback mechanisms
- ✅ Configurable behavior for different use cases
- ✅ Integration with existing automation workflows

This system ensures that your automated downloads work consistently and files are always accessible where you expect them to be.