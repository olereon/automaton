#!/usr/bin/env python3
"""
Mock Fixtures for GUI Tabs Testing
Provides realistic test data and mock objects for comprehensive GUI tabs testing.

FIXTURE CATEGORIES:
1. HTML Content Fixtures - Various complexity levels
2. Action Sequence Fixtures - Different workflow patterns
3. Selector Recommendation Fixtures - Different strategies
4. Performance Test Fixtures - Scalable test data
5. Error Scenario Fixtures - Edge cases and failures

These fixtures support consistent testing across all test modules.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Any
import random

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.engine import ActionType, Action

@dataclass
class HTMLFixture:
    """HTML content fixture with metadata"""
    name: str
    content: str
    complexity: str  # simple, medium, complex
    expected_elements: int
    expected_clickable: int
    description: str

@dataclass
class ActionSequenceFixture:
    """Action sequence fixture with metadata"""
    name: str
    actions: List[Action]
    workflow_type: str  # login, ecommerce, form, navigation
    expected_duration: float
    description: str

@dataclass
class SelectorFixture:
    """Selector recommendation fixture"""
    selector: str
    strategy: str
    confidence: int
    element_type: str
    description: str

class HTMLContentFixtures:
    """Collection of HTML content fixtures for testing"""
    
    @staticmethod
    def get_simple_login_form():
        """Simple login form HTML"""
        return HTMLFixture(
            name="simple_login_form",
            content="""
            <!DOCTYPE html>
            <html>
            <head><title>Simple Login</title></head>
            <body>
                <form id="login">
                    <input type="email" id="email" name="email" placeholder="Email" required>
                    <input type="password" id="password" name="password" placeholder="Password" required>
                    <button type="submit" id="submit-btn">Login</button>
                </form>
                <div id="message" style="display:none;"></div>
            </body>
            </html>
            """,
            complexity="simple",
            expected_elements=6,
            expected_clickable=1,
            description="Basic login form with email, password, and submit button"
        )
    
    @staticmethod
    def get_medium_ecommerce_page():
        """Medium complexity e-commerce page"""
        return HTMLFixture(
            name="medium_ecommerce_page",
            content="""
            <!DOCTYPE html>
            <html>
            <head><title>Product Page</title></head>
            <body>
                <div class="product-page">
                    <header class="site-header">
                        <nav class="navbar">
                            <a href="#" class="nav-link">Home</a>
                            <a href="#" class="nav-link">Products</a>
                            <a href="#" class="nav-link">Cart (<span id="cart-count">0</span>)</a>
                        </nav>
                    </header>
                    <main class="product-details">
                        <h1 class="product-title">Sample Product</h1>
                        <div class="product-price">$49.99</div>
                        <div class="product-options">
                            <label for="size">Size:</label>
                            <select id="size" name="size" class="form-select">
                                <option value="">Choose Size</option>
                                <option value="small">Small</option>
                                <option value="medium">Medium</option>
                                <option value="large">Large</option>
                            </select>
                            <label for="color">Color:</label>
                            <select id="color" name="color" class="form-select">
                                <option value="">Choose Color</option>
                                <option value="red">Red</option>
                                <option value="blue">Blue</option>
                                <option value="green">Green</option>
                            </select>
                        </div>
                        <div class="quantity-section">
                            <label for="quantity">Quantity:</label>
                            <input type="number" id="quantity" name="quantity" value="1" min="1" max="10" class="form-input">
                        </div>
                        <div class="action-buttons">
                            <button id="add-to-cart" class="btn btn-primary">Add to Cart</button>
                            <button id="buy-now" class="btn btn-success">Buy Now</button>
                            <button id="add-wishlist" class="btn btn-secondary">Add to Wishlist</button>
                        </div>
                        <div class="product-tabs">
                            <button class="tab-btn active" data-tab="description">Description</button>
                            <button class="tab-btn" data-tab="reviews">Reviews</button>
                            <button class="tab-btn" data-tab="shipping">Shipping</button>
                        </div>
                        <div class="tab-content">
                            <div id="description-tab" class="tab-pane active">Product description content...</div>
                            <div id="reviews-tab" class="tab-pane">Customer reviews...</div>
                            <div id="shipping-tab" class="tab-pane">Shipping information...</div>
                        </div>
                    </main>
                    <div id="notification" class="alert" style="display:none;">
                        <span class="message"></span>
                        <button class="close-btn">&times;</button>
                    </div>
                </div>
            </body>
            </html>
            """,
            complexity="medium",
            expected_elements=35,
            expected_clickable=9,
            description="E-commerce product page with options, tabs, and notifications"
        )
    
    @staticmethod
    def get_complex_dashboard():
        """Complex dashboard HTML with dynamic elements"""
        return HTMLFixture(
            name="complex_dashboard",
            content="""
            <!DOCTYPE html>
            <html>
            <head><title>Admin Dashboard</title></head>
            <body>
                <div class="dashboard-app">
                    <aside class="sidebar">
                        <div class="sidebar-header">
                            <h2>Admin Panel</h2>
                        </div>
                        <nav class="sidebar-nav">
                            <a href="#dashboard" class="nav-item active" data-section="dashboard">
                                <i class="icon-dashboard"></i> Dashboard
                            </a>
                            <a href="#users" class="nav-item" data-section="users">
                                <i class="icon-users"></i> Users
                            </a>
                            <a href="#products" class="nav-item" data-section="products">
                                <i class="icon-products"></i> Products
                            </a>
                            <a href="#orders" class="nav-item" data-section="orders">
                                <i class="icon-orders"></i> Orders
                            </a>
                            <a href="#settings" class="nav-item" data-section="settings">
                                <i class="icon-settings"></i> Settings
                            </a>
                        </nav>
                    </aside>
                    <main class="main-content">
                        <header class="main-header">
                            <div class="header-title">
                                <h1 id="page-title">Dashboard Overview</h1>
                            </div>
                            <div class="header-actions">
                                <button class="btn btn-outline refresh-btn" data-action="refresh">
                                    <i class="icon-refresh"></i> Refresh
                                </button>
                                <div class="dropdown user-menu">
                                    <button class="dropdown-toggle" data-toggle="dropdown">
                                        <i class="icon-user"></i> Admin
                                    </button>
                                    <div class="dropdown-menu">
                                        <a href="#profile" class="dropdown-item">Profile</a>
                                        <a href="#logout" class="dropdown-item">Logout</a>
                                    </div>
                                </div>
                            </div>
                        </header>
                        <section class="content-area">
                            <div class="dashboard-widgets">
                                <div class="widget stat-widget">
                                    <h3>Total Users</h3>
                                    <div class="stat-number" data-stat="users">1,245</div>
                                </div>
                                <div class="widget stat-widget">
                                    <h3>Total Orders</h3>
                                    <div class="stat-number" data-stat="orders">834</div>
                                </div>
                                <div class="widget stat-widget">
                                    <h3>Revenue</h3>
                                    <div class="stat-number" data-stat="revenue">$45,678</div>
                                </div>
                            </div>
                            <div class="data-section">
                                <div class="section-header">
                                    <h2>Recent Activity</h2>
                                    <div class="section-controls">
                                        <input type="search" class="search-input" placeholder="Search activities...">
                                        <select class="filter-select">
                                            <option value="">All Activities</option>
                                            <option value="users">User Actions</option>
                                            <option value="orders">Order Updates</option>
                                            <option value="system">System Events</option>
                                        </select>
                                        <button class="btn btn-primary export-btn">Export</button>
                                    </div>
                                </div>
                                <div class="data-table-container">
                                    <table class="data-table">
                                        <thead>
                                            <tr>
                                                <th>Time</th>
                                                <th>Type</th>
                                                <th>Description</th>
                                                <th>User</th>
                                                <th>Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody id="activity-table">
                                            <tr class="table-row" data-id="1">
                                                <td>10:30 AM</td>
                                                <td><span class="badge badge-info">User</span></td>
                                                <td>User registration completed</td>
                                                <td>john.doe@example.com</td>
                                                <td>
                                                    <button class="btn btn-sm view-btn" data-id="1" data-action="view">View</button>
                                                    <button class="btn btn-sm edit-btn" data-id="1" data-action="edit">Edit</button>
                                                </td>
                                            </tr>
                                            <tr class="table-row" data-id="2">
                                                <td>10:25 AM</td>
                                                <td><span class="badge badge-success">Order</span></td>
                                                <td>Order #1234 completed</td>
                                                <td>jane.smith@example.com</td>
                                                <td>
                                                    <button class="btn btn-sm view-btn" data-id="2" data-action="view">View</button>
                                                    <button class="btn btn-sm edit-btn" data-id="2" data-action="edit">Edit</button>
                                                </td>
                                            </tr>
                                        </tbody>
                                    </table>
                                    <div class="pagination">
                                        <button class="page-btn prev-btn" data-page="prev">Previous</button>
                                        <span class="page-info">Page 1 of 25</span>
                                        <button class="page-btn next-btn" data-page="next">Next</button>
                                    </div>
                                </div>
                            </div>
                        </section>
                    </main>
                    <div id="modal-overlay" class="modal-overlay" style="display:none;">
                        <div class="modal-dialog">
                            <div class="modal-header">
                                <h3 id="modal-title">Modal Title</h3>
                                <button class="modal-close">&times;</button>
                            </div>
                            <div class="modal-body" id="modal-body">
                                Modal content goes here...
                            </div>
                            <div class="modal-footer">
                                <button class="btn btn-secondary cancel-btn">Cancel</button>
                                <button class="btn btn-primary confirm-btn">Confirm</button>
                            </div>
                        </div>
                    </div>
                    <div id="loading-overlay" class="loading-overlay" style="display:none;">
                        <div class="loading-spinner">
                            <div class="spinner"></div>
                            <div class="loading-text">Loading...</div>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """,
            complexity="complex",
            expected_elements=75,
            expected_clickable=20,
            description="Complex admin dashboard with navigation, tables, modals, and dynamic content"
        )

class ActionSequenceFixtures:
    """Collection of action sequence fixtures for testing"""
    
    @staticmethod
    def get_simple_login_workflow():
        """Simple login workflow actions"""
        actions = [
            Action(ActionType.INPUT_TEXT, "Enter email", "#email", "test@example.com"),
            Action(ActionType.INPUT_TEXT, "Enter password", "#password", "password123"),
            Action(ActionType.CLICK_BUTTON, "Click login", "#submit-btn"),
            Action(ActionType.CHECK_ELEMENT, "Verify success", "#message", 
                  {'check': 'contains', 'value': 'success'})
        ]
        
        return ActionSequenceFixture(
            name="simple_login_workflow",
            actions=actions,
            workflow_type="login",
            expected_duration=2.0,
            description="Basic login workflow with validation"
        )
    
    @staticmethod
    def get_ecommerce_purchase_workflow():
        """E-commerce purchase workflow actions"""
        actions = [
            Action(ActionType.INPUT_TEXT, "Select size", "#size", "medium"),
            Action(ActionType.INPUT_TEXT, "Select color", "#color", "blue"),
            Action(ActionType.INPUT_TEXT, "Set quantity", "#quantity", "2"),
            Action(ActionType.CLICK_BUTTON, "Add to cart", "#add-to-cart"),
            Action(ActionType.CHECK_ELEMENT, "Verify cart notification", "#notification",
                  {'check': 'visible', 'value': 'true'}),
            Action(ActionType.WAIT, "Wait for notification", timeout=2000),
            Action(ActionType.CLICK_BUTTON, "Close notification", ".close-btn"),
            Action(ActionType.CLICK_BUTTON, "Go to cart", "[href*='cart']"),
            Action(ActionType.CHECK_ELEMENT, "Verify cart count", "#cart-count",
                  {'check': 'equals', 'value': '2'})
        ]
        
        return ActionSequenceFixture(
            name="ecommerce_purchase_workflow",
            actions=actions,
            workflow_type="ecommerce",
            expected_duration=5.0,
            description="Complete e-commerce purchase workflow"
        )
    
    @staticmethod
    def get_complex_dashboard_workflow():
        """Complex dashboard navigation workflow"""
        actions = [
            Action(ActionType.WAIT_FOR_ELEMENT, "Wait for dashboard", ".dashboard-app"),
            Action(ActionType.CLICK_BUTTON, "Navigate to users", "[data-section='users']"),
            Action(ActionType.CHECK_ELEMENT, "Verify users page", "#page-title",
                  {'check': 'contains', 'value': 'Users'}),
            Action(ActionType.INPUT_TEXT, "Search activities", ".search-input", "user registration"),
            Action(ActionType.INPUT_TEXT, "Filter by users", ".filter-select", "users"),
            Action(ActionType.WAIT, "Wait for filter", timeout=1000),
            Action(ActionType.CLICK_BUTTON, "View first item", ".view-btn[data-id='1']"),
            Action(ActionType.WAIT_FOR_ELEMENT, "Wait for modal", "#modal-overlay"),
            Action(ActionType.CHECK_ELEMENT, "Verify modal opened", "#modal-overlay",
                  {'check': 'visible', 'value': 'true'}),
            Action(ActionType.CLICK_BUTTON, "Close modal", ".modal-close"),
            Action(ActionType.CHECK_ELEMENT, "Verify modal closed", "#modal-overlay",
                  {'check': 'not_visible', 'value': 'true'}),
            Action(ActionType.CLICK_BUTTON, "Refresh data", ".refresh-btn"),
            Action(ActionType.CHECK_ELEMENT, "Verify refresh", ".loading-overlay",
                  {'check': 'visible', 'value': 'true'})
        ]
        
        return ActionSequenceFixture(
            name="complex_dashboard_workflow",
            actions=actions,
            workflow_type="navigation",
            expected_duration=8.0,
            description="Complex dashboard navigation and interaction workflow"
        )

class SelectorFixtures:
    """Collection of selector recommendation fixtures"""
    
    @staticmethod
    def get_high_confidence_selectors():
        """High confidence selector recommendations"""
        return [
            SelectorFixture("#email", "ID-based", 95, "input", "Email input by ID"),
            SelectorFixture("#submit-btn", "ID-based", 92, "button", "Submit button by ID"),
            SelectorFixture("[data-testid='login']", "Attribute-based", 88, "form", "Form by test ID"),
            SelectorFixture(".btn-primary", "Class-based", 85, "button", "Primary button by class")
        ]
    
    @staticmethod
    def get_medium_confidence_selectors():
        """Medium confidence selector recommendations"""
        return [
            SelectorFixture(".form-input", "Class-based", 75, "input", "Form input by class"),
            SelectorFixture("button[type='submit']", "Attribute-based", 78, "button", "Submit button by type"),
            SelectorFixture("form > div:nth-child(3) > button", "Path-based", 70, "button", "Button by path"),
            SelectorFixture(".nav-item.active", "Multi-class", 72, "link", "Active navigation item")
        ]
    
    @staticmethod
    def get_low_confidence_selectors():
        """Low confidence selector recommendations"""
        return [
            SelectorFixture("div > button", "Path-based", 45, "button", "Generic button path"),
            SelectorFixture(".btn", "Class-based", 50, "button", "Generic button class"),
            SelectorFixture("*[onclick]", "Attribute-based", 40, "any", "Any clickable element"),
            SelectorFixture("button:contains('Submit')", "Text-based", 55, "button", "Button by text")
        ]

class PerformanceTestFixtures:
    """Fixtures for performance testing with scalable data"""
    
    @staticmethod
    def generate_large_html_content(element_count=500):
        """Generate large HTML content for performance testing"""
        elements = []
        for i in range(element_count):
            elements.append(f"""
            <div class="item-{i % 10}" data-id="{i}">
                <header class="item-header-{i % 5}">
                    <h3 class="title title-{i % 3}">Item {i}</h3>
                    <span class="badge badge-{i % 4}">Category {i % 8}</span>
                </header>
                <div class="item-content">
                    <p class="description">Description for item {i}</p>
                    <div class="item-meta" data-created="{i}" data-priority="{i % 5}">
                        <span class="author">Author {i % 20}</span>
                        <span class="date">2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}</span>
                    </div>
                    <div class="item-actions">
                        <button class="btn btn-view view-{i}" data-id="{i}" data-action="view">View</button>
                        <button class="btn btn-edit edit-{i}" data-id="{i}" data-action="edit">Edit</button>
                        <button class="btn btn-delete delete-{i}" data-id="{i}" data-action="delete">Delete</button>
                    </div>
                </div>
            </div>
            """)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head><title>Performance Test Page</title></head>
        <body>
            <div class="performance-test-container">
                <header class="page-header">
                    <h1>Performance Test Page ({element_count} items)</h1>
                    <div class="controls">
                        <input type="search" id="search" placeholder="Search items...">
                        <select id="filter" class="filter-select">
                            <option value="">All Categories</option>
                            {"".join([f'<option value="{i}">Category {i}</option>' for i in range(8)])}
                        </select>
                        <button id="refresh" class="btn btn-primary">Refresh</button>
                    </div>
                </header>
                <main class="items-container">
                    {"".join(elements)}
                </main>
                <footer class="page-footer">
                    <div class="pagination">
                        <button class="page-btn" data-page="prev">Previous</button>
                        <span class="page-info">Page 1 of {(element_count // 50) + 1}</span>
                        <button class="page-btn" data-page="next">Next</button>
                    </div>
                </footer>
            </div>
        </body>
        </html>
        """
        
        return HTMLFixture(
            name=f"performance_test_{element_count}",
            content=html_content,
            complexity="complex",
            expected_elements=element_count * 8 + 10,  # Approximate
            expected_clickable=element_count * 3 + 4,  # 3 buttons per item + controls
            description=f"Performance test HTML with {element_count} items"
        )
    
    @staticmethod
    def generate_large_action_sequence(action_count=100):
        """Generate large action sequence for performance testing"""
        actions = []
        action_types = [ActionType.CLICK_BUTTON, ActionType.INPUT_TEXT, 
                       ActionType.CHECK_ELEMENT, ActionType.WAIT]
        
        for i in range(action_count):
            action_type = action_types[i % len(action_types)]
            
            if action_type == ActionType.INPUT_TEXT:
                action = Action(action_type, f"Input action {i}", f"#input-{i}", f"value-{i}")
            elif action_type == ActionType.CHECK_ELEMENT:
                action = Action(action_type, f"Check action {i}", f".check-{i}",
                              {'check': 'equals', 'value': f'expected-{i}'})
            elif action_type == ActionType.WAIT:
                action = Action(action_type, f"Wait action {i}", timeout=500 + (i % 10) * 100)
            else:  # CLICK_BUTTON
                action = Action(action_type, f"Click action {i}", f".btn-{i}")
            
            actions.append(action)
        
        return ActionSequenceFixture(
            name=f"performance_test_{action_count}_actions",
            actions=actions,
            workflow_type="performance",
            expected_duration=action_count * 0.1,  # 100ms per action estimate
            description=f"Performance test with {action_count} actions"
        )

class ErrorScenarioFixtures:
    """Fixtures for testing error scenarios and edge cases"""
    
    @staticmethod
    def get_malformed_html():
        """Malformed HTML for error handling tests"""
        return HTMLFixture(
            name="malformed_html",
            content="""
            <html>
            <head><title>Malformed HTML</title>
            <body>
                <div class="container">
                    <form id="broken-form"
                        <input type="text" id="unclosed-input" name="test"
                        <button type="submit" id="submit-btn">Submit
                        <div class="nested-div">
                            <p>Unclosed paragraph
                            <span>Unclosed span
                        </div>
                    </form>
                <!-- Unclosed comment
                </div>
            </body>
            """,
            complexity="simple",
            expected_elements=8,
            expected_clickable=1,
            description="Malformed HTML with unclosed tags and syntax errors"
        )
    
    @staticmethod
    def get_empty_html():
        """Empty HTML for edge case testing"""
        return HTMLFixture(
            name="empty_html",
            content="",
            complexity="simple",
            expected_elements=0,
            expected_clickable=0,
            description="Empty HTML content for edge case testing"
        )
    
    @staticmethod
    def get_invalid_action_sequence():
        """Action sequence with invalid configurations"""
        actions = [
            Action(ActionType.INPUT_TEXT, "Invalid selector", ">>>invalid<<<", "test"),
            Action(ActionType.CLICK_BUTTON, "Missing selector", "", timeout=-1000),
            Action(ActionType.CHECK_ELEMENT, "Invalid check", ".test",
                  {'check': 'invalid_check_type', 'value': None}),
            Action(ActionType.WAIT, "Invalid wait", timeout=-5000),
        ]
        
        return ActionSequenceFixture(
            name="invalid_action_sequence",
            actions=actions,
            workflow_type="error",
            expected_duration=0.0,
            description="Action sequence with invalid configurations for error testing"
        )

# Main fixture registry
class FixtureRegistry:
    """Central registry for all test fixtures"""
    
    def __init__(self):
        self.html_fixtures = {}
        self.action_fixtures = {}
        self.selector_fixtures = {}
        self._register_all_fixtures()
    
    def _register_all_fixtures(self):
        """Register all available fixtures"""
        # HTML fixtures
        self.html_fixtures.update({
            'simple_login': HTMLContentFixtures.get_simple_login_form(),
            'medium_ecommerce': HTMLContentFixtures.get_medium_ecommerce_page(),
            'complex_dashboard': HTMLContentFixtures.get_complex_dashboard(),
            'malformed_html': ErrorScenarioFixtures.get_malformed_html(),
            'empty_html': ErrorScenarioFixtures.get_empty_html()
        })
        
        # Action sequence fixtures
        self.action_fixtures.update({
            'simple_login': ActionSequenceFixtures.get_simple_login_workflow(),
            'ecommerce_purchase': ActionSequenceFixtures.get_ecommerce_purchase_workflow(),
            'complex_dashboard': ActionSequenceFixtures.get_complex_dashboard_workflow(),
            'invalid_actions': ErrorScenarioFixtures.get_invalid_action_sequence()
        })
        
        # Selector fixtures
        self.selector_fixtures.update({
            'high_confidence': SelectorFixtures.get_high_confidence_selectors(),
            'medium_confidence': SelectorFixtures.get_medium_confidence_selectors(),
            'low_confidence': SelectorFixtures.get_low_confidence_selectors()
        })
    
    def get_html_fixture(self, name):
        """Get HTML fixture by name"""
        return self.html_fixtures.get(name)
    
    def get_action_fixture(self, name):
        """Get action sequence fixture by name"""
        return self.action_fixtures.get(name)
    
    def get_selector_fixtures(self, name):
        """Get selector fixtures by name"""
        return self.selector_fixtures.get(name, [])
    
    def list_available_fixtures(self):
        """List all available fixtures"""
        return {
            'html_fixtures': list(self.html_fixtures.keys()),
            'action_fixtures': list(self.action_fixtures.keys()),
            'selector_fixtures': list(self.selector_fixtures.keys())
        }

# Global fixture registry instance
fixture_registry = FixtureRegistry()

if __name__ == "__main__":
    # Demo of fixture capabilities
    print("🧪 GUI Tabs Test Fixtures Demo")
    print("=" * 40)
    
    # Show available fixtures
    fixtures = fixture_registry.list_available_fixtures()
    print("Available fixtures:")
    for category, names in fixtures.items():
        print(f"  {category}: {', '.join(names)}")
    
    # Demo HTML fixture
    print(f"\nHTML Fixture Demo:")
    simple_login = fixture_registry.get_html_fixture('simple_login')
    print(f"  Name: {simple_login.name}")
    print(f"  Complexity: {simple_login.complexity}")
    print(f"  Expected elements: {simple_login.expected_elements}")
    print(f"  HTML length: {len(simple_login.content)} chars")
    
    # Demo action fixture
    print(f"\nAction Fixture Demo:")
    login_workflow = fixture_registry.get_action_fixture('simple_login')
    print(f"  Name: {login_workflow.name}")
    print(f"  Workflow type: {login_workflow.workflow_type}")
    print(f"  Actions count: {len(login_workflow.actions)}")
    print(f"  Expected duration: {login_workflow.expected_duration}s")
    
    # Demo performance fixture
    print(f"\nPerformance Fixture Demo:")
    perf_html = PerformanceTestFixtures.generate_large_html_content(50)
    print(f"  Generated HTML with {perf_html.expected_elements} elements")
    
    perf_actions = PerformanceTestFixtures.generate_large_action_sequence(25)
    print(f"  Generated {len(perf_actions.actions)} actions")
    
    print("\n✅ Fixtures ready for testing!")