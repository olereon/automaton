# Design System Guide

## Introduction

This guide explains Automaton's design system, which provides a consistent, modern visual language for all user interfaces. The design system ensures that all components share a unified look and feel while maintaining accessibility and usability standards.

## Design Philosophy

Our design system is built on the following principles:

- **Consistency**: Uniform visual language across all components
- **Accessibility**: WCAG-compliant color contrasts and keyboard navigation
- **Modularity**: Reusable components that can be combined in various ways
- **Scalability**: Design that works across different screen sizes and contexts

## Design Tokens

Design tokens are the visual design atoms of our design system. They represent small, repeatable design decisions such as colors, fonts, spacing, and more.

### Color System

Our color system is organized into semantic categories:

| Category | Light Theme | Dark Theme | Usage |
|----------|-------------|------------|-------|
| Primary | #0066CC | #3399FF | Main brand color, primary actions |
| Secondary | #6B46C1 | #8B5CF6 | Secondary actions, highlights |
| Surface Primary | #FFFFFF | #1E1E1E | Main backgrounds |
| Surface Secondary | #F8F9FA | #252526 | Panel backgrounds |
| Text Primary | #1F2937 | #F3F4F6 | Primary text content |
| Text Secondary | #6B7280 | #D1D5DB | Secondary text, captions |

### Typography

We use a consistent typography scale to create visual hierarchy:

| Scale | Size (px) | Line Height (px) | Weight | Use Case |
|-------|-----------|-----------------|--------|----------|
| xs | 11 | 16 | Normal | Small text, captions |
| sm | 13 | 20 | Normal | Body small |
| base | 15 | 24 | Normal | Body text |
| lg | 17 | 28 | Normal | Large text |
| xl | 19 | 32 | Normal | Headings |
| 2xl | 23 | 32 | Bold | Large headings |
| 3xl | 28 | 36 | Bold | Display text |
| 4xl | 35 | 40 | Bold | Hero text |

### Spacing System

Our spacing is based on a 4px grid system:

| Token | Value (px) | Use Case |
|-------|------------|----------|
| xs | 4 | Tight spaces between elements |
| sm | 8 | Small padding, margins |
| base | 12 | Default padding for components |
| md | 16 | Standard spacing between sections |
| lg | 24 | Large padding, margins |
| xl | 32 | Extra-large spacing |
| 2xl | 48 | Section separators |
| 3xl | 64 | Large gaps |
| 4xl | 96 | Page-level spacing |

## Component Library

Our component library provides pre-built, styled components that implement the design system.

### Button Variants

Buttons come in several variants for different use cases:

| Variant | Description | Use Case |
|---------|-------------|----------|
| Primary | Main brand color, high emphasis | Primary actions, form submissions |
| Secondary | Neutral color, medium emphasis | Secondary actions |
| Outline | Transparent with border, medium emphasis | Alternative actions |
| Ghost | Transparent, low emphasis | Destructive actions, tertiary actions |
| Danger | Red color, high emphasis | Destructive actions |

### Input Fields

Input fields follow a consistent design with proper focus states and validation indicators:

- **Default**: Standard appearance
- **Focus**: Blue border indicator
- **Error**: Red border indicator
- **Success**: Green border indicator
- **Disabled**: Grayed out appearance

### Panels and Containers

Panels and containers use elevation to create visual hierarchy:

| Elevation | Description | Use Case |
|-----------|-------------|----------|
| None | Flat appearance, no shadow | Inline content |
| sm | Subtle shadow | Elevated cards |
| base | Medium shadow | Modal dialogs |
| md | Strong shadow | Floating panels |
| lg | Very strong shadow | Popovers, tooltips |

## Using the Design System

### In Code

The design system is implemented in the `src.interfaces.design_system` module:

```python
from src.interfaces.design_system import DesignTokens, ComponentLibrary, ThemeMode

# Create a component library with dark theme
component_lib = ComponentLibrary(ThemeMode.DARK)

# Get button styling
button_style = component_lib.get_button_style(
    variant='primary',
    size=ComponentSize.MEDIUM
)
```

### In UI Components

Modern components automatically use the design system:

```python
from src.interfaces.modern_components import ModernButton, ModernEntry

# Create a styled button
button = ModernButton(
    parent=root,
    text="Click Me",
    variant='primary',
    size=ComponentSize.MEDIUM
)

# Create a styled input field
entry = ModernEntry(
    parent=root,
    placeholder="Enter text...",
    size=ComponentSize.MEDIUM
)
```

## Theme Support

The design system supports light and dark themes:

```python
from src.interfaces.design_system import ThemeMode, ModernTkinterTheme

# Apply dark theme to the entire application
theme = ModernTkinterTheme(ThemeMode.DARK)
theme.apply_to_root(root)
```

## Accessibility

Our design system follows WCAG 2.1 AA guidelines:

- Color contrasts of at least 4.5:1 for normal text
- Keyboard navigation support for all interactive elements
- Focus indicators with sufficient contrast
- Semantic HTML structure where applicable

## Customization

While the design system provides consistent defaults, it can be customized:

```python
# Override specific tokens
custom_tokens = DesignTokens()
custom_tokens.BRAND_PRIMARY = {
    ThemeMode.LIGHT: "#FF6600",
    ThemeMode.DARK: "#FF9933"
}

# Create a component library with custom tokens
custom_lib = ComponentLibrary(theme_mode=ThemeMode.DARK)
custom_lib.tokens = custom_tokens
```

## Best Practices

1. **Use semantic variants**: Choose button and input variants based on their semantic meaning, not just appearance
2. **Maintain contrast**: Ensure text and background colors meet accessibility standards
3. **Respect spacing**: Use the spacing system tokens rather than arbitrary values
4. **Test in both themes**: Verify that customizations work in both light and dark modes
5. **Follow the hierarchy**: Use typography and elevation to create clear visual hierarchy

## Related Documentation

- [Component Reference](6_components_reference.md) - Detailed documentation of all UI components
- [Modern Components Guide](22_modern_components_guide.md) - Using the modern component library
- [Accessibility Guide](docs/24_accessibility_guide.md) - Accessibility best practices