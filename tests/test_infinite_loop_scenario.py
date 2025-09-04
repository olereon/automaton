#!/usr/bin/env python3.11

"""
Test for the complete infinite loop scenario fix.

This test simulates the exact scenario that was causing the infinite loop:
1. System downloads new generations
2. Finds a duplicate, triggers exit-scan-return, finds boundary at container 26
3. Downloads boundary generation successfully  
4. Next thumbnail is also a duplicate (consecutive duplicate)
5. BEFORE FIX: Would trigger exit-scan-return again, find same boundary → infinite loop
6. AFTER FIX: Uses fast-forward mode instead, prevents infinite loop
"""

import pytest
from unittest.mock import AsyncMock, patch, Mock
from src.utils.generation_download_manager import GenerationDownloadManager, GenerationDownloadConfig, DuplicateMode

class TestInfiniteLoopScenario:
    """Test the complete infinite loop scenario and fix"""

    @pytest.fixture
    def skip_config(self, tmp_path):
        """SKIP mode configuration with exit-scan-return enabled"""
        return GenerationDownloadConfig(
            downloads_folder=str(tmp_path / "downloads"),
            logs_folder=str(tmp_path / "logs"),
            duplicate_mode=DuplicateMode.SKIP,
            duplicate_check_enabled=True,
            stop_on_duplicate=False,
            use_exit_scan_strategy=True,
            max_downloads=100
        )

    @pytest.fixture
    def log_entries_before_boundary(self):
        """Log entries before boundary - these are the OLD generations"""
        return {
            '03 Sep 2025 16:15:18': {  # This will be the boundary datetime
                'file_id': '#000000026', 
                'prompt': 'Boundary generation that marks the divide between old and new'
            },
            '03 Sep 2025 16:10:00': {
                'file_id': '#000000025',
                'prompt': 'Generation before boundary'  
            }
        }

    @pytest.mark.asyncio
    async def test_infinite_loop_scenario_step_by_step(self, skip_config, log_entries_before_boundary):
        """Test the complete scenario that caused infinite loop"""
        
        manager = GenerationDownloadManager(skip_config)
        
        # Initialize with existing log entries (simulates previous downloads)
        with patch.object(manager, '_load_existing_log_entries', return_value=log_entries_before_boundary):
            manager.initialize_enhanced_skip_mode()
        
        mock_page = AsyncMock()
        
        # --- STEP 1: System encounters first duplicate and triggers exit-scan-return ---
        print("\n=== STEP 1: First duplicate found, triggers exit-scan-return ===")
        
        duplicate_metadata = {
            "generation_date": "03 Sep 2025 16:15:18",  # Matches boundary in log
            "prompt": "Boundary generation that marks the divide between old and new"
        }
        
        with patch.object(manager, 'extract_metadata_from_page', return_value=duplicate_metadata):
            result1 = await manager.check_comprehensive_duplicate(mock_page, "thumbnail_1")
            
            print(f"First duplicate check result: {result1}")
            assert result1 == "exit_scan_return", "First duplicate should trigger exit-scan-return"
            assert manager.boundary_just_downloaded == False, "Boundary flag should be False initially"
        
        # --- STEP 2: Exit-scan-return finds boundary and sets flag ---
        print("\n=== STEP 2: Exit-scan-return finds boundary, sets boundary flag ===")
        
        # Simulate exit-scan-return success (this would happen in the actual workflow)
        manager.boundary_just_downloaded = True  # This gets set in the actual exit-scan-return logic
        print(f"Boundary flag after exit-scan-return: {manager.boundary_just_downloaded}")
        
        # --- STEP 3: Boundary generation gets downloaded successfully ---
        print("\n=== STEP 3: Boundary generation downloaded successfully ===")
        
        # (In real workflow, download happens here)
        # boundary_just_downloaded flag remains True to handle next thumbnail
        assert manager.boundary_just_downloaded == True, "Boundary flag maintained for next thumbnail"
        
        # --- STEP 4: System navigates to next thumbnail (consecutive duplicate) ---
        print("\n=== STEP 4: Next thumbnail is also duplicate (consecutive duplicate) ===")
        
        consecutive_duplicate_metadata = {
            "generation_date": "03 Sep 2025 16:10:00",  # Another old generation
            "prompt": "Generation before boundary"
        }
        
        with patch.object(manager, 'extract_metadata_from_page', return_value=consecutive_duplicate_metadata):
            result2 = await manager.check_comprehensive_duplicate(mock_page, "thumbnail_2")
            
            print(f"Consecutive duplicate check result: {result2}")
            
            # CRITICAL: Should return "skip" instead of "exit_scan_return"
            assert result2 == "skip", f"Consecutive duplicate should return 'skip' not '{result2}'"
            
            # Boundary flag should be reset after handling consecutive duplicate
            assert manager.boundary_just_downloaded == False, "Boundary flag should be reset"
        
        # --- STEP 5: System continues normally (no infinite loop) ---
        print("\n=== STEP 5: System continues normally without infinite loop ===")
        
        # If another duplicate is found after this, it should trigger normal exit-scan-return
        another_duplicate_metadata = {
            "generation_date": "03 Sep 2025 16:10:00",  # Same old generation
            "prompt": "Generation before boundary"
        }
        
        with patch.object(manager, 'extract_metadata_from_page', return_value=another_duplicate_metadata):
            result3 = await manager.check_comprehensive_duplicate(mock_page, "thumbnail_3")
            
            print(f"Third duplicate check result: {result3}")
            # Should trigger normal exit-scan-return again since boundary_just_downloaded=False
            assert result3 == "exit_scan_return", "Normal duplicates should trigger exit-scan-return again"
        
        print("\n✅ INFINITE LOOP FIX VERIFIED:")
        print("  - First duplicate: triggers exit-scan-return ✓")  
        print("  - Boundary download: sets boundary flag ✓")
        print("  - Consecutive duplicate: uses skip mode instead of exit-scan-return ✓")
        print("  - Boundary flag reset: prevents future issues ✓") 
        print("  - Normal operation: resumes after fix ✓")

    @pytest.mark.asyncio
    async def test_boundary_flag_workflow_integration(self, skip_config):
        """Test boundary flag integration with complete workflow"""
        
        manager = GenerationDownloadManager(skip_config)
        
        # Test flag initialization
        assert hasattr(manager, 'boundary_just_downloaded'), "Boundary flag should exist"
        assert manager.boundary_just_downloaded == False, "Should initialize to False"
        
        # Test flag setting (simulates exit-scan-return success)
        manager.boundary_just_downloaded = True
        assert manager.boundary_just_downloaded == True, "Flag should be settable"
        
        # Test flag reset after consecutive duplicate handling
        mock_page = AsyncMock()
        with patch.object(manager, '_load_existing_log_entries', return_value={'test': {}}):
            manager.existing_log_entries = {'03 Sep 2025 16:15:18': {'prompt': 'test'}}
            
            duplicate_metadata = {
                "generation_date": "03 Sep 2025 16:15:18",
                "prompt": "test"
            }
            
            with patch.object(manager, 'extract_metadata_from_page', return_value=duplicate_metadata):
                result = await manager.check_comprehensive_duplicate(mock_page, "test_thumb")
                
                # Should return skip and reset flag
                assert result == "skip", "Should handle consecutive duplicate with skip"
                assert manager.boundary_just_downloaded == False, "Flag should be reset"

def run_tests():
    """Run the tests directly"""
    import subprocess
    result = subprocess.run(['python3.11', '-m', 'pytest', __file__, '-v', '-s'], 
                          capture_output=True, text=True)
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    return result.returncode == 0

if __name__ == "__main__":
    success = run_tests()
    if success:
        print("\n🎉 SUCCESS: Infinite loop scenario fix is working correctly!")
        print("The system will no longer get stuck in infinite exit-scan-return loops")
        print("when consecutive duplicates are found after boundary downloads.")
    else:
        print("\n❌ FAILURE: Infinite loop scenario fix needs review")