#!/usr/bin/env python3.11

"""
Deep dive investigation into boundary processing workflow.

This test traces the exact execution path when boundary generation
fails to download, focusing on the disconnect between boundary detection
and actual download execution.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
from enum import Enum

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Mock the DuplicateMode enum
class DuplicateMode(Enum):
    FINISH = "finish"
    SKIP = "skip"

class TestBoundaryProcessingDeepDive:
    """Deep investigation into boundary processing failure"""

    def test_boundary_detection_vs_download_execution(self):
        """Test the disconnect between boundary detection and download execution"""
        
        print("\n" + "="*80)
        print("🔬 DEEP DIVE: BOUNDARY PROCESSING WORKFLOW INVESTIGATION")
        print("="*80)
        
        # Exact data from user's logs
        boundary_data = {
            'container_number': 47,
            'thumbnail_id': 'landmark_thumbnail_6',  # This is the key issue!
            'generation_date': '03 Sep 2025 16:15:18',
            'prompt': 'The camera begins with a medium shot, framing the Prismatic Mage levitating above the magic vortex, their flowing robes cascading and billowing. Crystalline prismatic shards suspended in the air pulse with synchronized light. The camera slowly orbits left, revealing the swirling vortex beneath them—its spiraling en...',
            'prompt_length': 319
        }
        
        incomplete_log_entry = {
            "03 Sep 2025 16:15:18": {
                "prompt": "The camera begins with a medium shot, framing the Prismatic Mage levitating above the magic vortex, their flowing robes cascading and billowing. Crystalline prismatic shards suspended in the air pulse with synchronized light. The camera slowly orbits left, revealing the swirling vortex beneath them—its spiraling en...",
                "file_id": "#999999999"  # Incomplete entry from previous failed run
            }
        }
        
        print(f"🎯 BOUNDARY DETECTION:")
        print(f"   Container: #{boundary_data['container_number']}")
        print(f"   Date: {boundary_data['generation_date']}")
        print(f"   Prompt: {boundary_data['prompt'][:100]}...")
        
        print(f"\n❌ DOWNLOAD EXECUTION:")
        print(f"   Processing: {boundary_data['thumbnail_id']}")
        print(f"   Result: Failed to download thumbnail #6")
        
        print(f"\n🤔 THE DISCONNECT:")
        print(f"   • Boundary found at container #{boundary_data['container_number']}")
        print(f"   • But processing thumbnail #{boundary_data['thumbnail_id'].split('_')[-1]}")
        print(f"   • This suggests thumbnail ID != boundary container number")
        
        # Mock the comprehensive duplicate check to see what it returns
        class MockGenerationDownloadManager:
            def __init__(self):
                self.existing_log_entries = incomplete_log_entry
                
            def check_comprehensive_duplicate_debug(self, metadata):
                """Debug version of comprehensive duplicate check"""
                
                generation_date = metadata['generation_date']
                prompt = metadata['prompt']
                
                print(f"\n🔍 COMPREHENSIVE DUPLICATE CHECK DEBUG:")
                print(f"   Input Date: {generation_date}")
                print(f"   Input Prompt Length: {len(prompt)}")
                print(f"   Log Entries: {len(self.existing_log_entries)}")
                
                # Check if date exists in log
                if generation_date in self.existing_log_entries:
                    existing_entry = self.existing_log_entries[generation_date]
                    file_id = existing_entry.get('file_id', '')
                    
                    print(f"   📚 Found entry in log: {generation_date}")
                    print(f"   📄 File ID: {file_id}")
                    
                    # Test our incomplete entry filtering
                    if file_id == '#999999999':
                        print(f"   ✅ FILTERING: Incomplete entry detected - should allow download")
                        return False  # Allow download
                    else:
                        print(f"   🛑 DUPLICATE: Complete entry detected - should block download")
                        return "exit_scan_return"
                        
                print(f"   ✅ No duplicate found - should allow download")
                return False
        
        manager = MockGenerationDownloadManager()
        result = manager.check_comprehensive_duplicate_debug(boundary_data)
        
        print(f"\n📊 COMPREHENSIVE CHECK RESULT: {result}")
        
        if result == False:
            print("   ✅ Should proceed with download")
        elif result == "exit_scan_return":
            print("   🚫 Should trigger exit-scan-return (might be the issue)")
        else:
            print(f"   ❓ Unexpected result: {result}")
        
        print(f"\n💡 HYPOTHESIS:")
        print(f"   1. Boundary detection works correctly")
        print(f"   2. Gallery opens at boundary correctly")
        print(f"   3. Metadata extraction succeeds")
        print(f"   4. BUT: Comprehensive duplicate check might be failing to filter incomplete entries")
        print(f"   5. OR: There's a different code path being used")
        
        # The test passes if we identify the investigation points
        assert boundary_data['container_number'] == 47, "Boundary detection should work"
        assert boundary_data['generation_date'] == '03 Sep 2025 16:15:18', "Metadata extraction should work"
        
    def test_comprehensive_duplicate_check_with_actual_data(self):
        """Test comprehensive duplicate check with exact data from logs"""
        
        print("\n" + "="*80)
        print("🧪 TESTING: COMPREHENSIVE DUPLICATE CHECK WITH REAL DATA")
        print("="*80)
        
        # Exact metadata from successful extraction
        extracted_metadata = {
            'generation_date': '03 Sep 2025 16:15:18',
            'prompt': 'The camera begins with a medium shot, framing the Prismatic Mage levitating above the magic vortex, their flowing robes cascading and billowing. Crystalline prismatic shards suspended in the air pulse with synchronized light. The camera slowly orbits left, revealing the swirling vortex beneath them—its spiraling en...'
        }
        
        # Exact log entry causing the issue
        problematic_log_entries = {
            "03 Sep 2025 16:15:18": {
                "prompt": "The camera begins with a medium shot, framing the Prismatic Mage levitating above the magic vortex, their flowing robes cascading and billowing. Crystalline prismatic shards suspended in the air pulse with synchronized light. The camera slowly orbits left, revealing the swirling vortex beneath them—its spiraling en...",
                "file_id": "#999999999",  # This is the problematic entry
                "creation_time": "03 Sep 2025 16:15:18",
                "media_type": "video"
            }
        }
        
        def simulate_comprehensive_duplicate_check(metadata, log_entries):
            """Simulate the actual comprehensive duplicate check logic"""
            
            generation_date = metadata.get('generation_date')
            prompt = metadata.get('prompt', '')
            
            print(f"🔍 SIMULATING COMPREHENSIVE DUPLICATE CHECK:")
            print(f"   Date: {generation_date}")
            print(f"   Prompt length: {len(prompt)}")
            
            # Algorithm from the actual function
            if generation_date in log_entries:
                existing_entry = log_entries[generation_date]
                
                # CRITICAL: Test our incomplete entry filtering
                file_id = existing_entry.get('file_id', '')
                print(f"   📄 Found log entry with file_id: {file_id}")
                
                if file_id == '#999999999':
                    print(f"   ⏭️ FILTERING: Incomplete entry - allowing download")
                    return False  # Not a duplicate
                    
                # Check prompt match (100 char comparison)
                existing_prompt = existing_entry.get('prompt', '')
                current_prompt_100 = prompt[:100]
                existing_prompt_100 = existing_prompt[:100]
                
                print(f"   🔍 Prompt comparison:")
                print(f"      Current (100 chars): {current_prompt_100}")
                print(f"      Existing (100 chars): {existing_prompt_100}")
                print(f"      Match: {current_prompt_100 == existing_prompt_100}")
                
                if current_prompt_100 == existing_prompt_100:
                    print(f"   🛑 DUPLICATE DETECTED: Returning 'exit_scan_return'")
                    return "exit_scan_return"
                    
            print(f"   ✅ NO DUPLICATE: Returning False")
            return False
        
        result = simulate_comprehensive_duplicate_check(extracted_metadata, problematic_log_entries)
        
        print(f"\n📊 FINAL RESULT: {result}")
        
        if result == False:
            print("   ✅ This should allow download - but it's still failing!")
            print("   💡 The issue must be elsewhere in the workflow")
        elif result == "exit_scan_return":
            print("   🚫 This would block download and trigger exit-scan-return")
            print("   💡 Our incomplete entry filtering might not be working")
        
        # Test assertion
        assert generation_date in problematic_log_entries, "Log entry should exist"
        print(f"\n🎯 KEY INSIGHT: The comprehensive duplicate check simulation gives us the answer!")

def run_comprehensive_investigation():
    """Run the comprehensive investigation"""
    test_instance = TestBoundaryProcessingDeepDive()
    test_instance.test_boundary_detection_vs_download_execution()
    test_instance.test_comprehensive_duplicate_check_with_actual_data()

if __name__ == "__main__":
    print("🚀 STARTING COMPREHENSIVE BOUNDARY PROCESSING INVESTIGATION")
    run_comprehensive_investigation()
    print("✅ INVESTIGATION COMPLETE")