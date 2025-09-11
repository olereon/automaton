# Automaton Advanced Usage Guide

## Introduction

This guide covers advanced techniques and patterns for using Automaton effectively. It assumes you're already familiar with the basics covered in the [User Guide](4_user_guide.md) and [API Reference](5_api_reference.md).

## Table of Contents

1. [Custom Action Development](#custom-action-development)
2. [Advanced Flow Control](#advanced-flow-control)
3. [Error Handling and Recovery](#error-handling-and-recovery)
4. [Performance Optimization](#performance-optimization)
5. [Dynamic Content Handling](#dynamic-content-handling)
6. [Multi-Page Workflows](#multi-page-workflows)
7. [Data Extraction and Processing](#data-extraction-and-processing)
8. [Integration with External Systems](#integration-with-external-systems)
9. [Testing and Debugging Automations](#testing-and-debugging-automations)
10. [Best Practices for Complex Automations](#best-practices-for-complex-automations)

## Custom Action Development

Creating custom actions allows you to extend Automaton's functionality for specialized tasks.

### Creating a Basic Custom Action

```python
from automaton.actions import Action, ActionResult, ActionHandler
from automaton.context import ExecutionContext

class ScreenshotActionHandler(ActionHandler):
    async def execute(self, action: Action, context: ExecutionContext) -> ActionResult:
        # Take a screenshot of the current page
        page = context.page
        screenshot_path = action.value or "screenshot.png"
        
        try:
            await page.screenshot(path=screenshot_path)
            return ActionResult(
                success=True,
                message=f"Screenshot saved to {screenshot_path}",
                data={"path": screenshot_path}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Failed to take screenshot: {str(e)}"
            )
    
    def validate(self, action: Action) -> List[str]:
        errors = []
        if action.value and not isinstance(action.value, str):
            errors.append("Screenshot path must be a string")
        return errors

# Register the custom action
from automaton.executor import ActionExecutor
action_executor = ActionExecutor()
action_executor.register_action("screenshot", ScreenshotActionHandler())
```

### Creating a Complex Custom Action

```python
import json
from typing import Dict, Any, List
from automaton.actions import Action, ActionResult, ActionHandler
from automaton.context import ExecutionContext

class DataTableExtractorHandler(ActionHandler):
    async def execute(self, action: Action, context: ExecutionContext) -> ActionResult:
        page = context.page
        selector = action.selector
        options = action.value or {}
        
        try:
            # Extract table headers
            header_selector = f"{selector} th"
            headers = await page.eval_on_selector_all(
                header_selector, 
                "elements => elements.map(el => el.textContent.trim())"
            )
            
            # Extract table rows
            row_selector = f"{selector} tr"
            rows = await page.query_selector_all(row_selector)
            
            data = []
            for row in rows[1:]:  # Skip header row
                cells = await row.query_selector_all("td")
                row_data = {}
                for i, cell in enumerate(cells):
                    if i < len(headers):
                        cell_text = await cell.text_content()
                        row_data[headers[i]] = cell_text.strip()
                data.append(row_data)
            
            # Store extracted data in a variable if specified
            if options.get("variable"):
                context.variables.set_variable(options["variable"], data)
            
            return ActionResult(
                success=True,
                message=f"Extracted {len(data)} rows from table",
                data={"rows": len(data), "headers": headers}
            )
        except Exception as e:
            return ActionResult(
                success=False,
                message=f"Failed to extract table data: {str(e)}"
            )
    
    def validate(self, action: Action) -> List[str]:
        errors = []
        if not action.selector:
            errors.append("Selector is required for extract_table action")
        return errors
```

### Using Custom Actions in Configuration

```json
{
  "name": "Custom Action Example",
  "url": "https://example.com/data",
  "actions": [
    {
      "type": "screenshot",
      "value": "example_page.png"
    },
    {
      "type": "extract_table",
      "selector": "#data-table",
      "value": {
        "variable": "table_data"
      }
    },
    {
      "type": "log_message",
      "value": "Extracted ${table_data.rows} rows with headers: ${table_data.headers}"
    }
  ]
}
```

## Advanced Flow Control

### Nested Conditional Logic

```json
{
  "actions": [
    {
      "type": "check_element",
      "selector": ".user-menu",
      "operator": "exists"
    },
    {
      "type": "if_begin",
      "condition": "check_result",
      "operator": "==",
      "value": true
    },
    {
      "type": "click_button",
      "selector": ".user-menu"
    },
    {
      "type": "check_element",
      "selector": ".logout-button",
      "operator": "exists"
    },
    {
      "type": "if_begin",
      "condition": "check_result",
      "operator": "==",
      "value": true
    },
    {
      "type": "click_button",
      "selector": ".logout-button"
    },
    {
      "type": "if_end"
    },
    {
      "type": "else"
    },
    {
      "type": "log_message",
      "value": "User is not logged in"
    },
    {
      "type": "if_end"
    }
  ]
}
```

### Complex Loop Patterns

```json
{
  "actions": [
    {
      "type": "set_variable",
      "value": {
        "name": "page_counter",
        "value": 1
      }
    },
    {
      "type": "while_begin",
      "condition": "has_more_pages",
      "operator": "==",
      "value": true
    },
    {
      "type": "log_message",
      "value": "Processing page ${page_counter}"
    },
    {
      "type": "extract_table",
      "selector": ".data-table",
      "value": {
        "variable": "current_page_data"
      }
    },
    {
      "type": "check_element",
      "selector": ".next-page",
      "operator": "exists"
    },
    {
      "type": "if_begin",
      "condition": "check_result",
      "operator": "==",
      "value": true
    },
    {
      "type": "click_button",
      "selector": ".next-page"
    },
    {
      "type": "wait_for_element",
      "selector": ".data-table"
    },
    {
      "type": "increment_variable",
      "value": {
        "name": "page_counter",
        "increment": 1
      }
    },
    {
      "type": "else"
    },
    {
      "type": "set_variable",
      "value": {
        "name": "has_more_pages",
        "value": false
      }
    },
    {
      "type": "if_end"
    },
    {
      "type": "while_end"
    }
  ]
}
```

### Retry Mechanisms

```json
{
  "actions": [
    {
      "type": "set_variable",
      "value": {
        "name": "retry_count",
        "value": 0
      }
    },
    {
      "type": "set_variable",
      "value": {
        "name": "max_retries",
        "value": 3
      }
    },
    {
      "type": "set_variable",
      "value": {
        "name": "action_successful",
        "value": false
      }
    },
    {
      "type": "while_begin",
      "condition": "action_successful",
      "operator": "==",
      "value": false
    },
    {
      "type": "if_begin",
      "condition": "retry_count",
      "operator": ">=",
      "value": "${max_retries}"
    },
    {
      "type": "log_message",
      "value": "Max retries (${max_retries}) reached. Giving up."
    },
    {
      "type": "break"
    },
    {
      "type": "if_end"
    },
    {
      "type": "try_begin"
    },
    {
      "type": "click_button",
      "selector": "#unstable-button"
    },
    {
      "type": "wait_for_element",
      "selector": ".success-message",
      "timeout": 5000
    },
    {
      "type": "set_variable",
      "value": {
        "name": "action_successful",
        "value": true
      }
    },
    {
      "type": "catch_begin"
    },
    {
      "type": "increment_variable",
      "value": {
        "name": "retry_count",
        "increment": 1
      }
    },
    {
      "type": "log_message",
      "value": "Attempt ${retry_count} failed. Retrying..."
    },
    {
      "type": "wait",
      "value": 2000
    },
    {
      "type": "catch_end"
    },
    {
      "type": "while_end"
    }
  ]
}
```

## Error Handling and Recovery

### Custom Error Handlers

```python
from automaton.errors import ErrorHandler, ErrorResult, AutomatonError
from automaton.context import ExecutionContext

class NetworkErrorHandler(ErrorHandler):
    async def handle_error(self, error: Exception, context: ExecutionContext) -> ErrorResult:
        if isinstance(error, NetworkError):
            # Log the error
            context.logger.error(f"Network error occurred: {str(error)}")
            
            # Wait before retrying
            import asyncio
            await asyncio.sleep(5)
            
            # Refresh the page
            await context.page.reload()
            
            # Indicate that execution should continue
            return ErrorResult(
                should_continue=True,
                message="Network error handled. Page refreshed."
            )
        
        # For other errors, use default handling
        return ErrorResult(
            should_continue=False,
            message=f"Unhandled error: {str(error)}"
        )

# Register the custom error handler
from automaton.engine import AutomationEngine
engine = AutomationEngine()
engine.error_handler.register_handler(NetworkError, NetworkErrorHandler())
```

### Graceful Degradation

```json
{
  "actions": [
    {
      "type": "try_begin"
    },
    {
      "type": "click_button",
      "selector": "#advanced-feature"
    },
    {
      "type": "wait_for_element",
      "selector": ".advanced-panel"
    },
    {
      "type": "log_message",
      "value": "Advanced feature loaded successfully"
    },
    {
      "type": "catch_begin"
    },
    {
      "type": "log_message",
      "value": "Advanced feature not available, using basic functionality"
    },
    {
      "type": "click_button",
      "selector": "#basic-feature"
    },
    {
      "type": "wait_for_element",
      "selector": ".basic-panel"
    },
    {
      "type": "catch_end"
    }
  ]
}
```

## Performance Optimization

### Parallel Execution

```python
import asyncio
from automaton.actions import Action, ActionResult
from automaton.context import ExecutionContext

class ParallelActionHandler(ActionHandler):
    async def execute(self, action: Action, context: ExecutionContext) -> ActionResult:
        parallel_actions = action.value.get("actions", [])
        results = []
        
        # Create tasks for parallel execution
        tasks = []
        for parallel_action in parallel_actions:
            task = self._execute_single_action(parallel_action, context)
            tasks.append(task)
        
        # Wait for all tasks to complete
        action_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        for result in action_results:
            if isinstance(result, Exception):
                results.append({
                    "success": False,
                    "message": str(result)
                })
            else:
                results.append(result.__dict__)
                if result.success:
                    success_count += 1
        
        return ActionResult(
            success=success_count == len(parallel_actions),
            message=f"Completed {success_count}/{len(parallel_actions)} actions successfully",
            data={"results": results}
        )
    
    async def _execute_single_action(self, action_config: Dict, context: ExecutionContext) -> ActionResult:
        # Convert action config to Action object
        action = Action(
            type=action_config["type"],
            selector=action_config.get("selector"),
            value=action_config.get("value")
        )
        
        # Execute the action
        handler = context.action_executor.get_handler(action.type)
        return await handler.execute(action, context)
```

### Resource Management

```json
{
  "actions": [
    {
      "type": "set_variable",
      "value": {
        "name": "start_time",
        "value": "${timestamp}"
      }
    },
    {
      "type": "log_message",
      "value": "Starting data extraction at ${start_time}"
    },
    {
      "type": "set_variable",
      "value": {
        "name": "batch_size",
        "value": 100
      }
    },
    {
      "type": "set_variable",
      "value": {
        "name": "processed_items",
        "value": 0
      }
    },
    {
      "type": "while_begin",
      "condition": "has_more_data",
      "operator": "==",
      "value": true
    },
    {
      "type": "process_batch",
      "value": {
        "batch_size": "${batch_size}",
        "variable": "current_batch"
      }
    },
    {
      "type": "increment_variable",
      "value": {
        "name": "processed_items",
        "increment": "${current_batch.length}"
      }
    },
    {
      "type": "log_message",
      "value": "Processed ${processed_items} items so far"
    },
    {
      "type": "check_memory_usage",
      "value": {
        "threshold": "80%",
        "variable": "memory_ok"
      }
    },
    {
      "type": "if_begin",
      "condition": "memory_ok",
      "operator": "==",
      "value": false
    },
    {
      "type": "log_message",
      "value": "Memory usage high, pausing to free resources"
    },
    {
      "type": "wait",
      "value": 5000
    },
    {
      "type": "clear_temporary_data"
    },
    {
      "type": "if_end"
    },
    {
      "type": "while_end"
    },
    {
      "type": "set_variable",
      "value": {
        "name": "end_time",
        "value": "${timestamp}"
      }
    },
    {
      "type": "log_message",
      "value": "Completed data extraction in ${end_time - start_time}ms"
    }
  ]
}
```

## Dynamic Content Handling

### Waiting for Dynamic Elements

```json
{
  "actions": [
    {
      "type": "click_button",
      "selector": "#load-data"
    },
    {
      "type": "conditional_wait",
      "selector": ".data-container",
      "operator": "contains",
      "value": "Loaded",
      "timeout": 30000,
      "interval": 1000,
      "backoff": 1.5
    },
    {
      "type": "log_message",
      "value": "Data loaded successfully"
    }
  ]
}
```

### Handling AJAX Requests

```json
{
  "actions": [
    {
      "type": "click_button",
      "selector": "#submit-form"
    },
    {
      "type": "wait_for_network_idle",
      "value": {
        "timeout": 30000,
        "idle_time": 2000
      }
    },
    {
      "type": "check_element",
      "selector": ".success-message",
      "operator": "exists"
    },
    {
      "type": "if_begin",
      "condition": "check_result",
      "operator": "==",
      "value": true
    },
    {
      "type": "log_message",
      "value": "Form submitted successfully"
    },
    {
      "type": "else"
    },
    {
      "type": "check_element",
      "selector": ".error-message",
      "operator": "exists"
    },
    {
      "type": "if_begin",
      "condition": "check_result",
      "operator": "==",
      "value": true
    },
    {
      "type": "log_message",
      "value": "Form submission failed"
    },
    {
      "type": "if_end"
    },
    {
      "type": "if_end"
    }
  ]
}
```

## Multi-Page Workflows

### Page Navigation with State Preservation

```json
{
  "actions": [
    {
      "type": "set_variable",
      "value": {
        "name": "collected_data",
        "value": []
      }
    },
    {
      "type": "navigate_to",
      "value": "https://example.com/page1"
    },
    {
      "type": "wait_for_element",
      "selector": ".content"
    },
    {
      "type": "extract_data",
      "selector": ".data-item",
      "value": {
        "variable": "page_data"
      }
    },
    {
      "type": "append_to_list",
      "value": {
        "list": "collected_data",
        "items": "${page_data}"
      }
    },
    {
      "type": "navigate_to",
      "value": "https://example.com/page2"
    },
    {
      "type": "wait_for_element",
      "selector": ".content"
    },
    {
      "type": "extract_data",
      "selector": ".data-item",
      "value": {
        "variable": "page_data"
      }
    },
    {
      "type": "append_to_list",
      "value": {
        "list": "collected_data",
        "items": "${page_data}"
      }
    },
    {
      "type": "save_data",
      "value": {
        "data": "${collected_data}",
        "filename": "multi_page_data.json"
      }
    }
  ]
}
```

### Handling Authentication Across Pages

```json
{
  "actions": [
    {
      "type": "check_element",
      "selector": ".login-form",
      "operator": "exists"
    },
    {
      "type": "if_begin",
      "condition": "check_result",
      "operator": "==",
      "value": true
    },
    {
      "type": "input_text",
      "selector": "#username",
      "value": "${username}"
    },
    {
      "type": "input_text",
      "selector": "#password",
      "value": "${password}"
    },
    {
      "type": "click_button",
      "selector": "#login-button"
    },
    {
      "type": "wait_for_element",
      "selector": ".user-dashboard"
    },
    {
      "type": "log_message",
      "value": "Login successful"
    },
    {
      "type": "if_end"
    },
    {
      "type": "navigate_to",
      "value": "https://example.com/protected-page"
    },
    {
      "type": "wait_for_element",
      "selector": ".protected-content"
    },
    {
      "type": "extract_data",
      "selector": ".data-item",
      "value": {
        "variable": "protected_data"
      }
    }
  ]
}
```

## Data Extraction and Processing

### Complex Data Extraction

```json
{
  "actions": [
    {
      "type": "extract_structured_data",
      "selector": ".product-list",
      "value": {
        "items": ".product-item",
        "fields": {
          "name": ".product-name",
          "price": ".product-price",
          "rating": ".product-rating",
          "availability": {
            "selector": ".stock-status",
            "attribute": "data-stock"
          }
        },
        "variable": "products"
      }
    },
    {
      "type": "process_data",
      "value": {
        "data": "${products}",
        "operations": [
          {
            "type": "filter",
            "condition": "item.price < 100"
          },
          {
            "type": "map",
            "transformation": "item.name + ' - $' + item.price"
          },
          {
            "type": "sort",
            "by": "rating",
            "order": "desc"
          }
        ],
        "variable": "filtered_products"
      }
    },
    {
      "type": "save_data",
      "value": {
        "data": "${filtered_products}",
        "filename": "products.json"
      }
    }
  ]
}
```

### Data Transformation and Export

```json
{
  "actions": [
    {
      "type": "extract_table",
      "selector": ".data-table",
      "value": {
        "variable": "table_data"
      }
    },
    {
      "type": "transform_data",
      "value": {
        "data": "${table_data}",
        "format": "csv",
        "options": {
          "delimiter": ",",
          "include_headers": true
        },
        "variable": "csv_data"
      }
    },
    {
      "type": "save_file",
      "value": {
        "content": "${csv_data}",
        "filename": "exported_data.csv"
      }
    },
    {
      "type": "transform_data",
      "value": {
        "data": "${table_data}",
        "format": "json",
        "options": {
          "indent": 2
        },
        "variable": "json_data"
      }
    },
    {
      "type": "save_file",
      "value": {
        "content": "${json_data}",
        "filename": "exported_data.json"
      }
    }
  ]
}
```

## Integration with External Systems

### API Integration

```json
{
  "actions": [
    {
      "type": "extract_data",
      "selector": ".form-data",
      "value": {
        "variable": "form_data"
      }
    },
    {
      "type": "api_request",
      "value": {
        "method": "POST",
        "url": "https://api.example.com/submit",
        "headers": {
          "Content-Type": "application/json",
          "Authorization": "Bearer ${api_token}"
        },
        "body": "${form_data}",
        "variable": "api_response"
      }
    },
    {
      "type": "check_variable",
      "value": {
        "variable": "api_response.status",
        "operator": "==",
        "value": 200
      }
    },
    {
      "type": "if_begin",
      "condition": "check_result",
      "operator": "==",
      "value": true
    },
    {
      "type": "log_message",
      "value": "API request successful"
    },
    {
      "type": "else"
    },
    {
      "type": "log_message",
      "value": "API request failed with status ${api_response.status}"
    },
    {
      "type": "if_end"
    }
  ]
}
```

### Database Integration

```json
{
  "actions": [
    {
      "type": "extract_table",
      "selector": ".data-table",
      "value": {
        "variable": "table_data"
      }
    },
    {
      "type": "database_connect",
      "value": {
        "type": "postgresql",
        "host": "${db_host}",
        "port": "${db_port}",
        "database": "${db_name}",
        "username": "${db_user}",
        "password": "${db_password}",
        "variable": "db_connection"
      }
    },
    {
      "type": "database_insert",
      "value": {
        "connection": "${db_connection}",
        "table": "extracted_data",
        "data": "${table_data}",
        "variable": "insert_result"
      }
    },
    {
      "type": "log_message",
      "value": "Inserted ${insert_result.row_count} rows into database"
    },
    {
      "type": "database_close",
      "value": {
        "connection": "${db_connection}"
      }
    }
  ]
}
```

## Testing and Debugging Automations

### Unit Testing Custom Actions

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from automaton.actions import Action
from automaton.context import ExecutionContext
from your_custom_actions import ScreenshotActionHandler

@pytest.mark.asyncio
async def test_screenshot_action_success():
    # Create mock page
    mock_page = AsyncMock()
    mock_page.screenshot = AsyncMock()
    
    # Create mock context
    mock_context = MagicMock()
    mock_context.page = mock_page
    mock_context.variables = MagicMock()
    
    # Create action handler
    handler = ScreenshotActionHandler()
    
    # Create action
    action = Action(
        type="screenshot",
        value="test_screenshot.png"
    )
    
    # Execute action
    result = await handler.execute(action, mock_context)
    
    # Verify results
    assert result.success is True
    assert "Screenshot saved to test_screenshot.png" in result.message
    mock_page.screenshot.assert_called_once_with(path="test_screenshot.png")

@pytest.mark.asyncio
async def test_screenshot_action_failure():
    # Create mock page that raises an exception
    mock_page = AsyncMock()
    mock_page.screenshot.side_effect = Exception("Screenshot failed")
    
    # Create mock context
    mock_context = MagicMock()
    mock_context.page = mock_page
    mock_context.variables = MagicMock()
    
    # Create action handler
    handler = ScreenshotActionHandler()
    
    # Create action
    action = Action(
        type="screenshot",
        value="test_screenshot.png"
    )
    
    # Execute action
    result = await handler.execute(action, mock_context)
    
    # Verify results
    assert result.success is False
    assert "Failed to take screenshot" in result.message
```

### Debug Mode Configuration

```json
{
  "name": "Debug Example",
  "url": "https://example.com",
  "debug": {
    "enabled": true,
    "screenshots_on_error": true,
    "verbose_logging": true,
    "slow_motion": 1000,
    "highlight_elements": true
  },
  "actions": [
    {
      "type": "input_text",
      "selector": "#search",
      "value": "test query"
    },
    {
      "type": "click_button",
      "selector": "#search-button"
    },
    {
      "type": "wait_for_element",
      "selector": ".search-results"
    }
  ]
}
```

## Best Practices for Complex Automations

### Modular Design

```json
{
  "name": "Main Automation",
  "includes": [
    "modules/login.json",
    "modules/data_extraction.json",
    "modules/data_processing.json",
    "modules/reporting.json"
  ],
  "actions": [
    {
      "type": "execute_module",
      "value": "login"
    },
    {
      "type": "execute_module",
      "value": "data_extraction"
    },
    {
      "type": "execute_module",
      "value": "data_processing"
    },
    {
      "type": "execute_module",
      "value": "reporting"
    }
  ]
}
```

### Configuration Management

```json
{
  "name": "Configurable Automation",
  "config": {
    "base_url": "https://${environment}.example.com",
    "timeout": "${timeout || 30000}",
    "retry_count": "${retry_count || 3}",
    "output_format": "${output_format || 'json'}"
  },
  "actions": [
    {
      "type": "navigate_to",
      "value": "${config.base_url}/data"
    },
    {
      "type": "wait_for_element",
      "selector": ".content",
      "timeout": "${config.timeout}"
    },
    {
      "type": "extract_data",
      "selector": ".data-item",
      "value": {
        "variable": "extracted_data"
      }
    },
    {
      "type": "save_data",
      "value": {
        "data": "${extracted_data}",
        "filename": "output.${config.output_format}"
      }
    }
  ]
}
```

### Error Recovery and Resilience

```json
{
  "name": "Resilient Automation",
  "actions": [
    {
      "type": "set_variable",
      "value": {
        "name": "error_count",
        "value": 0
      }
    },
    {
      "type": "set_variable",
      "value": {
        "name": "max_errors",
        "value": 5
      }
    },
    {
      "type": "try_begin"
    },
    {
      "type": "navigate_to",
      "value": "https://example.com/data"
    },
    {
      "type": "wait_for_element",
      "selector": ".content"
    },
    {
      "type": "extract_data",
      "selector": ".data-item",
      "value": {
        "variable": "extracted_data"
      }
    },
    {
      "type": "catch_begin"
    },
    {
      "type": "increment_variable",
      "value": {
        "name": "error_count",
        "increment": 1
      }
    },
    {
      "type": "log_message",
      "value": "Error occurred (error ${error_count}/${max_errors})"
    },
    {
      "type": "check_variable",
      "value": {
        "variable": "error_count",
        "operator": "<",
        "value": "${max_errors}"
      }
    },
    {
      "type": "if_begin",
      "condition": "check_result",
      "operator": "==",
      "value": true
    },
    {
      "type": "wait",
      "value": 5000
    },
    {
      "type": "log_message",
      "value": "Retrying operation..."
    },
    {
      "type": "continue"
    },
    {
      "type": "if_end"
    },
    {
      "type": "log_message",
      "value": "Max errors reached. Stopping automation."
    },
    {
      "type": "stop_automation"
    },
    {
      "type": "catch_end"
    }
  ]
}
```

## Next Steps

With these advanced techniques mastered, you can:

1. [Review Troubleshooting Techniques](8_troubleshooting_guide.md) for complex issues
2. [Check Contributing Guidelines](9_contributing_guide.md) for extending the framework
3. [Explore Deployment Options](10_deployment_guide.md) for production environments

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](../README.md).*