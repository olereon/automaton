# Modern Components Guide

## Introduction

This guide provides comprehensive documentation for Automaton's modern UI components. These components are built on top of our design system to provide a consistent, accessible, and visually appealing user interface.

## Component Overview

The modern components are located in `src.interfaces.modern_components` and provide drop-in replacements for standard Tkinter components with enhanced styling and functionality.

## Available Components

### ModernButton

A modern button component with hover effects, multiple variants, and design system integration.

#### Features

- Hover/focus states with smooth transitions
- Multiple variants (primary, secondary, outline, ghost, danger)
- Size variants (small, medium, large, extra_large)
- Accessibility support with proper focus indicators
- Loading state support

#### Usage

```python
from src.interfaces.modern_components import ModernButton
from src.interfaces.design_system import ComponentSize, ThemeMode

# Create a primary button
button = ModernButton(
    parent=root,
    text="Click Me",
    variant='primary',
    size=ComponentSize.MEDIUM,
    theme_mode=ThemeMode.DARK,
    command=lambda: print("Button clicked!")
)
```

#### Button Variants

| Variant | Description | Use Case |
|---------|-------------|----------|
| primary | Main brand color, high emphasis | Primary actions, form submissions |
| secondary | Neutral color, medium emphasis | Secondary actions |
| outline | Transparent with border, medium emphasis | Alternative actions |
| ghost | Transparent, low emphasis | Destructive actions, tertiary actions |
| danger | Red color, high emphasis | Destructive actions |

#### Button Sizes

| Size | Description | Use Case |
|------|-------------|----------|
| SMALL | Compact button | Toolbars, dense interfaces |
| MEDIUM | Standard button | Forms, dialogs |
| LARGE | Larger button | Primary actions, touch interfaces |
| EXTRA_LARGE | Largest button | Hero sections, call-to-action |

#### Loading State

```python
# Set loading state
button.set_loading(True)

# Remove loading state
button.set_loading(False)
```

### ModernEntry

A modern input field with focus states, validation styling, and accessibility features.

#### Features

- Focus ring indicators
- Error/success state styling
- Placeholder text support
- Input validation with visual feedback
- Clear button option

#### Usage

```python
from src.interfaces.modern_components import ModernEntry
from src.interfaces.design_system import ComponentState

# Create a standard input field
entry = ModernEntry(
    parent=root,
    placeholder="Enter your text...",
    size=ComponentSize.MEDIUM,
    theme_mode=ThemeMode.DARK
)

# Set validation state
entry.set_validation_state(ComponentState.ERROR)
```

#### Validation States

| State | Description | Visual Indicator |
|-------|-------------|------------------|
| DEFAULT | Normal state | Standard border |
| FOCUS | Field has focus | Blue border |
| ERROR | Validation failed | Red border |
| SUCCESS | Validation passed | Green border |
| DISABLED | Field is disabled | Grayed out appearance |

#### Placeholder Text

```python
# Create an entry with placeholder
entry = ModernEntry(
    parent=root,
    placeholder="Username...",
    theme_mode=ThemeMode.DARK
)

# Get the actual value (handles placeholder)
value = entry.get_value()
```

### ModernFrame

A modern container/panel component with elevation effects, semantic variants, and proper spacing.

#### Features

- Multiple surface variants (primary, secondary, tertiary, elevated)
- Elevation effects with visual depth
- Consistent padding and margin system
- Responsive design considerations

#### Usage

```python
from src.interfaces.modern_components import ModernFrame

# Create a primary panel
panel = ModernFrame(
    parent=root,
    variant='primary',
    elevation='base',
    padding=16,
    theme_mode=ThemeMode.DARK
)
```

#### Frame Variants

| Variant | Description | Use Case |
|---------|-------------|----------|
| primary | Main background color | Main content areas |
| secondary | Secondary background color | Secondary panels |
| tertiary | Tertiary background color | Card backgrounds |
| elevated | Elevated with shadow | Modal dialogs, popovers |

#### Elevation Levels

| Level | Description | Shadow Intensity |
|-------|-------------|-----------------|
| none | No shadow | Flat appearance |
| sm | Subtle shadow | Slightly elevated |
| base | Medium shadow | Standard elevation |
| md | Strong shadow | Highly elevated |
| lg | Very strong shadow | Floating elements |

#### Padding Options

```python
# Uniform padding
panel = ModernFrame(
    parent=root,
    padding=16,
    theme_mode=ThemeMode.DARK
)

# Different horizontal and vertical padding
panel = ModernFrame(
    parent=root,
    padding={'x': 24, 'y': 16},
    theme_mode=ThemeMode.DARK
)
```

### ModernLabel

A modern label component with typography variants, semantic text styling, and accessibility features.

#### Features

- Typography scale support (hero, heading1-3, body, caption)
- Semantic text colors (primary, secondary, tertiary, disabled)
- Font weight variations
- Proper line height and spacing

#### Usage

```python
from src.interfaces.modern_components import ModernLabel

# Create a heading label
label = ModernLabel(
    parent=root,
    text="Welcome to Automaton",
    variant='heading2',
    weight='bold',
    theme_mode=ThemeMode.DARK
)
```

#### Typography Variants

| Variant | Size | Weight | Use Case |
|---------|------|--------|----------|
| hero | 35px | bold | Page titles, hero text |
| heading1 | 28px | bold | Main headings |
| heading2 | 23px | bold | Section headings |
| heading3 | 19px | bold | Subsection headings |
| body | 15px | normal | Body text |
| body-large | 17px | normal | Large body text |
| caption | 13px | normal | Captions, small text |
| small | 11px | normal | Fine print |

#### Text Colors

| Color | Description | Use Case |
|-------|-------------|----------|
| primary | Main text color | Headings, important text |
| secondary | Secondary text color | Subheadings, less important text |
| tertiary | Tertiary text color | Captions, metadata |
| disabled | Disabled text color | Disabled elements |

### ModernNotebook

A modern tabbed interface with design system integration.

#### Features

- Modern tab styling with hover effects
- Consistent spacing and typography
- Active/inactive state management
- Keyboard navigation support

#### Usage

```python
from src.interfaces.modern_components import ModernNotebook

# Create a tabbed interface
notebook = ModernNotebook(
    parent=root,
    theme_mode=ThemeMode.DARK
)

# Add tabs
tab1 = ttk.Frame(notebook)
tab2 = ttk.Frame(notebook)

notebook.add(tab1, text="Tab 1")
notebook.add(tab2, text="Tab 2")
```

### ModernProgressBar

A modern progress bar component with smooth animations and semantic color coding.

#### Features

- Smooth progress transitions
- Multiple variants (primary, success, warning, error)
- Percentage display option
- Animated loading states

#### Usage

```python
from src.interfaces.modern_components import ModernProgressBar

# Create a progress bar
progress = ModernProgressBar(
    parent=root,
    variant='primary',
    show_percentage=True,
    height=8,
    theme_mode=ThemeMode.DARK
)

# Set progress value
progress.set_progress(75)
```

#### Progress Variants

| Variant | Color | Use Case |
|---------|-------|----------|
| primary | Brand color | Standard progress |
| success | Green | Successful completion |
| warning | Yellow | Warning state |
| error | Red | Error state |

### ModernScrollableFrame

A modern scrollable container with custom scrollbars and smooth scrolling behavior.

#### Features

- Custom styled scrollbars
- Smooth scrolling with mouse wheel
- Dynamic content sizing
- Keyboard navigation support

#### Usage

```python
from src.interfaces.modern_components import ModernScrollableFrame

# Create a scrollable frame
scrollable = ModernScrollableFrame(
    parent=root,
    theme_mode=ThemeMode.DARK
)

# Get the inner frame for adding content
inner_frame = scrollable.get_inner_frame()

# Add content to inner_frame
label = ModernLabel(
    parent=inner_frame,
    text="Scrollable Content",
    theme_mode=ThemeMode.DARK
)
```

## Component Showcase

The `ComponentShowcase` class provides an interactive demonstration of all modern components:

```python
from src.interfaces.modern_components import ComponentShowcase

# Create a showcase window
showcase = ComponentShowcase(
    parent=root,
    theme_mode=ThemeMode.DARK
)
```

## Best Practices

1. **Use semantic variants**: Choose component variants based on their semantic meaning, not just appearance
2. **Maintain consistency**: Use the same theme mode throughout your application
3. **Provide proper spacing**: Use the padding and margin system rather than arbitrary values
4. **Support accessibility**: Ensure all interactive elements have proper focus indicators
5. **Handle loading states**: Use loading states for actions that take time to complete

## Integration with Existing Code

To modernize existing Tkinter code:

1. Replace standard Tkinter components with their modern counterparts
2. Apply a consistent theme to the entire application
3. Use the design system for any custom styling

```python
import tkinter as tk
from src.interfaces.modern_components import ModernButton, ModernFrame
from src.interfaces.design_system import ModernTkinterTheme, ThemeMode

# Create root window
root = tk.Tk()
root.title("Modern UI Example")

# Apply theme
theme = ModernTkinterTheme(ThemeMode.DARK)
theme.apply_to_root(root)

# Create a modern frame
main_frame = ModernFrame(
    parent=root,
    variant='primary',
    padding=24,
    theme_mode=ThemeMode.DARK
)
main_frame.pack(fill=tk.BOTH, expand=True)

# Add a modern button
button = ModernButton(
    parent=main_frame,
    text="Click Me",
    variant='primary',
    theme_mode=ThemeMode.DARK,
    command=lambda: print("Modern button clicked!")
)
button.pack(pady=16)

root.mainloop()
```

## Related Documentation

- [Design System Guide](20_design_system_guide.md) - Design tokens and principles
- [Component Reference](6_components_reference.md) - Detailed component API
- [User Guide](4_user_guide.md) - Using the GUI interface