# Fast Generation Downloader

Optimized automation scripts for quick generation downloads with advanced duplicate detection and completion monitoring.

## 📁 Files

### `fast_generation_downloader.py`
Main automation script with optimized performance and duplicate detection.

### `fast_generation_config.json`
Configuration file with reduced timeouts and fast navigation settings.

## 🚀 Features

### ⚡ **Speed Optimizations**
- **Reduced Timeouts**: 5s downloads, 8s verification (vs 12s/30s in standard config)
- **Fast Navigation**: 1s waits between actions (vs 3s-4s in standard)
- **Quick Login**: 15s timeout (vs 30s in standard)
- **Optimized Scrolling**: 1s scroll wait, larger batch sizes

### 🚫 **Duplicate Detection**
- **Creation Time Comparison**: Automatically detects existing files by creation date
- **Smart Stopping**: Stops automation when duplicate detected (all newer files already downloaded)
- **File Pattern Matching**: Matches `video_YYYY-MM-DD-HH-MM-SS_gen_#NNNNNNNNN.mp4`
- **Progress Reporting**: Shows how many existing files were found

### ✅ **Download Completion Detection**
- **Real-time Monitoring**: Monitors downloads folder for new files
- **Fast Completion**: Proceeds immediately when download completes
- **Timeout Protection**: Falls back to fixed wait if completion not detected
- **Configurable Timeout**: Adjustable completion detection timeout

## 📊 Performance Improvements

| Feature | Standard Config | Fast Config | Improvement |
|---------|----------------|-------------|-------------|
| **Download Timeout** | 12,000ms | 5,000ms | **58% faster** |
| **Verification Timeout** | 30,000ms | 8,000ms | **73% faster** |
| **Login Timeout** | 30,000ms | 15,000ms | **50% faster** |
| **Page Load Wait** | 4,000ms | 2,000ms | **50% faster** |
| **Scroll Wait Time** | 2,000ms | 1,000ms | **50% faster** |
| **Max Downloads** | 16 | 50 | **212% more** |

## 🔧 Usage

### Basic Usage
```bash
cd /home/olereon/workspace/github.com/olereon/automaton/scripts
python3.11 fast_generation_downloader.py
```

### Custom Config
```bash
python3.11 fast_generation_downloader.py /path/to/custom/config.json
```

### Expected Output
```
🚀 Fast Generation Downloader
============================================================
🔍 Scanning existing files in: /path/to/downloads
✅ Found 16 existing files with 16 unique creation times
📋 Automation: Fast Generation Download Automation
🌐 URL: https://wan.video/generate
🎬 Actions: 4
⚡ Optimized for fast downloads with duplicate detection

🔥 Starting optimized automation...
✅ Browser session established with full viewport
🔍 Found 16 existing files - will stop if duplicate creation time detected
📊 Initial batch: 15 thumbnails visible
🎯 Processing thumbnail 1 (visible index: 1/15)
📥 Downloads completed: 1
✅ Download completed: video_2025-08-27-03-15-42_gen_#000000017.mp4
...
🛑 STOPPING: Duplicate creation time detected (27 Aug 2025 02:20:06)
🔄 All newer files have already been downloaded

📊 Results (Duration: 45.2s):
✅ Success: true
⚡ Actions completed: 3/4
🎯 Generation Download Results:
📥 Downloads completed: 3
⚡ Average time per download: 15.07s

🎉 Fast download completed in 45.2s!
```

## ⚙️ Configuration

### Key Settings in `fast_generation_config.json`

```json
{
  "max_downloads": 50,
  "download_timeout": 5000,
  "verification_timeout": 8000,
  "scroll_wait_time": 1000,
  "stop_on_duplicate": true,
  "duplicate_check_enabled": true,
  "download_completion_detection": true,
  "fast_navigation_mode": true
}
```

### Customization Options

**Duplicate Detection**:
- `stop_on_duplicate`: Stop when duplicate found (default: `true`)
- `duplicate_check_enabled`: Enable duplicate checking (default: `true`)
- `creation_time_comparison`: Compare by creation time (default: `true`)

**Speed Settings**:
- `download_timeout`: Max wait for download (default: `5000ms`)
- `verification_timeout`: Max wait for verification (default: `8000ms`)  
- `scroll_wait_time`: Wait between scrolls (default: `1000ms`)
- `fast_navigation_mode`: Enable fast navigation (default: `true`)

## 🛠️ Troubleshooting

### Issue: Downloads Not Detected
**Solution**: Check downloads folder permissions and path
```bash
ls -la /home/olereon/workspace/github.com/olereon/automaton/downloads/vids/
```

### Issue: Duplicate Detection Not Working  
**Solution**: Verify file naming pattern matches `video_YYYY-MM-DD-HH-MM-SS_gen_#NNNNNNNNN.mp4`

### Issue: Script Runs Too Fast
**Solution**: Increase timeouts in config:
```json
{
  "download_timeout": 8000,
  "verification_timeout": 12000,
  "scroll_wait_time": 2000
}
```

### Issue: Missing Dependencies
**Solution**: Ensure proper Python path:
```bash
export PYTHONPATH="/home/olereon/workspace/github.com/olereon/automaton/src:$PYTHONPATH"
```

## 📈 Performance Tips

1. **Run in Visible Mode**: Keep `headless: false` for better performance monitoring
2. **Optimal Batch Size**: Default `scroll_batch_size: 15` works well for most cases
3. **Network Considerations**: Adjust timeouts based on connection speed
4. **Disk Space**: Ensure sufficient space in downloads folder
5. **Browser Resources**: Close other browser instances for best performance

## 🔍 Monitoring

### Log Files
- **Main Log**: Console output with progress indicators
- **Debug Log**: `logs/fast_generation_extraction_debug.log`
- **Download Log**: `logs/generation_downloads.txt`

### Progress Indicators
- 🔍 Scanning existing files
- 🎯 Processing thumbnails
- ✅ Download completed
- 🚫 Duplicate detected
- 🛑 Stopping automation
- ⚡ Performance metrics

---

**Created**: August 2025  
**Compatible**: Python 3.11+, Playwright  
**Optimized**: DevTools disabled, Fast completion detection, Duplicate prevention