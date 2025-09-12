# Examples and Tutorials

## Introduction

This section provides practical examples and step-by-step tutorials to help you understand and implement various automation scenarios using Automaton. Each example includes a complete configuration file and detailed explanations of the automation workflow.

## Table of Contents

1. [Getting Started Examples](#getting-started-examples)
2. [Web Scraping Tutorials](#web-scraping-tutorials)
3. [Form Automation Examples](#form-automation-examples)
4. [Testing and Validation Tutorials](#testing-and-validation-tutorials)
5. [Advanced Automation Scenarios](#advanced-automation-scenarios)
6. [Integration Examples](#integration-examples)

## Getting Started Examples

### Basic Navigation and Screenshot

This example demonstrates basic navigation to a website and taking a screenshot.

**Configuration File**:
```json
{
  "name": "Basic Navigation",
  "description": "Navigate to a website and take a screenshot",
  "url": "https://example.com",
  "browser": {
    "type": "chromium",
    "headless": true,
    "viewport": {
      "width": 1280,
      "height": 720
    }
  },
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com",
      "wait_until": "networkidle"
    },
    {
      "type": "wait",
      "duration": 2000
    },
    {
      "type": "screenshot",
      "path": "example_homepage.png"
    }
  ]
}
```

**Explanation**:
1. The automation starts by navigating to `https://example.com`
2. It waits for the network to become idle (all resources loaded)
3. It then waits for an additional 2 seconds to ensure the page is fully rendered
4. Finally, it takes a screenshot and saves it as `example_homepage.png`

### Simple Text Extraction

This example shows how to extract text from a specific element on a page.

**Configuration File**:
```json
{
  "name": "Text Extraction",
  "description": "Extract text from a heading element",
  "url": "https://example.com",
  "browser": {
    "type": "chromium",
    "headless": true
  },
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com"
    },
    {
      "type": "wait",
      "selector": "h1",
      "state": "visible",
      "timeout": 10000
    },
    {
      "type": "extract_text",
      "selector": "h1",
      "variable": "main_heading"
    },
    {
      "type": "screenshot",
      "path": "heading_extraction.png"
    }
  ]
}
```

**Explanation**:
1. Navigate to `https://example.com`
2. Wait for the `h1` element to become visible (up to 10 seconds)
3. Extract the text content from the `h1` element and store it in a variable named `main_heading`
4. Take a screenshot for verification purposes

## Web Scraping Tutorials

### Scraping Product Information

This tutorial demonstrates how to scrape product information from an e-commerce website.

**Configuration File**:
```json
{
  "name": "Product Scraping",
  "description": "Scrape product names and prices from an e-commerce site",
  "url": "https://example-ecommerce.com/products",
  "browser": {
    "type": "chromium",
    "headless": true
  },
  "output_dir": "./scraped_data",
  "actions": [
    {
      "type": "navigate",
      "url": "https://example-ecommerce.com/products",
      "wait_until": "networkidle"
    },
    {
      "type": "wait",
      "selector": ".product-list",
      "state": "visible",
      "timeout": 15000
    },
    {
      "type": "loop",
      "count": 5,
      "actions": [
        {
          "type": "extract_text",
          "selector": ".product-title",
          "variable": "product_name"
        },
        {
          "type": "extract_text",
          "selector": ".product-price",
          "variable": "product_price"
        },
        {
          "type": "screenshot",
          "path": "product_${loop_index}.png"
        },
        {
          "type": "click",
          "selector": ".next-page"
        },
        {
          "type": "wait",
          "duration": 2000
        }
      ]
    }
  ]
}
```

**Explanation**:
1. Navigate to the products page of the e-commerce site
2. Wait for the product list container to be visible
3. Loop 5 times (for 5 pages of products):
   - Extract the product name and store it in a variable
   - Extract the product price and store it in a variable
   - Take a screenshot of each product page
   - Click the "next page" button
   - Wait 2 seconds for the next page to load

### Scraping with Pagination

This tutorial shows how to scrape data from multiple pages with proper pagination handling.

**Configuration File**:
```json
{
  "name": "Pagination Scraping",
  "description": "Scrape articles from a news site with pagination",
  "url": "https://example-news.com/articles",
  "browser": {
    "type": "chromium",
    "headless": true
  },
  "actions": [
    {
      "type": "navigate",
      "url": "https://example-news.com/articles"
    },
    {
      "type": "wait",
      "selector": ".article-list",
      "state": "visible"
    },
    {
      "type": "loop",
      "while": {
        "type": "element_exists",
        "selector": ".next-page:not(.disabled)"
      },
      "actions": [
        {
          "type": "extract_text",
          "selector": ".article-title",
          "variable": "article_title"
        },
        {
          "type": "extract_attribute",
          "selector": ".article-link",
          "attribute": "href",
          "variable": "article_url"
        },
        {
          "type": "extract_text",
          "selector": ".article-summary",
          "variable": "article_summary"
        },
        {
          "type": "click",
          "selector": ".next-page"
        },
        {
          "type": "wait",
          "selector": ".article-list",
          "state": "visible"
        }
      ]
    }
  ]
}
```

**Explanation**:
1. Navigate to the articles page
2. Wait for the article list to be visible
3. Loop while the "next page" button exists and is not disabled:
   - Extract the article title, URL, and summary
   - Click the "next page" button
   - Wait for the new page to load

## Form Automation Examples

### Login Form Automation

This example demonstrates how to automate logging into a website.

**Configuration File**:
```json
{
  "name": "Login Automation",
  "description": "Automate login to a website",
  "url": "https://example.com/login",
  "browser": {
    "type": "chromium",
    "headless": false
  },
  "variables": {
    "username": "user@example.com",
    "password": "securepassword123"
  },
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com/login"
    },
    {
      "type": "wait",
      "selector": "#username",
      "state": "visible"
    },
    {
      "type": "input_text",
      "selector": "#username",
      "value": "${username}",
      "clear_first": true
    },
    {
      "type": "input_text",
      "selector": "#password",
      "value": "${password}",
      "clear_first": true
    },
    {
      "type": "click",
      "selector": "#login-button"
    },
    {
      "type": "wait",
      "duration": 3000
    },
    {
      "type": "if",
      "condition": {
        "type": "element_exists",
        "selector": ".error-message"
      },
      "then": [
        {
          "type": "extract_text",
          "selector": ".error-message",
          "variable": "login_error"
        },
        {
          "type": "screenshot",
          "path": "login_error.png"
        }
      ],
      "else": [
        {
          "type": "screenshot",
          "path": "login_success.png"
        },
        {
          "type": "extract_text",
          "selector": ".welcome-message",
          "variable": "welcome_text"
        }
      ]
    }
  ]
}
```

**Explanation**:
1. Navigate to the login page
2. Wait for the username field to be visible
3. Enter the username and password
4. Click the login button
5. Wait 3 seconds for the page to process the login
6. Check if an error message is displayed:
   - If yes, extract the error message and take a screenshot
   - If no, take a success screenshot and extract the welcome message

### Registration Form Automation

This example shows how to fill out a registration form.

**Configuration File**:
```json
{
  "name": "Registration Form",
  "description": "Automate filling a registration form",
  "url": "https://example.com/register",
  "browser": {
    "type": "chromium",
    "headless": false
  },
  "variables": {
    "email": "newuser@example.com",
    "password": "SecurePass123!",
    "confirm_password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe"
  },
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com/register"
    },
    {
      "type": "wait",
      "selector": "#registration-form",
      "state": "visible"
    },
    {
      "type": "input_text",
      "selector": "#email",
      "value": "${email}"
    },
    {
      "type": "input_text",
      "selector": "#password",
      "value": "${password}"
    },
    {
      "type": "input_text",
      "selector": "#confirm-password",
      "value": "${confirm_password}"
    },
    {
      "type": "input_text",
      "selector": "#first-name",
      "value": "${first_name}"
    },
    {
      "type": "input_text",
      "selector": "#last-name",
      "value": "${last_name}"
    },
    {
      "type": "click",
      "selector": "#terms-checkbox"
    },
    {
      "type": "click",
      "selector": "#register-button"
    },
    {
      "type": "wait",
      "duration": 3000
    },
    {
      "type": "screenshot",
      "path": "registration_result.png"
    }
  ]
}
```

**Explanation**:
1. Navigate to the registration page
2. Wait for the registration form to be visible
3. Fill in all form fields with the provided variables
4. Click the terms and conditions checkbox
5. Click the register button
6. Wait 3 seconds for the registration to process
7. Take a screenshot of the result

## Testing and Validation Tutorials

### Form Validation Testing

This tutorial demonstrates how to test form validation by submitting invalid data.

**Configuration File**:
```json
{
  "name": "Form Validation Testing",
  "description": "Test form validation with various invalid inputs",
  "url": "https://example.com/contact",
  "browser": {
    "type": "chromium",
    "headless": false
  },
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com/contact"
    },
    {
      "type": "wait",
      "selector": "#contact-form",
      "state": "visible"
    },
    {
      "type": "input_text",
      "selector": "#email",
      "value": "invalid-email"
    },
    {
      "type": "click",
      "selector": "#submit-button"
    },
    {
      "type": "wait",
      "duration": 1000
    },
    {
      "type": "if",
      "condition": {
        "type": "element_exists",
        "selector": ".email-error"
      },
      "then": [
        {
          "type": "extract_text",
          "selector": ".email-error",
          "variable": "email_error_message"
        },
        {
          "type": "screenshot",
          "path": "email_validation_error.png"
        }
      ],
      "else": [
        {
          "type": "screenshot",
          "path": "email_validation_missing.png"
        }
      ]
    },
    {
      "type": "input_text",
      "selector": "#email",
      "value": "valid@example.com",
      "clear_first": true
    },
    {
      "type": "input_text",
      "selector": "#message",
      "value": ""
    },
    {
      "type": "click",
      "selector": "#submit-button"
    },
    {
      "type": "wait",
      "duration": 1000
    },
    {
      "type": "if",
      "condition": {
        "type": "element_exists",
        "selector": ".message-error"
      },
      "then": [
        {
          "type": "extract_text",
          "selector": ".message-error",
          "variable": "message_error_message"
        },
        {
          "type": "screenshot",
          "path": "message_validation_error.png"
        }
      ]
    }
  ]
}
```

**Explanation**:
1. Navigate to the contact form
2. Wait for the form to be visible
3. Test email validation by entering an invalid email
4. Check if an error message is displayed and capture it
5. Fix the email and test message validation by leaving it empty
6. Check if an error message is displayed and capture it

### Link Verification

This tutorial shows how to verify that all links on a page are working.

**Configuration File**:
```json
{
  "name": "Link Verification",
  "description": "Check all links on a page to ensure they work",
  "url": "https://example.com",
  "browser": {
    "type": "chromium",
    "headless": true
  },
  "output_dir": "./link_verification",
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com"
    },
    {
      "type": "wait",
      "selector": "body",
      "state": "visible"
    },
    {
      "type": "execute_script",
      "script": "return Array.from(document.querySelectorAll('a[href]')).map(a => a.href);",
      "variable": "all_links"
    },
    {
      "type": "loop",
      "variable": "link",
      "in": "${all_links}",
      "actions": [
        {
          "type": "navigate",
          "url": "${link}",
          "timeout": 10000
        },
        {
          "type": "wait",
          "duration": 2000
        },
        {
          "type": "if",
          "condition": {
            "type": "element_exists",
            "selector": "body"
          },
          "then": [
            {
              "type": "extract_text",
              "selector": "title",
              "variable": "page_title"
            },
            {
              "type": "screenshot",
              "path": "link_${link_index}.png"
            }
          ],
          "else": [
            {
              "type": "screenshot",
              "path": "broken_link_${link_index}.png"
            }
          ]
        },
        {
          "type": "navigate",
          "url": "https://example.com"
        }
      ]
    }
  ]
}
```

**Explanation**:
1. Navigate to the starting page
2. Execute a script to extract all link URLs from the page
3. Loop through each link:
   - Navigate to the link URL
   - Wait for the page to load
   - Check if the page loaded successfully (body element exists)
   - If successful, extract the page title and take a screenshot
   - If not successful, take a screenshot of the broken page
   - Navigate back to the starting page

## Advanced Automation Scenarios

### Data Extraction with Conditional Logic

This example demonstrates extracting data with conditional logic based on page content.

**Configuration File**:
```json
{
  "name": "Conditional Data Extraction",
  "description": "Extract data based on page conditions",
  "url": "https://example-news.com/articles",
  "browser": {
    "type": "chromium",
    "headless": true
  },
  "actions": [
    {
      "type": "navigate",
      "url": "https://example-news.com/articles"
    },
    {
      "type": "wait",
      "selector": ".article-list",
      "state": "visible"
    },
    {
      "type": "loop",
      "count": 10,
      "actions": [
        {
          "type": "extract_text",
          "selector": ".article-title",
          "variable": "article_title"
        },
        {
          "type": "if",
          "condition": {
            "type": "element_exists",
            "selector": ".premium-badge"
          },
          "then": [
            {
              "type": "extract_text",
              "selector": ".article-summary",
              "variable": "article_summary"
            },
            {
              "type": "screenshot",
              "path": "premium_article_${loop_index}.png"
            }
          ],
          "else": [
            {
              "type": "extract_text",
              "selector": ".article-content",
              "variable": "article_content"
            },
            {
              "type": "screenshot",
              "path": "regular_article_${loop_index}.png"
            }
          ]
        },
        {
          "type": "click",
          "selector": ".next-article"
        },
        {
          "type": "wait",
          "selector": ".article-list",
          "state": "visible"
        }
      ]
    }
  ]
}
```

**Explanation**:
1. Navigate to the articles page
2. Loop through 10 articles:
   - Extract the article title
   - Check if the article has a premium badge:
     - If yes, extract the summary and take a screenshot
     - If no, extract the full content and take a screenshot
   - Click to the next article
   - Wait for the page to load

### Multi-Step Workflow with Error Handling

This example shows a complex workflow with error handling at each step.

**Configuration File**:
```json
{
  "name": "Multi-Step Workflow",
  "description": "Complex workflow with error handling",
  "url": "https://example.com",
  "browser": {
    "type": "chromium",
    "headless": false
  },
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com/login",
      "timeout": 15000
    },
    {
      "type": "if",
      "condition": {
        "type": "element_exists",
        "selector": "#username"
      },
      "then": [
        {
          "type": "input_text",
          "selector": "#username",
          "value": "user@example.com"
        },
        {
          "type": "input_text",
          "selector": "#password",
          "value": "password123"
        },
        {
          "type": "click",
          "selector": "#login-button"
        },
        {
          "type": "wait",
          "duration": 3000
        },
        {
          "type": "if",
          "condition": {
            "type": "element_exists",
            "selector": ".error-message"
          },
          "then": [
            {
              "type": "screenshot",
              "path": "login_error.png"
            },
            {
              "type": "extract_text",
              "selector": ".error-message",
              "variable": "error_details"
            }
          ]
        }
      ],
      "else": [
        {
          "type": "screenshot",
          "path": "login_page_not_found.png"
        }
      ]
    },
    {
      "type": "navigate",
      "url": "https://example.com/dashboard"
    },
    {
      "type": "wait",
      "selector": ".dashboard-content",
      "state": "visible",
      "timeout": 10000
    },
    {
      "type": "if",
      "condition": {
        "type": "element_exists",
        "selector": ".notification"
      },
      "then": [
        {
          "type": "extract_text",
          "selector": ".notification",
          "variable": "notification_text"
        },
        {
          "type": "click",
          "selector": ".close-notification"
        }
      ]
    },
    {
      "type": "click",
      "selector": ".reports-link"
    },
    {
      "type": "wait",
      "selector": ".reports-container",
      "state": "visible",
      "timeout": 10000
    },
    {
      "type": "screenshot",
      "path": "reports_page.png"
    },
    {
      "type": "click",
      "selector": ".generate-report-button"
    },
    {
      "type": "wait",
      "selector": ".report-status",
      "state": "visible",
      "timeout": 30000
    },
    {
      "type": "loop",
      "while": {
        "type": "element_text_contains",
        "selector": ".report-status",
        "text": "Generating"
      },
      "actions": [
        {
          "type": "wait",
          "duration": 5000
        },
        {
          "type": "extract_text",
          "selector": ".report-status",
          "variable": "current_status"
        }
      ]
    },
    {
      "type": "screenshot",
      "path": "completed_report.png"
    },
    {
      "type": "click",
      "selector": ".download-report-button"
    },
    {
      "type": "wait",
      "duration": 5000
    }
  ]
}
```

**Explanation**:
1. Navigate to the login page
2. Check if the login form exists and fill it in
3. Check for login errors and capture them if they occur
4. Navigate to the dashboard
5. Check for notifications and handle them
6. Navigate to the reports page
7. Generate a report and wait for it to complete
8. Download the completed report

## Integration Examples

### Automaton with API Integration

This example shows how to integrate Automaton with API calls.

**Configuration File**:
```json
{
  "name": "API Integration",
  "description": "Extract data and send it to an API",
  "url": "https://example.com/products",
  "browser": {
    "type": "chromium",
    "headless": true
  },
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com/products"
    },
    {
      "type": "wait",
      "selector": ".product-list",
      "state": "visible"
    },
    {
      "type": "loop",
      "count": 5,
      "actions": [
        {
          "type": "extract_text",
          "selector": ".product-name",
          "variable": "product_name"
        },
        {
          "type": "extract_text",
          "selector": ".product-price",
          "variable": "product_price"
        },
        {
          "type": "extract_attribute",
          "selector": ".product-link",
          "attribute": "href",
          "variable": "product_url"
        },
        {
          "type": "http_request",
          "method": "POST",
          "url": "https://api.example.com/products",
          "headers": {
            "Content-Type": "application/json",
            "Authorization": "Bearer your_api_token"
          },
          "body": {
            "name": "${product_name}",
            "price": "${product_price}",
            "url": "${product_url}"
          },
          "variable": "api_response"
        },
        {
          "type": "if",
          "condition": {
            "type": "variable_equals",
            "variable": "api_response.status",
            "value": 200
          },
          "then": [
            {
              "type": "log",
              "message": "Successfully sent product data: ${product_name}",
              "level": "info"
            }
          ],
          "else": [
            {
              "type": "log",
              "message": "Failed to send product data: ${product_name}. Status: ${api_response.status}",
              "level": "error"
            }
          ]
        },
        {
          "type": "click",
          "selector": ".next-page"
        },
        {
          "type": "wait",
          "selector": ".product-list",
          "state": "visible"
        }
      ]
    }
  ]
}
```

**Explanation**:
1. Navigate to the products page
2. Loop through 5 pages of products:
   - Extract the product name, price, and URL
   - Send this data to an API endpoint
   - Log the success or failure of the API call
   - Navigate to the next page

### Automaton with Database Integration

This example demonstrates how to save extracted data to a database.

**Configuration File**:
```json
{
  "name": "Database Integration",
  "description": "Extract data and save it to a database",
  "url": "https://example.com/articles",
  "browser": {
    "type": "chromium",
    "headless": true
  },
  "actions": [
    {
      "type": "navigate",
      "url": "https://example.com/articles"
    },
    {
      "type": "wait",
      "selector": ".article-list",
      "state": "visible"
    },
    {
      "type": "loop",
      "count": 10,
      "actions": [
        {
          "type": "extract_text",
          "selector": ".article-title",
          "variable": "article_title"
        },
        {
          "type": "extract_text",
          "selector": ".article-author",
          "variable": "article_author"
        },
        {
          "type": "extract_text",
          "selector": ".article-date",
          "variable": "article_date"
        },
        {
          "type": "extract_text",
          "selector": ".article-content",
          "variable": "article_content"
        },
        {
          "type": "database_query",
          "connection": "postgresql://user:password@localhost:5432/articles_db",
          "query": "INSERT INTO articles (title, author, date, content) VALUES ($1, $2, $3, $4) RETURNING id",
          "parameters": [
            "${article_title}",
            "${article_author}",
            "${article_date}",
            "${article_content}"
          ],
          "variable": "insert_result"
        },
        {
          "type": "if",
          "condition": {
            "type": "variable_exists",
            "variable": "insert_result.rows[0].id"
          },
          "then": [
            {
              "type": "log",
              "message": "Article saved with ID: ${insert_result.rows[0].id}",
              "level": "info"
            }
          ],
          "else": [
            {
              "type": "log",
              "message": "Failed to save article: ${article_title}",
              "level": "error"
            }
          ]
        },
        {
          "type": "click",
          "selector": ".next-page"
        },
        {
          "type": "wait",
          "selector": ".article-list",
          "state": "visible"
        }
      ]
    }
  ]
}
```

**Explanation**:
1. Navigate to the articles page
2. Loop through 10 pages of articles:
   - Extract the article title, author, date, and content
   - Insert this data into a PostgreSQL database
   - Log the success or failure of the database operation
   - Navigate to the next page

## Next Steps

1. Experiment with these examples by modifying them to suit your specific needs
2. Combine elements from different examples to create more complex automations
3. Refer to the [Configuration Reference](19_configuration_reference.md) for more details on configuration options
4. Check the [Advanced Usage](7_advanced_usage.md) guide for more sophisticated automation techniques

---

*This document is part of the Automaton documentation series. For a complete list of documentation, see the [main README](README.md).*