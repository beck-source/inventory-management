#!/usr/bin/env python3
"""
Vue Component Structure Analyzer & Optimizer
Analyzes Vue 3 SFC components for performance issues, code duplication, and optimization opportunities.
"""

import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Tuple, Optional
from collections import defaultdict

# ============================================================================
# Data Structures
# ============================================================================

@dataclass
class Issue:
    """Represents a single optimization issue"""
    severity: str  # 'error', 'warning', 'info'
    category: str
    file: str
    line: int
    message: str
    suggestion: str
    code: str = ""

@dataclass
class ComponentMetrics:
    """Metrics for a component"""
    file: str
    lines: int
    methods_count: int
    computed_count: int
    hooks_count: int
    imports_count: int
    has_watch: bool
    has_on_mounted: bool
    data_refs: int
    unique_issues: int


# ============================================================================
# Vue SFC Parser
# ============================================================================

class VueSFCParser:
    """Parses Vue 3 Single File Components"""
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        with open(filepath, 'r', encoding='utf-8') as f:
            self.content = f.read()
        self.lines = self.content.split('\n')
        
    def extract_section(self, section_name: str) -> Tuple[str, int]:
        """Extract <template>, <script>, or <style> section with line number"""
        pattern = rf'<{section_name}[^>]*>(.*?)</{section_name}>'
        match = re.search(pattern, self.content, re.DOTALL)
        if match:
            line_num = self.content[:match.start()].count('\n')
            return match.group(1), line_num
        return "", 0
    
    def get_template(self) -> Tuple[str, int]:
        return self.extract_section('template')
    
    def get_script(self) -> Tuple[str, int]:
        return self.extract_section('script')
    
    def get_style(self) -> Tuple[str, int]:
        return self.extract_section('style')
    
    def find_all_matches(self, pattern: str, section: str) -> List[Tuple[str, int]]:
        """Find all regex matches in a section"""
        if section == 'template':
            content, offset = self.get_template()
        elif section == 'script':
            content, offset = self.get_script()
        else:
            return []
        
        matches = []
        for match in re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE):
            line = content[:match.start()].count('\n') + offset + 1
            matches.append((match.group(0), line))
        return matches


# ============================================================================
# Analysis Rules
# ============================================================================

class PerformanceAnalyzer:
    """Analyzes performance issues"""
    
    @staticmethod
    def check_v_for_keys(parser: VueSFCParser) -> List[Issue]:
        """Check for v-for without keys or with index as key"""
        issues = []
        template, offset = parser.get_template()
        
        # Pattern: v-for without :key
        for match in re.finditer(r'v-for="[^"]*"(?!\s*:key)', template):
            line = template[:match.start()].count('\n') + offset + 1
            issues.append(Issue(
                severity='warning',
                category='performance',
                file=parser.filepath,
                line=line,
                message='v-for directive missing :key binding',
                suggestion='Add unique :key binding to improve rendering performance (use stable identifiers like id, sku, not index)',
                code=match.group(0)
            ))
        
        # Pattern: :key="index" or :key="$index"
        for match in re.finditer(r':key="[\$]?index"', template):
            line = template[:match.start()].count('\n') + offset + 1
            issues.append(Issue(
                severity='error',
                category='performance',
                file=parser.filepath,
                line=line,
                message='Using array index as v-for key',
                suggestion='Replace with unique identifier (id, sku, uuid). Index keys break component state during reordering/filtering.',
                code=match.group(0)
            ))
        
        return issues
    
    @staticmethod
    def check_v_if_v_for_nesting(parser: VueSFCParser) -> List[Issue]:
        """Check for v-if on same element as v-for"""
        issues = []
        template, offset = parser.get_template()
        
        # Pattern: element with both v-for and v-if
        for match in re.finditer(r'<\w+[^>]*v-for="[^"]*"[^>]*v-if', template):
            line = template[:match.start()].count('\n') + offset + 1
            issues.append(Issue(
                severity='warning',
                category='performance',
                file=parser.filepath,
                line=line,
                message='v-if and v-for on same element',
                suggestion='Move v-if to a parent element or wrap v-for in template. This adds unnecessary filtering per render.',
                code=match.group(0)[:60]
            ))
        
        return issues
    
    @staticmethod
    def check_complex_expressions(parser: VueSFCParser) -> List[Issue]:
        """Check for overly complex template expressions"""
        issues = []
        template, offset = parser.get_template()
        
        # Pattern: complex expressions with multiple operators/function calls
        complex_patterns = [
            (r'\{\{[^}]{80,}\}\}', 'Expression exceeds 80 characters'),
            (r'\{\{[^}]*\?[^}]*\:[^}]*\?[^}]*\:[^}]*\}\}', 'Nested ternary operators'),
            (r'\{\{[^}]*\.[^}]*\.[^}]*\.[^}]*\.[^}]*\}\}', 'Deep property chain (5+ levels)'),
        ]
        
        for pattern, desc in complex_patterns:
            for match in re.finditer(pattern, template):
                line = template[:match.start()].count('\n') + offset + 1
                expr = match.group(0)[:70]
                issues.append(Issue(
                    severity='info',
                    category='performance',
                    file=parser.filepath,
                    line=line,
                    message=f'Complex template expression: {desc}',
                    suggestion='Extract to computed property or method for reusability and maintainability',
                    code=expr
                ))
        
        return issues
    
    @staticmethod
    def check_watchers_with_immediate(parser: VueSFCParser) -> List[Issue]:
        """Check for watch with immediate and onMounted doing similar work"""
        issues = []
        script, offset = parser.get_script()
        
        # Pattern: watch with immediate: true
        watch_matches = list(re.finditer(r'watch\([^,]+,\s*\([^)]*\)\s*=>\s*\{', script))
        mounted_matches = list(re.finditer(r'onMounted\([^)]*\)\s*', script))
        
        if watch_matches and mounted_matches:
            # Check if both exist - possible duplication
            for wmatch in watch_matches:
                if 'immediate' in script[wmatch.start():wmatch.start()+200]:
                    line = script[:wmatch.start()].count('\n') + offset + 1
                    issues.append(Issue(
                        severity='info',
                        category='performance',
                        file=parser.filepath,
                        line=line,
                        message='watch with immediate: true combined with onMounted',
                        suggestion='Consider using watchEffect or combining logic to avoid redundant initialization',
                        code='watch(..., { immediate: true })'
                    ))
        
        return issues


class CodeReuseAnalyzer:
    """Analyzes code duplication and reuse opportunities"""
    
    @staticmethod
    def check_duplicated_methods(parser: VueSFCParser) -> List[Issue]:
        """Check for duplicated helper methods like translateX, formatX"""
        issues = []
        script, offset = parser.get_script()
        
        # Extract all method definitions
        methods = re.findall(r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>', script)
        methods += re.findall(r'(\w+)\s*:\s*\([^)]*\)\s*=>', script)
        
        # Check for common patterns that should be in composables/utils
        duplication_patterns = {
            'translate': 'Consider extracting to useI18n() composable',
            'format': 'Consider extracting to utils or composable',
            'get': 'Utility method - consider moving to composable',
            'calculate': 'Business logic - consider moving to composable or utils',
        }
        
        for method in set(methods):
            for pattern, suggestion in duplication_patterns.items():
                if pattern in method.lower():
                    line = script[:script.find(method)].count('\n') + offset + 1
                    issues.append(Issue(
                        severity='info',
                        category='reuse',
                        file=parser.filepath,
                        line=line,
                        message=f'Utility method "{method}" might be duplicated across components',
                        suggestion=suggestion,
                        code=method
                    ))
                    break
        
        return issues
    
    @staticmethod
    def check_shared_state_patterns(parser: VueSFCParser) -> List[Issue]:
        """Check for patterns that should use composables instead of inline refs"""
        issues = []
        script, offset = parser.get_script()
        
        # Pattern: multiple refs managing related state
        refs = re.findall(r'const\s+(\w+)\s*=\s*ref\(', script)
        
        # Common groupings that suggest composable extraction
        if len(refs) >= 3:
            # Check for filter-related refs
            filter_refs = [r for r in refs if 'filter' in r.lower() or 'select' in r.lower()]
            if len(filter_refs) >= 2:
                line = script[:script.find('const')].count('\n') + offset + 1
                issues.append(Issue(
                    severity='info',
                    category='reuse',
                    file=parser.filepath,
                    line=line,
                    message=f'Multiple filter/selection refs ({len(filter_refs)}) suggest composable extraction',
                    suggestion='Create a composable (e.g., useFilters) to group related state and logic',
                    code=', '.join(filter_refs)
                ))
        
        return issues
    
    @staticmethod
    def check_duplicate_loading_pattern(parser: VueSFCParser) -> List[Issue]:
        """Check for loading/error state pattern that could be abstracted"""
        issues = []
        script, offset = parser.get_script()
        
        has_loading = 'loading' in script.lower()
        has_error = 'error' in script.lower()
        has_try_catch = 'try' in script and 'catch' in script
        
        if has_loading and has_error and has_try_catch:
            # This pattern appears in almost all views - worth extracting
            # But we only flag if it's a complex setup
            try_match = re.search(r'try\s*\{[^}]*finally', script, re.DOTALL)
            if try_match and len(try_match.group(0)) > 200:
                line = script[:script.find('try')].count('\n') + offset + 1
                issues.append(Issue(
                    severity='info',
                    category='reuse',
                    file=parser.filepath,
                    line=line,
                    message='Async loading pattern (loading, error, try/catch) is repeated',
                    suggestion='Create useAsync() or useFetch() composable to handle load/error/data states',
                    code='try/catch + loading + error'
                ))
        
        return issues


class StructureAnalyzer:
    """Analyzes component structure and organization"""
    
    @staticmethod
    def check_large_setup_function(parser: VueSFCParser) -> List[Issue]:
        """Check for overly large setup() functions"""
        issues = []
        script, offset = parser.get_script()
        
        setup_match = re.search(r'setup\s*\([^)]*\)\s*\{(.*)\n\s*\}(?=\n\s*\})?', script, re.DOTALL)
        if setup_match:
            setup_body = setup_match.group(1)
            lines = setup_body.count('\n')
            
            if lines > 150:
                line = script[:setup_match.start()].count('\n') + offset + 1
                issues.append(Issue(
                    severity='warning',
                    category='structure',
                    file=parser.filepath,
                    line=line,
                    message=f'Large setup function ({lines} lines)',
                    suggestion='Extract related logic into composables (useFilters, useData, useUI, etc.)',
                    code=f'{lines} lines'
                ))
        
        return issues
    
    @staticmethod
    def check_return_statement_size(parser: VueSFCParser) -> List[Issue]:
        """Check for large return objects exposing too much"""
        issues = []
        script, offset = parser.get_script()
        
        return_match = re.search(r'return\s*\{([^}]+)\}(?=\s*\})', script, re.DOTALL)
        if return_match:
            return_obj = return_match.group(1)
            items = [x.strip() for x in return_obj.split(',') if x.strip()]
            
            if len(items) > 20:
                line = script[:return_match.start()].count('\n') + offset + 1
                issues.append(Issue(
                    severity='info',
                    category='structure',
                    file=parser.filepath,
                    line=line,
                    message=f'Large return object ({len(items)} properties) exposes internal state',
                    suggestion='Group related properties: return { dataLayer: {...}, uiLayer: {...}, handlers: {...} }',
                    code=f'{len(items)} properties'
                ))
        
        return issues
    
    @staticmethod
    def check_component_imports(parser: VueSFCParser) -> List[Issue]:
        """Check for too many component imports"""
        issues = []
        script, offset = parser.get_script()
        
        # Count component imports
        import_pattern = r"import\s+\w+\s+from\s+'\.\..*\.vue'"
        imports = re.findall(import_pattern, script)
        
        if len(imports) > 5:
            line = offset + 1
            issues.append(Issue(
                severity='info',
                category='structure',
                file=parser.filepath,
                line=line,
                message=f'Component imports many sub-components ({len(imports)})',
                suggestion='Consider lazy loading: const ModalX = defineAsyncComponent(() => import("..."))',
                code=f'{len(imports)} component imports'
            ))
        
        return issues


class CrossFileAnalyzer:
    """Analyzes patterns across multiple files"""
    
    def __init__(self):
        self.file_methods: Dict[str, Set[str]] = defaultdict(set)
        self.duplicates: Dict[str, List[str]] = defaultdict(list)
    
    def collect_methods(self, filepath: str, parser: VueSFCParser):
        """Collect all method names from a file"""
        script, _ = parser.get_script()
        methods = re.findall(r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>', script)
        methods += re.findall(r'(?:const\s+)?(\w+)\s*:\s*\([^)]*\)\s*=>', script)
        self.file_methods[filepath] = set(methods)
    
    def find_duplicated_methods(self, threshold: int = 3) -> List[Tuple[str, List[str]]]:
        """Find method names that appear in multiple files"""
        method_to_files = defaultdict(list)
        
        for filepath, methods in self.file_methods.items():
            for method in methods:
                method_to_files[method].append(filepath)
        
        duplicates = [
            (method, files) 
            for method, files in method_to_files.items() 
            if len(files) >= threshold and method not in ['setup', 'loadData']
        ]
        
        return sorted(duplicates, key=lambda x: len(x[1]), reverse=True)
    
    def analyze_all_files(self, vue_dir: str) -> List[Issue]:
        """Scan all Vue files and find cross-file patterns"""
        issues = []
        
        vue_files = list(Path(vue_dir).rglob('*.vue'))
        
        for filepath in vue_files:
            parser = VueSFCParser(str(filepath))
            self.collect_methods(str(filepath), parser)
        
        # Find duplicated methods
        duplicates = self.find_duplicated_methods()
        
        for method, files in duplicates:
            # Only suggest extraction if it appears to be utility-like
            utility_patterns = ['translate', 'format', 'get', 'calculate', 'is']
            if any(p in method.lower() for p in utility_patterns):
                issue = Issue(
                    severity='info',
                    category='reuse',
                    file='[CROSS-FILE]',
                    line=0,
                    message=f'Method "{method}" duplicated across {len(files)} files',
                    suggestion=f'Extract to utils or composable. Found in: {", ".join(Path(f).name for f in files[:3])}{"..." if len(files) > 3 else ""}',
                    code=method
                )
                issues.append(issue)
        
        return issues


# ============================================================================
# Reporter
# ============================================================================

class AnalysisReporter:
    """Generates analysis reports"""
    
    def __init__(self, issues: List[Issue], metrics: List[ComponentMetrics]):
        self.issues = issues
        self.metrics = metrics
    
    def to_console(self) -> str:
        """Generate console output"""
        output = []
        output.append("\n" + "="*80)
        output.append("VUE COMPONENT STRUCTURE ANALYSIS & OPTIMIZATION REPORT")
        output.append("="*80 + "\n")
        
        # Summary
        by_severity = defaultdict(list)
        by_category = defaultdict(list)
        
        for issue in self.issues:
            by_severity[issue.severity].append(issue)
            by_category[issue.category].append(issue)
        
        output.append(f"[*] SUMMARY")
        output.append(f"  Total Issues: {len(self.issues)}")
        output.append(f"  Errors: {len(by_severity['error'])}")
        output.append(f"  Warnings: {len(by_severity['warning'])}")
        output.append(f"  Info: {len(by_severity['info'])}")
        output.append(f"  Components Analyzed: {len(self.metrics)}\n")
        
        # By Category
        output.append(f"[*] BY CATEGORY")
        for category in ['performance', 'reuse', 'structure']:
            count = len(by_category.get(category, []))
            if count > 0:
                output.append(f"  {category.capitalize()}: {count}")
        output.append("")
        
        # Metrics
        output.append(f"[*] COMPONENT METRICS")
        avg_lines = sum(m.lines for m in self.metrics) / len(self.metrics) if self.metrics else 0
        output.append(f"  Avg lines per component: {avg_lines:.0f}")
        output.append(f"  Avg methods per component: {sum(m.methods_count for m in self.metrics) / len(self.metrics) if self.metrics else 0:.0f}")
        output.append(f"  Components with watchers: {sum(1 for m in self.metrics if m.has_watch)}")
        output.append("")
        
        # Issues by Severity
        for severity in ['error', 'warning', 'info']:
            severity_issues = by_severity.get(severity, [])
            if severity_issues:
                prefix = '[ERR]' if severity == 'error' else '[WRN]' if severity == 'warning' else '[INFO]'
                output.append(f"{prefix} {severity.upper()} ({len(severity_issues)})")
                output.append("-" * 80)
                
                for issue in severity_issues[:5]:  # Show first 5 per severity
                    output.append(f"\n  [*] {issue.file.split('/')[-1]}:{issue.line}")
                    output.append(f"     Category: {issue.category}")
                    output.append(f"     {issue.message}")
                    if issue.code:
                        output.append(f"     Code: {issue.code}")
                    output.append(f"     [*] Suggestion: {issue.suggestion}")
                
                if len(severity_issues) > 5:
                    output.append(f"\n  ... and {len(severity_issues) - 5} more {severity}(s)")
                output.append("")
        
        # Top Recommendations
        output.append("[*] TOP OPTIMIZATION OPPORTUNITIES")
        output.append("-" * 80)
        
        reuse_issues = by_category.get('reuse', [])
        performance_issues = by_category.get('performance', [])
        
        if reuse_issues:
            output.append(f"\n1. Extract Reusable Logic ({len(reuse_issues)} opportunities)")
            for issue in reuse_issues[:3]:
                output.append(f"   * {issue.suggestion} ({issue.file.split('/')[-1]})")
        
        if performance_issues:
            output.append(f"\n2. Performance Optimizations ({len(performance_issues)} opportunities)")
            for issue in performance_issues[:3]:
                output.append(f"   * {issue.suggestion} ({issue.file.split('/')[-1]})")
        
        # Structural improvements
        structure_issues = by_category.get('structure', [])
        if structure_issues:
            output.append(f"\n3. Structural Improvements ({len(structure_issues)} opportunities)")
            for issue in structure_issues[:3]:
                output.append(f"   * {issue.suggestion} ({issue.file.split('/')[-1]})")
        
        output.append("\n" + "="*80 + "\n")
        
        return "\n".join(output)
    
    def to_json(self) -> str:
        """Generate JSON output"""
        data = {
            'summary': {
                'total_issues': len(self.issues),
                'errors': len([i for i in self.issues if i.severity == 'error']),
                'warnings': len([i for i in self.issues if i.severity == 'warning']),
                'info': len([i for i in self.issues if i.severity == 'info']),
                'components_analyzed': len(self.metrics),
            },
            'issues': [asdict(i) for i in self.issues],
            'metrics': [asdict(m) for m in self.metrics],
        }
        return json.dumps(data, indent=2)


# ============================================================================
# Main Analysis Engine
# ============================================================================

class VueAnalyzer:
    """Main analyzer orchestrator"""
    
    def __init__(self, vue_dir: str):
        self.vue_dir = vue_dir
        self.issues: List[Issue] = []
        self.metrics: List[ComponentMetrics] = []
    
    def analyze(self) -> Tuple[List[Issue], List[ComponentMetrics]]:
        """Run full analysis on all Vue files"""
        vue_files = list(Path(self.vue_dir).rglob('*.vue'))
        
        print(f"[*] Analyzing {len(vue_files)} Vue files...\n")
        
        # Single-file analysis
        for filepath in vue_files:
            print(f"  * {filepath.relative_to(self.vue_dir)}")
            self._analyze_file(str(filepath))
        
        # Cross-file analysis
        print(f"\n[*] Analyzing cross-file patterns...\n")
        cross_analyzer = CrossFileAnalyzer()
        cross_issues = cross_analyzer.analyze_all_files(self.vue_dir)
        self.issues.extend(cross_issues)
        
        return self.issues, self.metrics
    
    def _analyze_file(self, filepath: str):
        """Analyze a single Vue file"""
        parser = VueSFCParser(filepath)
        
        # Performance checks
        self.issues.extend(PerformanceAnalyzer.check_v_for_keys(parser))
        self.issues.extend(PerformanceAnalyzer.check_v_if_v_for_nesting(parser))
        self.issues.extend(PerformanceAnalyzer.check_complex_expressions(parser))
        self.issues.extend(PerformanceAnalyzer.check_watchers_with_immediate(parser))
        
        # Code reuse checks
        self.issues.extend(CodeReuseAnalyzer.check_duplicated_methods(parser))
        self.issues.extend(CodeReuseAnalyzer.check_shared_state_patterns(parser))
        self.issues.extend(CodeReuseAnalyzer.check_duplicate_loading_pattern(parser))
        
        # Structure checks
        self.issues.extend(StructureAnalyzer.check_large_setup_function(parser))
        self.issues.extend(StructureAnalyzer.check_return_statement_size(parser))
        self.issues.extend(StructureAnalyzer.check_component_imports(parser))
        
        # Collect metrics
        script, _ = parser.get_script()
        template, _ = parser.get_template()
        
        methods = len(re.findall(r'const\s+\w+\s*=\s*\([^)]*\)\s*=>', script))
        computed = len(re.findall(r'const\s+\w+\s*=\s*computed\(', script))
        hooks = len(re.findall(r'(onMounted|onUnmounted|onUpdated|onBeforeMount|onBeforeUnmount|watch)\(', script))
        imports = len(re.findall(r'import\s+', script))
        refs = len(re.findall(r'const\s+\w+\s*=\s*ref\(', script))
        
        file_issues = len([i for i in self.issues if i.file == filepath])
        total_lines = len(template.split('\n')) + len(script.split('\n'))
        
        self.metrics.append(ComponentMetrics(
            file=filepath,
            lines=total_lines,
            methods_count=methods,
            computed_count=computed,
            hooks_count=hooks,
            imports_count=imports,
            has_watch='watch(' in script,
            has_on_mounted='onMounted(' in script,
            data_refs=refs,
            unique_issues=file_issues
        ))


def main():
    """Main entry point"""
    import sys
    
    # Find Vue directory
    client_dir = Path(__file__).parent.parent / 'client' / 'src'
    
    if not client_dir.exists():
        print(f"ERROR: Vue source directory not found: {client_dir}")
        sys.exit(1)
    
    # Run analysis
    analyzer = VueAnalyzer(str(client_dir))
    issues, metrics = analyzer.analyze()
    
    # Generate report
    reporter = AnalysisReporter(issues, metrics)
    
    # Print to console
    print(reporter.to_console())
    
    # Save JSON report
    report_path = Path(__file__).parent / 'vue-analysis-report.json'
    with open(report_path, 'w') as f:
        f.write(reporter.to_json())
    print(f"Report saved to: {report_path}\n")
    
    # Exit with error code if critical issues found
    critical_count = len([i for i in issues if i.severity == 'error'])
    sys.exit(1 if critical_count > 0 else 0)


if __name__ == '__main__':
    main()
