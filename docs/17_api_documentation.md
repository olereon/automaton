# API Documentation

## Introduction

This section provides comprehensive API documentation for Automaton, covering all available endpoints, methods, parameters, and response formats. The documentation is organized by functional categories to help you quickly find the information you need.

## Table of Contents

1. [Authentication](#authentication)
2. [Automation Endpoints](#automation-endpoints)
3. [Browser Management](#browser-management)
4. [Element Interaction](#element-interaction)
5. [Data Extraction](#data-extraction)
6. [Flow Control](#flow-control)
7. [Error Handling](#error-handling)
8. [Response Formats](#response-formats)

## Authentication

Automaton API uses API key authentication for secure access. Include your API key in the request headers for all API calls.

### Header Format

```
Authorization: Bearer YOUR_API_KEY
```

### Example

```bash
curl -X GET "https://api.automaton.example.com/v1/automations" \
     -H "Authorization: Bearer your_api_key_here"
```

## Automation Endpoints

### List Automations

Retrieve a list of all available automations.

**Endpoint**: `GET /v1/automations`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| limit | integer | No | Maximum number of results to return |
| offset | integer | No | Number of results to skip for pagination |

**Response**:
```json
{
  "success": true,
  "data": [
    {
      "id": "automation_1",
      "name": "Login Automation",
      "description": "Automated login process",
      "created_at": "2023-01-15T10:30:00Z",
      "updated_at": "2023-01-20T14:45:00Z"
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 10,
    "offset": 0
  }
}
```

### Get Automation

Retrieve details of a specific automation.

**Endpoint**: `GET /v1/automations/{id}`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | Yes | Automation ID |

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "automation_1",
    "name": "Login Automation",
    "description": "Automated login process",
    "actions": [
      {
        "type": "navigate",
        "url": "https://example.com/login"
      },
      {
        "type": "input_text",
        "selector": "#username",
        "value": "user@example.com"
      }
    ],
    "created_at": "2023-01-15T10:30:00Z",
    "updated_at": "2023-01-20T14:45:00Z"
  }
}
```

### Create Automation

Create a new automation.

**Endpoint**: `POST /v1/automations`

**Request Body**:
```json
{
  "name": "New Automation",
  "description": "Description of the automation",
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com"
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "automation_2",
    "name": "New Automation",
    "description": "Description of the automation",
    "actions": [
      {
        "type": "navigate",
        "url": "https://example.com"
      }
    ],
    "created_at": "2023-01-25T09:15:00Z",
    "updated_at": "2023-01-25T09:15:00Z"
  }
}
```

### Update Automation

Update an existing automation.

**Endpoint**: `PUT /v1/automations/{id}`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | Yes | Automation ID |

**Request Body**:
```json
{
  "name": "Updated Automation",
  "description": "Updated description",
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com"
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "id": "automation_1",
    "name": "Updated Automation",
    "description": "Updated description",
    "actions": [
      {
        "type": "navigate",
        "url": "https://example.com"
      }
    ],
    "created_at": "2023-01-15T10:30:00Z",
    "updated_at": "2023-01-25T10:20:00Z"
  }
}
```

### Delete Automation

Delete an automation.

**Endpoint**: `DELETE /v1/automations/{id}`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | Yes | Automation ID |

**Response**:
```json
{
  "success": true,
  "message": "Automation deleted successfully"
}
```

### Run Automation

Execute an automation.

**Endpoint**: `POST /v1/automations/{id}/run`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| id | string | Yes | Automation ID |
| parameters | object | No | Runtime parameters for the automation |

**Request Body**:
```json
{
  "parameters": {
    "username": "user@example.com",
    "password": "securepassword"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "execution_id": "exec_12345",
    "status": "running",
    "started_at": "2023-01-25T11:30:00Z",
    "automation_id": "automation_1"
  }
}
```

## Browser Management

### Create Browser Session

Create a new browser session for automation.

**Endpoint**: `POST /v1/browser/sessions`

**Request Body**:
```json
{
  "browser_type": "chromium",
  "headless": true,
  "viewport": {
    "width": 1920,
    "height": 1080
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "session_id": "session_12345",
    "browser_type": "chromium",
    "headless": true,
    "viewport": {
      "width": 1920,
      "height": 1080
    },
    "created_at": "2023-01-25T11:35:00Z"
  }
}
```

### Get Browser Session

Retrieve details of a browser session.

**Endpoint**: `GET /v1/browser/sessions/{session_id}`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | Browser session ID |

**Response**:
```json
{
  "success": true,
  "data": {
    "session_id": "session_12345",
    "browser_type": "chromium",
    "headless": true,
    "viewport": {
      "width": 1920,
      "height": 1080
    },
    "status": "active",
    "created_at": "2023-01-25T11:35:00Z",
    "last_activity": "2023-01-25T11:40:00Z"
  }
}
```

### Close Browser Session

Close a browser session.

**Endpoint**: `DELETE /v1/browser/sessions/{session_id}`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| session_id | string | Yes | Browser session ID |

**Response**:
```json
{
  "success": true,
  "message": "Browser session closed successfully"
}
```

## Element Interaction

### Find Element

Find an element on the page.

**Endpoint**: `POST /v1/elements/find`

**Request Body**:
```json
{
  "session_id": "session_12345",
  "selector": "#submit-button",
  "timeout": 5000
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "element_id": "element_67890",
    "selector": "#submit-button",
    "tag_name": "button",
    "text": "Submit",
    "visible": true,
    "enabled": true,
    "rect": {
      "x": 100,
      "y": 200,
      "width": 80,
      "height": 30
    }
  }
}
```

### Click Element

Click on an element.

**Endpoint**: `POST /v1/elements/{element_id}/click`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| element_id | string | Yes | Element ID |

**Request Body**:
```json
{
  "session_id": "session_12345"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Element clicked successfully"
}
```

### Input Text

Enter text into an input field.

**Endpoint**: `POST /v1/elements/{element_id}/input`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| element_id | string | Yes | Element ID |

**Request Body**:
```json
{
  "session_id": "session_12345",
  "text": "example text",
  "clear_first": true
}
```

**Response**:
```json
{
  "success": true,
  "message": "Text input successfully"
}
```

## Data Extraction

### Extract Text

Extract text from an element.

**Endpoint**: `GET /v1/elements/{element_id}/text`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| element_id | string | Yes | Element ID |

**Request Body**:
```json
{
  "session_id": "session_12345"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "text": "Example text content"
  }
}
```

### Extract Attribute

Extract an attribute value from an element.

**Endpoint**: `GET /v1/elements/{element_id}/attribute`

**Parameters**:
| Name | Type | Required | Description |
|------|------|----------|-------------|
| element_id | string | Yes | Element ID |

**Request Body**:
```json
{
  "session_id": "session_12345",
  "attribute_name": "href"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "attribute_value": "https://example.com/page"
  }
}
```

### Screenshot

Take a screenshot of the current page or an element.

**Endpoint**: `POST /v1/browser/screenshot`

**Request Body**:
```json
{
  "session_id": "session_12345",
  "element_id": "element_67890",
  "format": "png"
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "screenshot_id": "screenshot_54321",
    "format": "png",
    "size": 24576,
    "taken_at": "2023-01-25T11:45:00Z"
  }
}
```

## Flow Control

### Wait

Wait for a specified amount of time or condition.

**Endpoint**: `POST /v1/flow/wait`

**Request Body**:
```json
{
  "session_id": "session_12345",
  "type": "time",
  "duration": 2000
}
```

**Response**:
```json
{
  "success": true,
  "message": "Wait completed successfully"
}
```

### Conditional Execution

Execute actions based on conditions.

**Endpoint**: `POST /v1/flow/if`

**Request Body**:
```json
{
  "session_id": "session_12345",
  "condition": {
    "type": "element_exists",
    "selector": "#success-message"
  },
  "then": [
    {
      "type": "click",
      "selector": "#continue-button"
    }
  ],
  "else": [
    {
      "type": "click",
      "selector": "#retry-button"
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "condition_met": true,
    "executed_branch": "then"
  }
}
```

## Error Handling

### Error Response Format

All API endpoints return errors in a consistent format:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "additional": "error information"
    }
  }
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| INVALID_REQUEST | The request is malformed or missing required parameters |
| UNAUTHORIZED | Authentication failed or API key is invalid |
| FORBIDDEN | The authenticated user does not have permission to access the resource |
| NOT_FOUND | The requested resource does not exist |
| SESSION_EXPIRED | The browser session has expired or is invalid |
| ELEMENT_NOT_FOUND | The requested element could not be found on the page |
| TIMEOUT | The operation timed out |
| INTERNAL_ERROR | An unexpected error occurred on the server |

## Response Formats

### Success Response

All successful API responses follow this format:

```json
{
  "success": true,
  "data": {
    // Response data specific to the endpoint
  },
  "message": "Optional success message"
}
```

### Pagination Response

Endpoints that return lists of items use this pagination format:

```json
{
  "success": true,
  "data": [
    // Array of items
  ],
  "pagination": {
    "total": 100,
    "limit": 10,
    "offset": 0
  }
}
```

### Execution Response

Endpoints that trigger long-running operations return an execution response:

```json
{
  "success": true,
  "data": {
    "execution_id": "exec_12345",
    "status": "running|completed|failed",
    "started_at": "2023-01-25T11:30:00Z",
    "completed_at": "2023-01-25T11:35:00Z", // Only if status is completed or failed
    "result": {
      // Execution results (only if status is completed)
    },
    "error": {
      // Error information (only if status is failed)
    }
  }
}
```

## Rate Limiting

API requests are rate limited to ensure fair usage:

- **Default Limit**: 100 requests per minute
- **Burst Limit**: 200 requests per minute

Rate limit headers are included in all API responses:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1643089200
```

When the rate limit is exceeded, the API returns a 429 status code:

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "API rate limit exceeded",
    "details": {
      "retry_after": 60
    }
  }
}
```

## Versioning

The API uses semantic versioning. Include the API version in all request URLs:

```
https://api.automaton.example.com/v1/endpoint
```

Current version: v1

## Next Steps

1. Explore the [Action Types Reference](ACTION_TYPES_REFERENCE.md) for detailed information on all available actions
2. Check the [Advanced Usage](7_advanced_usage.md) guide for complex API usage patterns
3. Refer to the [Troubleshooting Guide](8_troubleshooting_guide.md) for common API issues

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](README.md).*