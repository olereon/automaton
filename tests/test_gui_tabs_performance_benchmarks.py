#!/usr/bin/env python3
"""
Performance Benchmarks for New GUI Tabs
Comprehensive performance testing for Action Tab and Selector Tab functionality.

PERFORMANCE TARGETS:
- Tab switching: < 50ms
- Large action sequence loading: < 1s for 100 actions
- HTML analysis: < 500ms for 50KB HTML
- Selector generation: < 200ms for typical page
- Cross-tab operations: < 100ms per operation
- Memory usage: < 50MB for typical workflow

This module provides detailed performance profiling and benchmarking.
"""

import sys
import os
import time
import asyncio
import memory_profiler
import statistics
from pathlib import Path
from unittest.mock import Mock

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.engine import ActionType, Action

class PerformanceBenchmark:
    """Performance benchmarking utilities"""
    
    def __init__(self):
        self.results = {}
        
    def time_function(self, func_name, func, *args, **kwargs):
        """Time a function execution"""
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        self.results[func_name] = execution_time
        
        return result, execution_time
    
    async def time_async_function(self, func_name, func, *args, **kwargs):
        """Time an async function execution"""
        start_time = time.perf_counter()
        result = await func(*args, **kwargs)
        end_time = time.perf_counter()
        
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        self.results[func_name] = execution_time
        
        return result, execution_time
    
    def benchmark_repeated(self, func_name, func, iterations=10, *args, **kwargs):
        """Benchmark a function with multiple iterations"""
        times = []
        
        for _ in range(iterations):
            start_time = time.perf_counter()
            func(*args, **kwargs)
            end_time = time.perf_counter()
            times.append((end_time - start_time) * 1000)
        
        stats = {
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0
        }
        
        self.results[func_name] = stats
        return stats

class ActionTabPerformanceTest:
    """Performance tests for Action Tab"""
    
    def __init__(self):
        from tests.test_new_gui_tabs_comprehensive import MockActionTab
        self.action_tab = MockActionTab()
        self.benchmark = PerformanceBenchmark()
    
    def create_test_actions(self, count):
        """Create test actions for performance testing"""
        actions = []
        for i in range(count):
            action_type = [ActionType.INPUT_TEXT, ActionType.CLICK_BUTTON, 
                          ActionType.CHECK_ELEMENT, ActionType.WAIT][i % 4]
            
            action = Action(
                action_type,
                description=f"Performance test action {i+1}",
                selector=f".test-element-{i}",
                value=f"test-value-{i}" if action_type == ActionType.INPUT_TEXT else None,
                timeout=1000 + (i * 100)
            )
            actions.append(action)
        return actions
    
    def test_action_sequence_loading_performance(self):
        """Test performance of loading different sized action sequences"""
        print("📊 Testing Action Sequence Loading Performance...")
        
        sequence_sizes = [10, 50, 100, 250, 500]
        results = {}
        
        for size in sequence_sizes:
            test_actions = self.create_test_actions(size)
            
            # Benchmark loading
            _, load_time = self.benchmark.time_function(
                f"load_sequence_{size}", 
                self.action_tab.load_action_sequence,
                test_actions
            )
            
            results[size] = load_time
            print(f"  📋 {size} actions: {load_time:.2f}ms")
            
            # Performance targets
            if size <= 100 and load_time > 1000:
                print(f"  ⚠️ WARNING: Loading {size} actions took {load_time:.2f}ms (target: <1000ms)")
            elif size > 100 and load_time > (size * 10):  # 10ms per action max
                print(f"  ⚠️ WARNING: Loading {size} actions took {load_time:.2f}ms (target: <{size * 10}ms)")
        
        return results
    
    def test_action_selection_performance(self):
        """Test performance of action selection and parameter population"""
        print("\n📊 Testing Action Selection Performance...")
        
        # Create large action sequence
        test_actions = self.create_test_actions(100)
        self.action_tab.load_action_sequence(test_actions)
        
        # Test selection performance at different indices
        selection_times = []
        test_indices = [0, 25, 50, 75, 99]
        
        for index in test_indices:
            _, select_time = self.benchmark.time_function(
                f"select_action_{index}",
                self.action_tab.select_action,
                index
            )
            selection_times.append(select_time)
            print(f"  🎯 Select action {index}: {select_time:.2f}ms")
        
        avg_selection_time = statistics.mean(selection_times)
        print(f"  📊 Average selection time: {avg_selection_time:.2f}ms")
        
        # Performance target: < 50ms per selection
        if avg_selection_time > 50:
            print(f"  ⚠️ WARNING: Average selection time {avg_selection_time:.2f}ms exceeds target (50ms)")
        
        return selection_times
    
    def test_parameter_operations_performance(self):
        """Test performance of parameter preview and apply operations"""
        print("\n📊 Testing Parameter Operations Performance...")
        
        test_actions = self.create_test_actions(10)
        self.action_tab.load_action_sequence(test_actions)
        self.action_tab.select_action(0)
        
        # Test parameter preview performance
        preview_stats = self.benchmark.benchmark_repeated(
            "parameter_preview",
            self.action_tab.preview_parameters,
            iterations=50
        )
        print(f"  👀 Parameter preview: {preview_stats['mean']:.2f}ms avg")
        
        # Test parameter apply performance
        apply_stats = self.benchmark.benchmark_repeated(
            "parameter_apply",
            self.action_tab.apply_parameter_changes,
            iterations=50
        )
        print(f"  ✅ Parameter apply: {apply_stats['mean']:.2f}ms avg")
        
        # Performance targets: < 10ms for these operations
        if preview_stats['mean'] > 10:
            print(f"  ⚠️ WARNING: Parameter preview too slow: {preview_stats['mean']:.2f}ms")
        if apply_stats['mean'] > 10:
            print(f"  ⚠️ WARNING: Parameter apply too slow: {apply_stats['mean']:.2f}ms")
        
        return {'preview': preview_stats, 'apply': apply_stats}
    
    async def test_execution_performance(self):
        """Test performance of action sequence execution"""
        print("\n📊 Testing Action Execution Performance...")
        
        sequence_sizes = [5, 10, 25, 50]
        execution_results = {}
        
        for size in sequence_sizes:
            test_actions = self.create_test_actions(size)
            self.action_tab.load_action_sequence(test_actions)
            
            _, exec_time = await self.benchmark.time_async_function(
                f"execution_{size}",
                self.action_tab.execute_action_sequence
            )
            
            execution_results[size] = exec_time
            time_per_action = exec_time / size
            print(f"  ⚡ {size} actions: {exec_time:.2f}ms total, {time_per_action:.2f}ms per action")
        
        return execution_results

class SelectorTabPerformanceTest:
    """Performance tests for Selector Tab"""
    
    def __init__(self):
        from tests.test_new_gui_tabs_comprehensive import MockSelectorTab
        self.selector_tab = MockSelectorTab()
        self.benchmark = PerformanceBenchmark()
    
    def create_test_html(self, complexity_level):
        """Create test HTML of different complexity levels"""
        if complexity_level == "simple":
            return """
            <html><body>
                <div id="main">
                    <button class="btn">Click me</button>
                    <input type="text" name="username">
                </div>
            </body></html>
            """
        
        elif complexity_level == "medium":
            elements = []
            for i in range(25):
                elements.append(f"""
                <div class="item-{i}" data-id="{i}">
                    <span class="label">Item {i}</span>
                    <button class="btn btn-{i % 3}" id="btn-{i}">Action</button>
                </div>
                """)
            
            return f"<html><body>{''.join(elements)}</body></html>"
        
        elif complexity_level == "complex":
            # Generate deeply nested, complex HTML
            elements = []
            for i in range(100):
                elements.append(f"""
                <div class="container-{i % 5}">
                    <header class="item-header">
                        <h3 class="title-{i % 3}">Title {i}</h3>
                    </header>
                    <main class="item-content" data-index="{i}">
                        <div class="form-group">
                            <label for="input-{i}">Label {i}</label>
                            <input type="text" id="input-{i}" class="form-control input-{i % 4}">
                        </div>
                        <div class="actions">
                            <button type="button" class="btn btn-primary action-{i}" 
                                    data-action="submit" data-id="{i}">Submit</button>
                            <button type="button" class="btn btn-secondary cancel-{i}"
                                    data-action="cancel">Cancel</button>
                        </div>
                    </main>
                </div>
                """)
            
            return f"<html><body><div id='app'>{''.join(elements)}</div></body></html>"
        
        return "<html></html>"
    
    def test_html_loading_performance(self):
        """Test performance of HTML content loading"""
        print("\n📊 Testing HTML Loading Performance...")
        
        complexity_levels = ["simple", "medium", "complex"]
        loading_results = {}
        
        for level in complexity_levels:
            html_content = self.create_test_html(level)
            html_size = len(html_content)
            
            _, load_time = self.benchmark.time_function(
                f"html_load_{level}",
                self.selector_tab.load_html_content,
                html_content
            )
            
            loading_results[level] = {
                'time': load_time,
                'size': html_size,
                'size_kb': html_size / 1024
            }
            
            print(f"  📄 {level.capitalize()} HTML ({html_size/1024:.1f}KB): {load_time:.2f}ms")
            
            # Performance target: < 1ms per KB
            if load_time > (html_size / 1024):
                print(f"  ⚠️ WARNING: Loading too slow for {level} HTML")
        
        return loading_results
    
    def test_html_analysis_performance(self):
        """Test performance of HTML structure analysis"""
        print("\n📊 Testing HTML Analysis Performance...")
        
        complexity_levels = ["simple", "medium", "complex"]
        analysis_results = {}
        
        for level in complexity_levels:
            html_content = self.create_test_html(level)
            self.selector_tab.load_html_content(html_content)
            
            # Benchmark analysis with multiple iterations
            analysis_stats = self.benchmark.benchmark_repeated(
                f"analysis_{level}",
                self.selector_tab.analyze_html_structure,
                iterations=10
            )
            
            analysis_results[level] = analysis_stats
            print(f"  🔍 {level.capitalize()} analysis: {analysis_stats['mean']:.2f}ms avg "
                  f"(min: {analysis_stats['min']:.2f}ms, max: {analysis_stats['max']:.2f}ms)")
            
            # Performance targets
            target_time = {'simple': 50, 'medium': 200, 'complex': 500}[level]
            if analysis_stats['mean'] > target_time:
                print(f"  ⚠️ WARNING: Analysis too slow for {level} HTML (target: {target_time}ms)")
        
        return analysis_results
    
    def test_selector_generation_performance(self):
        """Test performance of selector recommendation generation"""
        print("\n📊 Testing Selector Generation Performance...")
        
        # Load complex HTML for comprehensive testing
        html_content = self.create_test_html("complex")
        self.selector_tab.load_html_content(html_content)
        self.selector_tab.analyze_html_structure()
        
        # Test different generation scenarios
        scenarios = [
            ("basic", {}),
            ("high_confidence", {'min_confidence': 90}),
            ("medium_confidence", {'min_confidence': 75})
        ]
        
        generation_results = {}
        
        for scenario_name, criteria in scenarios:
            generation_stats = self.benchmark.benchmark_repeated(
                f"generation_{scenario_name}",
                self.selector_tab.generate_selector_recommendations,
                iterations=10,
                criteria
            )
            
            generation_results[scenario_name] = generation_stats
            print(f"  🎯 {scenario_name}: {generation_stats['mean']:.2f}ms avg "
                  f"(std: {generation_stats['std_dev']:.2f}ms)")
            
            # Performance target: < 200ms for generation
            if generation_stats['mean'] > 200:
                print(f"  ⚠️ WARNING: Generation too slow for {scenario_name} scenario")
        
        return generation_results
    
    def test_selector_validation_performance(self):
        """Test performance of selector validation"""
        print("\n📊 Testing Selector Validation Performance...")
        
        # Setup with recommendations
        html_content = self.create_test_html("medium")
        self.selector_tab.load_html_content(html_content)
        self.selector_tab.generate_selector_recommendations()
        
        if self.selector_tab.recommended_selectors:
            test_selector = self.selector_tab.recommended_selectors[0]['selector']
            test_strategy = self.selector_tab.recommended_selectors[0]['strategy']
            
            # Benchmark validation
            validation_stats = self.benchmark.benchmark_repeated(
                "validation",
                self.selector_tab.validate_selector_strategy,
                iterations=20,
                test_selector, test_strategy
            )
            
            print(f"  ✅ Validation: {validation_stats['mean']:.2f}ms avg "
                  f"(min: {validation_stats['min']:.2f}ms, max: {validation_stats['max']:.2f}ms)")
            
            # Performance target: < 100ms per validation
            if validation_stats['mean'] > 100:
                print(f"  ⚠️ WARNING: Validation too slow: {validation_stats['mean']:.2f}ms")
            
            return validation_stats
        
        print("  ⚠️ No selectors available for validation testing")
        return None

class TabIntegrationPerformanceTest:
    """Performance tests for tab integration"""
    
    def __init__(self):
        from tests.test_new_gui_tabs_comprehensive import MockActionTab, MockSelectorTab
        self.action_tab = MockActionTab()
        self.selector_tab = MockSelectorTab()
        self.benchmark = PerformanceBenchmark()
    
    def test_cross_tab_data_transfer_performance(self):
        """Test performance of data transfer between tabs"""
        print("\n📊 Testing Cross-Tab Data Transfer Performance...")
        
        # Setup both tabs with data
        test_actions = [
            Action(ActionType.CLICK_BUTTON, "Test action", "")
        ]
        html_content = """
        <div class="container">
            <button id="test-btn" class="btn-primary">Test Button</button>
            <input type="text" name="username" class="form-control">
        </div>
        """
        
        # Load data
        self.action_tab.load_action_sequence(test_actions)
        self.selector_tab.load_html_content(html_content)
        self.selector_tab.generate_selector_recommendations()
        
        # Test selector transfer from Selector tab to Action tab
        def transfer_selector():
            self.action_tab.select_action(0)
            recommended_selector = self.selector_tab.recommended_selectors[0]['selector']
            self.action_tab.parameter_fields['selector'].set(recommended_selector)
            self.action_tab.apply_parameter_changes()
        
        transfer_stats = self.benchmark.benchmark_repeated(
            "cross_tab_transfer",
            transfer_selector,
            iterations=25
        )
        
        print(f"  🔄 Cross-tab transfer: {transfer_stats['mean']:.2f}ms avg "
              f"(std: {transfer_stats['std_dev']:.2f}ms)")
        
        # Performance target: < 50ms per transfer
        if transfer_stats['mean'] > 50:
            print(f"  ⚠️ WARNING: Cross-tab transfer too slow: {transfer_stats['mean']:.2f}ms")
        
        return transfer_stats
    
    def test_tab_switching_simulation_performance(self):
        """Test performance of simulated tab switching"""
        print("\n📊 Testing Tab Switching Simulation Performance...")
        
        # Setup both tabs with realistic data
        large_actions = []
        for i in range(50):
            large_actions.append(Action(ActionType.CLICK_BUTTON, f"Action {i}", f".btn-{i}"))
        
        complex_html = self.create_complex_html_for_switching()
        
        # Load data in both tabs
        self.action_tab.load_action_sequence(large_actions)
        self.selector_tab.load_html_content(complex_html)
        self.selector_tab.generate_selector_recommendations()
        
        # Simulate tab switching operations
        def simulate_tab_switch():
            # Switch to Action tab (simulate UI updates)
            self.action_tab.select_action(0)
            preview = self.action_tab.preview_parameters()
            
            # Switch to Selector tab (simulate UI updates)
            analysis = self.selector_tab.get_selector_pattern_analysis()
            
            return len(preview) + len(analysis)
        
        switch_stats = self.benchmark.benchmark_repeated(
            "tab_switching",
            simulate_tab_switch,
            iterations=30
        )
        
        print(f"  🔄 Tab switching: {switch_stats['mean']:.2f}ms avg "
              f"(min: {switch_stats['min']:.2f}ms, max: {switch_stats['max']:.2f}ms)")
        
        # Performance target: < 50ms per switch
        if switch_stats['mean'] > 50:
            print(f"  ⚠️ WARNING: Tab switching too slow: {switch_stats['mean']:.2f}ms")
        
        return switch_stats
    
    def create_complex_html_for_switching(self):
        """Create complex HTML for tab switching tests"""
        elements = []
        for i in range(30):
            elements.append(f"""
            <div class="component-{i}">
                <header>Component {i}</header>
                <div class="controls">
                    <button class="action-{i}" data-id="{i}">Action {i}</button>
                    <input type="text" class="input-{i}" value="Value {i}">
                </div>
            </div>
            """)
        
        return f"<html><body>{''.join(elements)}</body></html>"

class MemoryProfiler:
    """Memory profiling for GUI tabs"""
    
    @staticmethod
    @memory_profiler.profile
    def profile_action_tab_memory():
        """Profile memory usage of Action Tab operations"""
        from tests.test_new_gui_tabs_comprehensive import MockActionTab
        
        action_tab = MockActionTab()
        
        # Create large dataset
        actions = []
        for i in range(200):
            action = Action(ActionType.INPUT_TEXT, f"Action {i}", f".selector-{i}", f"value-{i}")
            actions.append(action)
        
        # Load and manipulate data
        action_tab.load_action_sequence(actions)
        
        for i in range(0, 200, 10):
            action_tab.select_action(i)
            preview = action_tab.preview_parameters()
            action_tab.apply_parameter_changes()
        
        return action_tab
    
    @staticmethod 
    @memory_profiler.profile
    def profile_selector_tab_memory():
        """Profile memory usage of Selector Tab operations"""
        from tests.test_new_gui_tabs_comprehensive import MockSelectorTab
        
        selector_tab = MockSelectorTab()
        
        # Create large HTML content
        html_parts = []
        for i in range(500):
            html_parts.append(f"""
            <div class="item-{i}" data-index="{i}">
                <span class="label-{i % 10}">Item {i}</span>
                <button class="btn-{i % 5}" id="button-{i}">Button {i}</button>
            </div>
            """)
        
        large_html = f"<html><body>{''.join(html_parts)}</body></html>"
        
        # Load and process data
        selector_tab.load_html_content(large_html)
        selector_tab.analyze_html_structure()
        selector_tab.generate_selector_recommendations()
        
        for selector_info in selector_tab.recommended_selectors:
            selector_tab.validate_selector_strategy(
                selector_info['selector'], 
                selector_info['strategy']
            )
        
        return selector_tab

async def run_performance_benchmarks():
    """Run all performance benchmarks"""
    print("🚀 Starting GUI Tabs Performance Benchmarks")
    print("=" * 60)
    
    # Action Tab Performance
    print("\n📋 ACTION TAB PERFORMANCE")
    print("=" * 30)
    action_perf = ActionTabPerformanceTest()
    
    action_perf.test_action_sequence_loading_performance()
    action_perf.test_action_selection_performance()  
    action_perf.test_parameter_operations_performance()
    await action_perf.test_execution_performance()
    
    # Selector Tab Performance
    print("\n🎯 SELECTOR TAB PERFORMANCE")
    print("=" * 30)
    selector_perf = SelectorTabPerformanceTest()
    
    selector_perf.test_html_loading_performance()
    selector_perf.test_html_analysis_performance()
    selector_perf.test_selector_generation_performance()
    selector_perf.test_selector_validation_performance()
    
    # Integration Performance
    print("\n🔄 INTEGRATION PERFORMANCE")
    print("=" * 30)
    integration_perf = TabIntegrationPerformanceTest()
    
    integration_perf.test_cross_tab_data_transfer_performance()
    integration_perf.test_tab_switching_simulation_performance()
    
    # Memory profiling (commented out by default as it's verbose)
    # print("\n💾 MEMORY PROFILING")
    # print("=" * 30)
    # print("Action Tab Memory Profile:")
    # MemoryProfiler.profile_action_tab_memory()
    # print("\nSelector Tab Memory Profile:")
    # MemoryProfiler.profile_selector_tab_memory()
    
    print("\n" + "=" * 60)
    print("🏁 Performance Benchmarks Complete!")
    print("=" * 60)
    
    # Summary recommendations
    print("\n📊 PERFORMANCE SUMMARY & RECOMMENDATIONS:")
    print("✅ Action Tab: Optimize for <1s loading of 100+ actions")
    print("✅ Selector Tab: Target <500ms analysis for complex HTML")
    print("✅ Tab Integration: Keep cross-tab operations under 50ms")
    print("✅ Memory Usage: Monitor for memory leaks with large datasets")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(run_performance_benchmarks())
    sys.exit(0 if success else 1)