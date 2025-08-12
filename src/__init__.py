"""
Automaton - AI-Powered Web Automation Platform

A lightweight, cross-platform web automation tool with both GUI and CLI interfaces.
"""

__version__ = "1.0.0"
__author__ = "Automaton Team"
__description__ = "AI-Powered Web Automation Platform"

from core.engine import (
    WebAutomationEngine,
    AutomationSequenceBuilder,
    AutomationConfig,
    ActionType,
    Action
)

__all__ = [
    "WebAutomationEngine",
    "AutomationSequenceBuilder", 
    "AutomationConfig",
    "ActionType",
    "Action"
]