# Enhanced File Naming System Guide

## Overview

The Generation Download Automation now supports **enhanced descriptive file naming** that replaces sequential numbering (#000000001.mp4) with meaningful filenames that include metadata like media type, creation date, and custom identifiers.

## 🏷️ New Naming Convention

### **Format Structure**
```
<media_type>_<creation_date>_<unique_id>.<extension>
```

### **Components**
- **media_type**: `vid` (video), `img` (image), `aud` (audio), `file` (other)
- **creation_date**: Formatted date from generation metadata 
- **unique_id**: User-configurable identifier for project/batch identification
- **extension**: Original file extension

### **Examples**
```
Sequential (Old):    #000000001.mp4, #000000002.mp4, #000000003.jpg
Descriptive (New):   vid_2025-08-24-14-35-22_initialT.mp4
                     vid_2025-08-24-14-40-15_initialT.mp4  
                     img_2025-08-24-14-45-33_initialT.jpg
```

## 🔧 Configuration

### **Basic Configuration**
```json
{
    "use_descriptive_naming": true,
    "unique_id": "initialT",
    "naming_format": "{media_type}_{creation_date}_{unique_id}",
    "date_format": "%Y-%m-%d-%H-%M-%S"
}
```

### **Configuration Parameters**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `use_descriptive_naming` | bool | `true` | Enable enhanced naming |
| `unique_id` | string | `"gen"` | Custom identifier for batch |
| `naming_format` | string | `"{media_type}_{creation_date}_{unique_id}"` | Filename template |
| `date_format` | string | `"%Y-%m-%d-%H-%M-%S"` | Date formatting |

### **Advanced Templates**

#### **Minimal Template**
```json
{
    "naming_format": "{media_type}_{unique_id}",
    "unique_id": "batch_001"
}
```
**Output**: `vid_batch_001.mp4`

#### **Date-Only Template**  
```json
{
    "naming_format": "{creation_date}_{media_type}",
    "date_format": "%Y%m%d_%H%M%S"
}
```
**Output**: `20250824_143522_vid.mp4`

#### **Custom Order Template**
```json
{
    "naming_format": "{unique_id}_{media_type}_{creation_date}",
    "unique_id": "project_alpha",
    "date_format": "%d-%m-%Y"
}
```
**Output**: `project_alpha_vid_24-08-2025.mp4`

## 🎬 Media Type Detection

### **Automatic Detection**
Media type is automatically determined from file extension:

| Extensions | Media Type | Code |
|------------|------------|------|
| `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`, etc. | Video | `vid` |
| `.jpg`, `.png`, `.gif`, `.webp`, `.bmp`, etc. | Image | `img` |
| `.mp3`, `.wav`, `.flac`, `.aac`, `.ogg`, etc. | Audio | `aud` |
| Unknown extensions | Generic file | `file` |

### **Supported Extensions**

#### **Video**: 
`mp4`, `avi`, `mov`, `mkv`, `webm`, `wmv`, `flv`, `mpg`, `mpeg`, `m4v`

#### **Image**: 
`jpg`, `jpeg`, `png`, `gif`, `bmp`, `tiff`, `tif`, `webp`, `svg`, `ico`

#### **Audio**: 
`mp3`, `wav`, `flac`, `aac`, `ogg`, `wma`, `m4a`, `opus`, `aiff`

## 📅 Date Parsing & Formatting

### **Input Date Formats**
The system automatically parses multiple date formats from webpage metadata:

```
24 Aug 2025 14:35:22    → 2025-08-24-14-35-22
2025-08-24 14:35:22     → 2025-08-24-14-35-22
24/08/2025 14:35:22     → 2025-08-24-14-35-22
08/24/2025 14:35:22     → 2025-08-24-14-35-22
2025-08-24              → 2025-08-24-00-00-00
24 Aug 2025             → 2025-08-24-00-00-00
```

### **Output Date Formats**

| Format Code | Example | Description |
|-------------|---------|-------------|
| `%Y-%m-%d-%H-%M-%S` | `2025-08-24-14-35-22` | ISO-like with hyphens |
| `%Y%m%d_%H%M%S` | `20250824_143522` | Compact format |
| `%d-%m-%Y` | `24-08-2025` | European date only |
| `%m-%d-%Y` | `08-24-2025` | US date only |
| `%Y-%m-%d` | `2025-08-24` | ISO date only |

### **Fallback Handling**
- **Unknown Date**: Uses current timestamp
- **Parse Errors**: Falls back to current timestamp  
- **Empty Date**: Uses current timestamp

## 🚀 Usage Examples

### **Basic Implementation**
```python
from src.utils.generation_download_manager import (
    GenerationDownloadManager,
    GenerationDownloadConfig
)

# Configure enhanced naming
config = GenerationDownloadConfig(
    downloads_folder="/path/to/downloads",
    use_descriptive_naming=True,
    unique_id="project_demo",
    naming_format="{media_type}_{creation_date}_{unique_id}",
    date_format="%Y-%m-%d-%H-%M-%S"
)

manager = GenerationDownloadManager(config)
results = await manager.run_download_automation(page)
```

### **Project-Specific Batches**
```python
# Different unique IDs for different projects
configs = {
    "marketing": GenerationDownloadConfig(unique_id="marketing_Q3"),
    "development": GenerationDownloadConfig(unique_id="dev_prototype"), 
    "research": GenerationDownloadConfig(unique_id="research_v2")
}
```

### **Time-Based Organization**
```python
# Organize by date hierarchy
config = GenerationDownloadConfig(
    naming_format="{creation_date}_{media_type}_{unique_id}",
    date_format="%Y-%m-%d",  # Date first for chronological sorting
    unique_id="daily_batch"
)
```

## 🔄 Backward Compatibility

### **Legacy Mode**
Set `use_descriptive_naming: false` to revert to sequential naming:

```json
{
    "use_descriptive_naming": false,
    "id_format": "#{:09d}"  
}
```
**Output**: `#000000001.mp4`, `#000000002.mp4`, etc.

### **Hybrid Approach**  
The system automatically falls back to sequential naming if:
- Descriptive naming is disabled
- Date parsing fails and fallback is configured
- Template formatting encounters errors

## 🛡️ File Safety Features

### **Duplicate Handling**
If a file with the same name exists, automatic numbering is added:
```
vid_2025-08-24-14-35-22_test.mp4      (original)
vid_2025-08-24-14-35-22_test_1.mp4    (duplicate 1)
vid_2025-08-24-14-35-22_test_2.mp4    (duplicate 2)
```

### **Filename Sanitization**
Invalid characters are automatically replaced:
```
Original: vid_2025/08/24_test<file>.mp4
Sanitized: vid_2025_08_24_test_file_.mp4
```

**Replaced Characters**: `<>:"/\|?*` → `_`

### **Length Limits**
Filenames are truncated to 200 characters to ensure filesystem compatibility while preserving the extension.

## 📋 Complete Configuration Example

```json
{
    "_comment": "Enhanced Naming Configuration Example",
    
    "downloads_folder": "/home/user/downloads/generations",
    "logs_folder": "/home/user/logs",
    "max_downloads": 50,
    
    "use_descriptive_naming": true,
    "unique_id": "initialT",
    "naming_format": "{media_type}_{creation_date}_{unique_id}",
    "date_format": "%Y-%m-%d-%H-%M-%S",
    
    "scroll_batch_size": 10,
    "scroll_amount": 600,
    
    "thumbnail_container_selector": ".thumsInner",
    "image_to_video_text": "Image to video",
    "creation_time_text": "Creation Time",
    "download_no_watermark_text": "Download without Watermark",
    
    "_example_output": [
        "vid_2025-08-24-14-35-22_initialT.mp4",
        "vid_2025-08-24-14-40-15_initialT.mp4", 
        "img_2025-08-24-14-45-33_initialT.jpg"
    ]
}
```

## 🧪 Testing

### **Run Naming Tests**
```bash
python3.11 examples/test_enhanced_naming.py
```

This test verifies:
- ✅ Media type detection for all supported formats
- ✅ Date parsing from multiple input formats  
- ✅ Template formatting with different configurations
- ✅ Legacy fallback functionality
- ✅ Filename sanitization and safety features

### **Expected Test Output**
```
🏷️ Testing Enhanced File Naming System
✅ Generated: vid_2025-08-24-14-35-22_initialT.mp4
✅ Media type correct: vid
✅ Unique ID included: initialT

🎬 Testing Media Type Detection  
✅ .mp4 → vid  (expected: vid)
✅ .png → img  (expected: img)
✅ .mp3 → aud  (expected: aud)
```

## 🎯 Best Practices

### **Unique ID Strategies**
- **Project-based**: `"project_alpha"`, `"marketing_q3"`, `"research_v2"`
- **Date-based**: `"2025_08_24"`, `"aug2025"`, `"week34"`
- **Sequential**: `"batch_001"`, `"series_a"`, `"run_01"`
- **User-based**: `"john_doe"`, `"team_design"`, `"client_abc"`

### **Naming Format Patterns**
```python
# Chronological sorting
"{creation_date}_{media_type}_{unique_id}"

# Type-based organization  
"{media_type}_{unique_id}_{creation_date}"

# Project-focused
"{unique_id}_{creation_date}_{media_type}"
```

### **Date Format Selection**
- **Sortable**: `%Y-%m-%d-%H-%M-%S` (2025-08-24-14-35-22)
- **Compact**: `%Y%m%d%H%M%S` (20250824143522)
- **Readable**: `%d_%b_%Y_%H_%M` (24_Aug_2025_14_35)

## 🔗 Integration

The enhanced naming system integrates seamlessly with existing features:

- **Infinite Scroll**: Works with unlimited downloads
- **Metadata Extraction**: Uses real creation dates from webpage
- **Progress Logging**: Logs enhanced filenames in generation_downloads.txt
- **Error Recovery**: Falls back gracefully to sequential naming
- **Stop Functionality**: Preserves naming consistency during interruptions

## 📈 Benefits

### **Before (Sequential)**
```
#000000001.mp4  ← What is this?
#000000002.mp4  ← When was it created?  
#000000003.jpg  ← What project is this for?
```

### **After (Descriptive)**
```
vid_2025-08-24-14-35-22_initialT.mp4  ← Video, Aug 24 2025 2:35 PM, Project initialT
vid_2025-08-24-14-40-15_initialT.mp4  ← Video, Aug 24 2025 2:40 PM, Project initialT
img_2025-08-24-14-45-33_initialT.jpg  ← Image, Aug 24 2025 2:45 PM, Project initialT
```

✅ **Instant identification** of content type and creation time  
✅ **Project organization** through unique identifiers  
✅ **Chronological sorting** in file explorers  
✅ **Batch management** for different projects/clients  
✅ **Professional workflow** with meaningful file organization

The enhanced naming system transforms file management from cryptic sequential numbers into a professional, organized, and immediately understandable file structure.