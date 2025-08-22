#!/usr/bin/env python3
"""
Programming-Like Blocks Example
Demonstrates comprehensive IF/WHILE/ELSE blocks for adaptable automation.
"""

import sys
import asyncio
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.engine import AutomationSequenceBuilder, WebAutomationEngine

async def smart_queue_processor():
    """
    Advanced queue processing with programming-like control flow:
    
    WHILE queue has items:
        IF queue count >= 8:
            Wait and continue (skip processing)
        ELIF queue count >= 6:
            Process 1 item only
        ELSE:
            Process 2 items
        END IF
        
        Check if we should continue processing
        IF processing_limit_reached:
            BREAK
        END IF
    END WHILE
    """
    
    print("🔄 SMART QUEUE PROCESSOR WITH PROGRAMMING BLOCKS")
    print("=" * 60)
    
    builder = AutomationSequenceBuilder(
        name="Smart Queue Processor",
        url="https://yourqueue.com"  # Replace with your URL
    )
    
    automation = (builder
        .set_headless(False)
        .set_viewport(1280, 720)
        
        # Initial setup
        .add_wait(2000, "Initial page load")
        
        # Main processing loop
        .add_while_begin("check_passed", "WHILE queue has items")
        
            # Check current queue count
            .add_check_element(
                selector=".queue-count",
                check_type="not_zero", 
                expected_value="",
                attribute="text",
                description="Check if queue has items"
            )
            
            # If no items, break out of loop
            .add_if_begin("check_failed", "IF queue is empty")
                .add_break("Break - no more items")
            .add_if_end()
            
            # Check queue capacity and decide processing strategy
            .add_check_element(".queue-count", "greater", "7", "text", "Check if queue >= 8")
            
            .add_if_begin("check_passed", "IF queue is nearly full (>=8)")
                # Queue too full - wait and continue
                .add_wait(5000, "Wait 5 seconds")
                .add_continue("Skip processing this cycle")
                
            .add_elif("value_equals", "ELIF queue count is 6 or 7")  # 6-7 items
                # Moderate load - process 1 item
                .add_click_button("button.process-one", "Process 1 item")
                .add_wait(2000, "Wait for processing")
                
            .add_else("ELSE queue has space (<6 items)")
                # Low load - process 2 items
                .add_click_button("button.process-one", "Process first item") 
                .add_wait(1000, "Wait between items")
                .add_click_button("button.process-one", "Process second item")
                .add_wait(2000, "Wait for processing")
                
            .add_if_end("END queue capacity check")
            
            # Check processing limits
            .add_check_element(
                selector=".processed-today",
                check_type="greater",
                expected_value="50", 
                attribute="text",
                description="Check if daily limit reached"
            )
            
            .add_if_begin("check_passed", "IF daily processing limit reached")
                .add_break("Break - daily limit reached")
            .add_if_end()
            
            # Add small delay before next iteration
            .add_wait(1000, "Wait before next check")
            
        .add_while_end("END main processing loop")
        
        # Final status check
        .add_check_element(".queue-count", "equals", "0", "text", "Final queue check")
        
        .add_if_begin("check_passed", "IF queue is now empty") 
            .add_click_button("button.mark-complete", "Mark session complete")
        .add_else("ELSE queue still has items")
            .add_click_button("button.save-progress", "Save current progress")
        .add_if_end()
        
        .build()
    )
    
    engine = WebAutomationEngine(automation)
    results = await engine.run_automation()
    
    print(f"\n✅ AUTOMATION COMPLETED")
    print(f"Success: {results['success']}")
    print(f"Actions completed: {results['actions_completed']}/{results['total_actions']}")
    
    return results

async def adaptive_form_processor():
    """
    Adaptive form processing with nested conditionals:
    
    FOR each form on the page:
        IF form is required:
            IF form type is text:
                Fill with appropriate text
            ELIF form type is select:
                Choose first available option
            ELIF form type is checkbox:
                Check if label contains "agree"
            ELSE:
                Skip this form field
            END IF
        END IF
    END FOR
    """
    
    print("\n📝 ADAPTIVE FORM PROCESSOR")
    print("=" * 60)
    
    builder = AutomationSequenceBuilder(
        name="Adaptive Form Processor", 
        url="https://yourform.com"
    )
    
    automation = (builder
        .set_headless(False)
        .add_wait(3000, "Wait for form to load")
        
        # Process required fields
        .add_while_begin("check_passed", "WHILE there are unprocessed required fields")
        
            # Check if there are required fields remaining
            .add_check_element(
                selector="input[required]:not(.processed), select[required]:not(.processed)",
                check_type="not_zero",
                expected_value="",
                attribute="length",  # Count of elements
                description="Check for unprocessed required fields"
            )
            
            .add_if_begin("check_failed", "IF no more required fields")
                .add_break("All required fields processed")
            .add_if_end()
            
            # Check field type and process accordingly
            .add_check_element(
                selector="input[required]:not(.processed):first",
                check_type="equals", 
                expected_value="text",
                attribute="type",
                description="Check if field is text input"
            )
            
            .add_if_begin("check_passed", "IF field is text input")
                .add_input_text("input[required]:not(.processed):first", "Sample text", "Fill text field")
                .add_wait(500, "Wait after text input")
                
            .add_elif("value_equals", "ELIF field is email")  # Check for email type
                .add_input_text("input[required]:not(.processed):first", "test@example.com", "Fill email field")
                .add_wait(500, "Wait after email input")
                
            .add_elif("value_equals", "ELIF field is number")  # Check for number type
                .add_input_text("input[required]:not(.processed):first", "123", "Fill number field")
                .add_wait(500, "Wait after number input")
                
            .add_else("ELSE field is other type (select, checkbox, etc.)")
                # Handle select dropdowns
                .add_check_element(
                    selector="select[required]:not(.processed):first",
                    check_type="not_zero",
                    expected_value="",
                    attribute="length",
                    description="Check if there's a select field"
                )
                
                .add_if_begin("check_passed", "IF there's a select field")
                    .add_click_button("select[required]:not(.processed):first option:nth-child(2)", "Select first option")
                    .add_wait(500, "Wait after select")
                .add_if_end()
                
            .add_if_end("END field type check")
            
            # Mark current field as processed (add class)
            # Note: This would typically be done with JavaScript injection
            .add_wait(100, "Mark field as processed")
            
            # Safety check - prevent infinite loops
            .add_check_element(
                selector=".form-processing-count",
                check_type="greater", 
                expected_value="20",
                attribute="text",
                description="Safety check for processing count"
            )
            
            .add_if_begin("check_passed", "IF processed too many fields")
                .add_break("Safety break - too many iterations")
            .add_if_end()
            
        .add_while_end("END field processing loop")
        
        # Final form submission
        .add_check_element("form button[type='submit']", "not_zero", "", "length", "Check for submit button")
        
        .add_if_begin("check_passed", "IF submit button exists")
            .add_click_button("form button[type='submit']", "Submit form")
            .add_wait(3000, "Wait for form submission")
            
            # Check submission result
            .add_check_element(".success-message", "contains", "success", "text", "Check for success message")
            
            .add_if_begin("check_passed", "IF submission successful")
                .add_wait(2000, "Success - wait before closing")
            .add_else("ELSE submission failed")
                .add_click_button("button.retry", "Retry submission")
            .add_if_end()
            
        .add_if_end("END submission check")
        
        .build()
    )
    
    engine = WebAutomationEngine(automation)
    results = await engine.run_automation()
    
    print(f"\n✅ FORM PROCESSING COMPLETED") 
    print(f"Success: {results['success']}")
    
    return results

async def error_handling_with_blocks():
    """
    Robust error handling using blocks:
    
    TRY (simulate with check):
        Attempt primary action
        IF action failed:
            TRY alternative method 1
            IF still failed:
                TRY alternative method 2
                IF still failed:
                    Log error and exit
                END IF
            END IF
        END IF
    """
    
    print("\n🛡️ ERROR HANDLING WITH BLOCKS")
    print("=" * 60)
    
    builder = AutomationSequenceBuilder(
        name="Robust Error Handler",
        url="https://unreliable-site.com"
    )
    
    automation = (builder
        .set_headless(False)
        .add_wait(2000, "Initial load")
        
        # Attempt primary login method
        .add_check_element("button.login-primary", "not_zero", "", "length", "Check for primary login")
        
        .add_if_begin("check_passed", "IF primary login available")
            .add_click_button("button.login-primary", "Try primary login")
            .add_wait(2000, "Wait for login response")
            
            # Check if login succeeded
            .add_check_element(".login-success", "not_zero", "", "length", "Check login success")
            
            .add_if_begin("check_failed", "IF primary login failed")
                # Try alternative method 1
                .add_check_element("button.login-alt1", "not_zero", "", "length", "Check for alt method 1")
                
                .add_if_begin("check_passed", "IF alternative method 1 available")
                    .add_click_button("button.login-alt1", "Try alternative method 1")
                    .add_wait(2000, "Wait for alt1 response")
                    
                    .add_check_element(".login-success", "not_zero", "", "length", "Check alt1 success")
                    
                    .add_if_begin("check_failed", "IF alt method 1 also failed")
                        # Try alternative method 2
                        .add_check_element("button.login-alt2", "not_zero", "", "length", "Check for alt method 2")
                        
                        .add_if_begin("check_passed", "IF alternative method 2 available")
                            .add_click_button("button.login-alt2", "Try alternative method 2")
                            .add_wait(2000, "Wait for alt2 response")
                            
                            .add_check_element(".login-success", "not_zero", "", "length", "Check alt2 success")
                            
                            .add_if_begin("check_failed", "IF all methods failed")
                                .add_click_button("button.report-error", "Report login failure")
                                .add_wait(1000, "Log error state")
                            .add_if_end()
                            
                        .add_if_end("END alt method 2 check")
                    .add_if_end("END alt method 1 failure handling")
                .add_if_end("END alt method 1 check")
            .add_if_end("END primary login failure handling")
            
        .add_else("ELSE no login method available")
            .add_wait(1000, "Log no login methods available")
            
        .add_if_end("END login attempt")
        
        # Final status verification
        .add_check_element(".user-dashboard", "not_zero", "", "length", "Check if logged in")
        
        .add_if_begin("check_passed", "IF successfully logged in")
            .add_click_button("button.proceed", "Proceed to main task")
        .add_else("ELSE login failed completely")
            .add_click_button("button.exit", "Exit due to login failure")
        .add_if_end()
        
        .build()
    )
    
    engine = WebAutomationEngine(automation)
    results = await engine.run_automation()
    
    print(f"\n✅ ERROR HANDLING COMPLETED")
    print(f"Success: {results['success']}")
    
    return results

if __name__ == "__main__":
    print("PROGRAMMING-LIKE BLOCKS AUTOMATION EXAMPLES")
    print("=" * 60)
    print("Choose an example:")
    print("1. Smart Queue Processor (WHILE loops with complex conditions)")
    print("2. Adaptive Form Processor (nested IF/WHILE for form handling)")
    print("3. Error Handling with Blocks (robust error recovery)")
    print("4. Run all examples")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(smart_queue_processor())
    elif choice == "2":
        asyncio.run(adaptive_form_processor())
    elif choice == "3":
        asyncio.run(error_handling_with_blocks())
    elif choice == "4":
        print("\n" + "="*60)
        asyncio.run(smart_queue_processor())
        print("\n" + "="*60)
        asyncio.run(adaptive_form_processor())
        print("\n" + "="*60)
        asyncio.run(error_handling_with_blocks())
    else:
        print("Invalid choice")