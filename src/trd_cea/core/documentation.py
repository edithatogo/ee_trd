"""
Documentation and Knowledge Management System

Automated documentation generation, API documentation, and knowledge management
for health economic evaluation models.
"""

import os
import sys
import inspect
import json
import yaml
import pandas as pd
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Callable, Type
import importlib
import pydoc
from docutils.core import publish_doctree, publish_string
from sphinx.application import Sphinx
import numpy as np
import logging
from functools import wraps


class DocumentationGenerator:
    """
    Automated documentation generator for health economic analysis tools.
    Creates API documentation, parameter documentation, and analysis guides.
    """
    
    def __init__(self, source_dir: str = "scripts", output_dir: str = "docs/api"):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def scan_modules(self) -> Dict[str, Any]:
        """Scan all modules in the source directory and extract documentation."""
        modules = {}
        
        for py_file in self.source_dir.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            module_path = py_file.relative_to(self.source_dir.parent)
            module_name = str(module_path.with_suffix("")).replace(os.sep, ".")
            
            try:
                # Import the module
                spec = importlib.util.spec_from_file_location(module_name, py_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Extract module information
                module_info = self._extract_module_info(module)
                modules[module_name] = module_info
                
                self.logger.info(f"Processed module: {module_name}")
                
            except Exception as e:
                self.logger.warning(f"Could not process module {module_name}: {str(e)}")
        
        return modules
    
    def _extract_module_info(self, module) -> Dict[str, Any]:
        """Extract information from a module."""
        module_doc = inspect.getdoc(module) or ""
        
        # Extract classes
        classes = {}
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not name.startswith('_'):
                classes[name] = self._extract_class_info(obj)
        
        # Extract functions
        functions = {}
        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith('_'):
                functions[name] = self._extract_function_info(obj)
        
        return {
            'docstring': module_doc,
            'file': inspect.getfile(module) if hasattr(module, '__file__') else 'unknown',
            'classes': classes,
            'functions': functions,
            'module': module.__name__ if hasattr(module, '__name__') else 'unknown'
        }
    
    def _extract_class_info(self, cls) -> Dict[str, Any]:
        """Extract information about a class."""
        class_doc = inspect.getdoc(cls) or ""
        
        # Get methods
        methods = {}
        for name, method in inspect.getmembers(cls, lambda x: inspect.isfunction(x) or inspect.ismethod(x)):
            if not name.startswith('_') or name in ['__init__']:
                methods[name] = self._extract_function_info(method)
        
        # Get inheritance
        bases = [base.__name__ for base in cls.__bases__ if base != object]
        
        return {
            'docstring': class_doc,
            'methods': methods,
            'bases': bases,
            'module': cls.__module__,
            'signature': str(inspect.signature(cls.__init__)) if '__init__' in dir(cls) else 'No __init__ found'
        }
    
    def _extract_function_info(self, func) -> Dict[str, Any]:
        """Extract information about a function."""
        func_doc = inspect.getdoc(func) or ""
        
        try:
            sig = inspect.signature(func)
        except (ValueError, TypeError):
            sig = 'Unable to extract signature'
        
        # Get source code snippet
        try:
            source_lines = inspect.getsourcelines(func)[0][:5]  # First 5 lines
            source_snippet = ''.join(source_lines)
        except:
            source_snippet = 'Source unavailable'
        
        # Get function parameters
        params = {}
        if isinstance(sig, str) and sig == 'Unable to extract signature':
            params = 'Signature unavailable'
        else:
            for param_name, param in sig.parameters.items():
                params[param_name] = {
                    'kind': param.kind.name,
                    'default': param.default if param.default != inspect.Parameter.empty else 'No default',
                    'annotation': param.annotation if param.annotation != inspect.Parameter.empty else 'No annotation'
                }
        
        return {
            'name': func.__name__,
            'docstring': func_doc,
            'signature': str(sig),
            'parameters': params,
            'return_annotation': getattr(func, '__annotations__', {}).get('return', 'No return annotation'),
            'module': func.__module__,
            'source_snippet': source_snippet
        }
    
    def generate_api_documentation(self, modules_info: Dict[str, Any]) -> str:
        """Generate API documentation in Markdown format."""
        doc_parts = [
            "# API Documentation",
            f"Generated at: {datetime.now().isoformat()}",
            "",
            "## Table of Contents",
            ""
        ]
        
        # Add TOC entries
        for module_name in sorted(modules_info.keys()):
            doc_parts.append(f"- [{module_name}](#{module_name.replace('.', '-')})")
            
            # Add function and class links within the module
            module_info = modules_info[module_name]
            for func_name in sorted(module_info.get('functions', {}).keys()):
                doc_parts.append(f"  - [{func_name}](#{func_name})")
            for class_name in sorted(module_info.get('classes', {}).keys()):
                doc_parts.append(f"  - [{class_name}](#{class_name})")
        
        doc_parts.append("")  # Empty line after TOC
        
        # Generate documentation for each module
        for module_name, module_info in sorted(modules_info.items()):
            doc_parts.extend([
                f"## {module_name}",
                f"**File**: `{module_info['file']}`",
                ""
            ])
            
            if module_info.get('docstring'):
                doc_parts.extend([
                    "### Description",
                    module_info['docstring'],
                    ""
                ])
            
            # Document classes
            for class_name, class_info in sorted(module_info.get('classes', {}).items()):
                doc_parts.extend([
                    f"### Class: {class_name}",
                    f"**Signature**: `{class_info['signature']}`",
                    ""
                ])
                
                if class_info.get('docstring'):
                    doc_parts.extend([
                        class_info['docstring'],
                        ""
                    ])
                
                if class_info.get('bases'):
                    doc_parts.extend([
                        "**Inherits from**: " + ", ".join(class_info['bases']),
                        ""
                    ])
                
                # Document class methods
                for method_name, method_info in sorted(class_info['methods'].items()):
                    doc_parts.extend([
                        f"#### Method: `{method_name}`",
                        f"**Signature**: `{method_info['signature']}`",
                        ""
                    ])
                    
                    if method_info.get('docstring'):
                        doc_parts.extend([
                            method_info['docstring'],
                            ""
                        ])
                    
                    # Document parameters
                    if isinstance(method_info['parameters'], dict):
                        if method_info['parameters']:
                            doc_parts.append("**Parameters:**")
                            for param_name, param_info in method_info['parameters'].items():
                                if isinstance(param_info, dict):
                                    default_val = param_info['default']
                                    default_str = f"`{default_val}`" if default_val != 'No default' else "*required*"
                                    annotation = param_info['annotation']
                                    annotation_str = f"`{annotation}`" if annotation != 'No annotation' else ""
                                    
                                    doc_parts.append(f"- `{param_name}` {annotation_str}: {default_str}")
                            doc_parts.append("")
            
            # Document functions
            for func_name, func_info in sorted(module_info.get('functions', {}).items()):
                doc_parts.extend([
                    f"### Function: `{func_name}`",
                    f"**Signature**: `{func_info['signature']}`",
                    ""
                ])
                
                if func_info.get('docstring'):
                    doc_parts.extend([
                        func_info['docstring'],
                        ""
                    ])
                
                # Document parameters
                if isinstance(func_info['parameters'], dict):
                    if func_info['parameters']:
                        doc_parts.append("**Parameters:**")
                        for param_name, param_info in func_info['parameters'].items():
                            if isinstance(param_info, dict):
                                default_val = param_info['default']
                                default_str = f"`{default_val}`" if default_val != 'No default' else "*required*"
                                annotation = param_info['annotation']
                                annotation_str = f"`{annotation}`" if annotation != 'No annotation' else ""
                                
                                doc_parts.append(f"- `{param_name}` {annotation_str}: {default_str}")
                        doc_parts.append("")
                
                # Document return value
                if func_info.get('return_annotation') and func_info['return_annotation'] != 'No return annotation':
                    doc_parts.extend([
                        f"**Returns**: `{func_info['return_annotation']}`",
                        ""
                    ])
            
            doc_parts.append("---")  # Separator between modules
        
        api_doc_content = "\n".join(doc_parts)
        
        # Write API documentation
        api_doc_path = self.output_dir / "api_documentation.md"
        with open(api_doc_path, 'w', encoding='utf-8') as f:
            f.write(api_doc_content)
        
        self.logger.info(f"API documentation generated at {api_doc_path}")
        return str(api_doc_path)
    
    def generate_parameter_documentation(self, config_dir: str = "config") -> str:
        """Generate documentation for configuration parameters."""
        config_path = Path(config_dir)
        param_docs = []
        
        param_docs.extend([
            "# Configuration Parameters Documentation",
            f"Generated at: {datetime.now().isoformat()}",
            "",
            "This document describes the configuration parameters used in the health economic evaluation models.",
            ""
        ])
        
        # Process configuration files
        for config_file in config_path.rglob("*.y*ml"):  # Both .yml and .yaml
            try:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                param_docs.extend([
                    f"## Configuration File: {config_file.name}",
                    "",
                    "| Parameter | Type | Description | Default | Notes |",
                    "|-----------|------|-------------|---------|-------|"
                ])
                
                self._extract_config_params(config_data, param_docs, "")
                
                param_docs.append("")  # Spacer between files
                
            except Exception as e:
                self.logger.warning(f"Could not process config file {config_file}: {str(e)}")
        
        param_doc_content = "\n".join(param_docs)
        
        # Write parameter documentation
        param_doc_path = self.output_dir / "parameter_documentation.md"
        with open(param_doc_path, 'w', encoding='utf-8') as f:
            f.write(param_doc_content)
        
        self.logger.info(f"Parameter documentation generated at {param_doc_path}")
        return str(param_doc_path)
    
    def _extract_config_params(self, data: Any, doc_list: List[str], prefix: str = ""):
        """Recursively extract parameters from configuration data."""
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                
                if isinstance(value, dict):
                    # Nested dictionary - process recursively
                    self._extract_config_params(value, doc_list, full_key)
                else:
                    # Leaf value - document it
                    param_type = type(value).__name__
                    default_val = str(value) if value is not None else "null"
                    
                    # Add a brief description based on the parameter name
                    description = self._infer_param_description(full_key)
                    
                    doc_list.append(f"| `{full_key}` | `{param_type}` | {description} | `{default_val}` | |")
        elif isinstance(data, list):
            # For lists, document as a generic list parameter
            for i, item in enumerate(data):
                full_key = f"{prefix}[{i}]"
                if isinstance(item, (dict, list)):
                    self._extract_config_params(item, doc_list, full_key)
                else:
                    param_type = type(item).__name__
                    doc_list.append(f"| `{full_key}` | `{param_type}` | List element | `{item}` | |")
    
    def _infer_param_description(self, param_name: str) -> str:
        """Infer parameter description based on its name."""
        descriptions = {
            'wtp': 'Willingness-to-pay threshold for health economic evaluation',
            'cost': 'Cost parameter for interventions',
            'effect': 'Effectiveness parameter (usually QALYs)',
            'discount': 'Discount rate for future costs and effects',
            'time_horizon': 'Time horizon for the analysis',
            'lambda': 'Willingness-to-pay parameter (lambda)',
            'n_simulations': 'Number of simulations for probabilistic analysis',
            'strategy': 'Treatment strategy identifier',
            'perspective': 'Economic perspective (healthcare, societal, etc.)',
            'jurisdiction': 'Geographic jurisdiction for analysis',
            'base_case': 'Base case parameter values',
            'sensitivity': 'Parameters for sensitivity analysis',
        }
        
        # Look for partial matches
        for key, desc in descriptions.items():
            if key in param_name.lower():
                return desc
        
        # If no match, return a generic description
        return f"Configuration parameter for {param_name}"
    
    def generate_analysis_documentation(self, analysis_scripts_dir: str = "scripts/analysis") -> str:
        """Generate documentation for analysis workflows."""
        analysis_path = Path(analysis_scripts_dir)
        analysis_docs = []
        
        analysis_docs.extend([
            "# Analysis Workflows Documentation",
            f"Generated at: {datetime.now().isoformat()}",
            "",
            "This document describes the analysis workflows and scripts available in the toolkit.",
            ""
        ])
        
        for script_file in analysis_path.rglob("*.py"):
            if "__pycache__" not in str(script_file):
                try:
                    with open(script_file, 'r') as f:
                        content = f.read()
                    
                    # Extract function definitions and their docstrings
                    functions = self._extract_functions_from_script(content)
                    
                    relative_path = script_file.relative_to(Path('.'))
                    analysis_docs.extend([
                        f"## Script: {relative_path}",
                        ""
                    ])
                    
                    if functions:
                        analysis_docs.extend([
                            "| Function | Description |",
                            "|----------|-------------|"
                        ])
                        for func_name, docstring in functions:
                            clean_docstring = (docstring.split('.')[0] + '.' if docstring and '.' in docstring 
                                             else docstring[:50] + "..." if len(docstring) > 50 else docstring)
                            analysis_docs.append(f"| `{func_name}` | {clean_docstring or 'No description'} |")
                    else:
                        analysis_docs.append("No functions with docstrings found in this script.")
                    
                    analysis_docs.append("")  # Space between scripts
                    
                except Exception as e:
                    self.logger.warning(f"Could not process analysis script {script_file}: {str(e)}")
        
        analysis_doc_content = "\n".join(analysis_docs)
        
        # Write analysis documentation
        analysis_doc_path = self.output_dir / "analysis_documentation.md"
        with open(analysis_doc_path, 'w', encoding='utf-8') as f:
            f.write(analysis_doc_content)
        
        self.logger.info(f"Analysis documentation generated at {analysis_doc_path}")
        return str(analysis_doc_path)
    
    def _extract_functions_from_script(self, content: str) -> List[tuple]:
        """Extract function names and docstrings from script content."""
        import ast
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return []  # Return empty list if syntax error
        
        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node)
                functions.append((node.name, docstring or ""))
        
        return functions


class KnowledgeManagementSystem:
    """
    Knowledge management system for storing and retrieving analysis knowledge,
    best practices, and lessons learned.
    """
    
    def __init__(self, knowledge_base_path: str = "knowledge_base/"):
        self.knowledge_base = Path(knowledge_base_path)
        self.knowledge_base.mkdir(exist_ok=True)
        
        # Initialize knowledge categories
        self.categories = ['best_practices', 'lessons_learned', 'methodology_notes', 'parameter_guidelines']
        for category in self.categories:
            (self.knowledge_base / category).mkdir(exist_ok=True)
        
        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def store_knowledge(self, 
                       topic: str, 
                       content: str, 
                       category: str = 'best_practices', 
                       tags: List[str] = None,
                       metadata: Dict[str, Any] = None) -> str:
        """Store a knowledge article."""
        if tags is None:
            tags = []
        if metadata is None:
            metadata = {}
        
        # Create a unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = self._create_slug(topic)
        filename = f"{slug}_{timestamp}.md"
        
        knowledge_path = self.knowledge_base / category / filename
        
        # Create content with metadata header
        content_with_metadata = self._add_metadata_header(content, topic, tags, metadata)
        
        with open(knowledge_path, 'w', encoding='utf-8') as f:
            f.write(content_with_metadata)
        
        self.logger.info(f"Knowledge article '{topic}' stored in {knowledge_path}")
        return str(knowledge_path)
    
    def _create_slug(self, text: str) -> str:
        """Create a URL-friendly slug from text."""
        import re
        # Convert to lowercase and replace non-alphanumeric chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', text.lower())
        slug = re.sub(r'[-\s]+', '-', slug).strip('-')
        return slug
    
    def _add_metadata_header(self, content: str, topic: str, tags: List[str], metadata: Dict[str, Any]) -> str:
        """Add metadata header to knowledge article."""
        header_parts = [
            "---",
            f"title: \"{topic}\"",
            f"date_created: \"{datetime.now().isoformat()}\"",
            f"tags: [{', '.join([f'\"{tag}\"' for tag in tags])}]",
            "metadata:",
        ]
        
        for key, value in metadata.items():
            header_parts.append(f"  {key}: {json.dumps(value)}")
        
        header_parts.append("---")
        header_parts.append("")  # Empty line after frontmatter
        
        return "\n".join(header_parts) + content
    
    def retrieve_knowledge(self, 
                          query: str = "", 
                          category: str = None, 
                          tags: List[str] = None) -> List[Dict[str, Any]]:
        """Retrieve knowledge articles based on query, category, or tags."""
        results = []
        
        search_paths = [self.knowledge_base] if category is None else [self.knowledge_base / category]
        
        for search_path in search_paths:
            if not search_path.exists():
                continue
                
            for knowledge_file in search_path.rglob("*.md"):
                try:
                    with open(knowledge_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Extract metadata if present
                    metadata = self._extract_metadata(content)
                    content_body = self._remove_metadata_header(content)
                    
                    # Check if article matches query criteria
                    matches_query = self._match_article(query, content_body, metadata)
                    matches_tags = self._match_tags(tags, metadata.get('tags', []))
                    
                    if (not query or matches_query) and (tags is None or matches_tags):
                        results.append({
                            'title': metadata.get('title', knowledge_file.stem),
                            'category': knowledge_file.parent.name,
                            'path': str(knowledge_file),
                            'content_preview': content_body[:200] + "...",
                            'metadata': metadata,
                            'last_modified': datetime.fromtimestamp(knowledge_file.stat().st_mtime).isoformat()
                        })
                
                except Exception as e:
                    self.logger.warning(f"Could not read knowledge file {knowledge_file}: {str(e)}")
        
        return results
    
    def _extract_metadata(self, content: str) -> Dict[str, Any]:
        """Extract metadata from content header."""
        if content.startswith('---'):
            try:
                end_header = content.find('---', 3)  # Find closing ---
                if end_header != -1:
                    header_content = content[3:end_header].strip()
                    return yaml.safe_load(header_content) or {}
            except:
                pass
        
        return {}
    
    def _remove_metadata_header(self, content: str) -> str:
        """Remove metadata header from content."""
        if content.startswith('---'):
            try:
                end_header = content.find('---', 3)
                if end_header != -1:
                    return content[end_header + 3:].strip()
            except:
                pass
        
        return content
    
    def _match_article(self, query: str, content: str, metadata: Dict[str, Any]) -> bool:
        """Check if article matches the query."""
        if not query:
            return True  # If no query, match all
        
        query_lower = query.lower()
        
        # Check in title
        if query_lower in metadata.get('title', '').lower():
            return True
        
        # Check in content
        if query_lower in content.lower():
            return True
        
        # Check in tags
        tags = [str(tag).lower() for tag in metadata.get('tags', [])]
        if any(query_lower in tag for tag in tags):
            return True
        
        return False
    
    def _match_tags(self, required_tags: List[str], article_tags: List[str]) -> bool:
        """Check if article contains all required tags."""
        if required_tags is None:
            return True  # If no tag filter, match all
        
        if not required_tags:
            return True  # If tag filter is empty, match all
        
        article_tags_lower = [str(tag).lower() for tag in article_tags]
        required_tags_lower = [tag.lower() for tag in required_tags]
        
        return all(tag in article_tags_lower for tag in required_tags_lower)
    
    def generate_knowledge_summary(self) -> str:
        """Generate a summary of the knowledge base."""
        summary_parts = [
            "# Knowledge Base Summary",
            f"Generated at: {datetime.now().isoformat()}",
            "",
            "## Categories",
            ""
        ]
        
        for category in self.categories:
            category_path = self.knowledge_base / category
            if category_path.exists():
                article_count = len(list(category_path.rglob("*.md")))
                summary_parts.append(f"- {category}: {article_count} articles")
        
        summary_parts.extend([
            "",
            "## Recent Additions",
            "| Title | Category | Date Added | Tags |",
            "|-------|----------|------------|------|"
        ])
        
        # Get recent articles (last 10)
        all_articles = []
        for category in self.categories:
            category_path = self.knowledge_base / category
            if category_path.exists():
                for file in category_path.rglob("*.md"):
                    all_articles.append(file)
        
        # Sort by modification time (most recent first)
        all_articles.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        recent_articles = all_articles[:10]
        
        for article_path in recent_articles:
            try:
                content = open(article_path, 'r', encoding='utf-8').read()
                metadata = self._extract_metadata(content)
                
                title = metadata.get('title', article_path.stem)
                category = article_path.parent.name
                date_added = datetime.fromtimestamp(article_path.stat().st_mtime).strftime('%Y-%m-%d')
                tags = ', '.join(metadata.get('tags', []))
                
                summary_parts.append(f"| {title} | {category} | {date_added} | {tags} |")
            except:
                # Skip if there's an error reading the file
                continue
        
        summary_content = "\n".join(summary_parts)
        
        summary_path = self.knowledge_base / "knowledge_summary.md"
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        self.logger.info(f"Knowledge base summary generated at {summary_path}")
        return str(summary_path)


class AutoDocumentationDecorator:
    """
    Decorator to automatically document function usage and create usage examples.
    """
    
    def __init__(self, doc_section: str = "functions"):
        self.doc_section = doc_section
        self.documentation_log = []
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Log function usage
            usage_info = {
                'function': func.__name__,
                'module': func.__module__,
                'args': str(args),
                'kwargs': str(kwargs),
                'timestamp': datetime.now().isoformat()
            }
            self.documentation_log.append(usage_info)
            
            # Execute the original function
            result = func(*args, **kwargs)
            
            return result
        
        # Add documentation attributes to the wrapper
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        wrapper.__module__ = func.__module__
        
        # Store reference to the original function
        wrapper._original_func = func
        wrapper._usage_log = self.documentation_log
        
        return wrapper
    
    def export_usage_examples(self, filename: str = "usage_examples.md") -> str:
        """Export collected usage examples to a documentation file."""
        if not self.documentation_log:
            return ""
        
        doc_parts = [
            f"# Usage Examples - {self.doc_section}",
            f"Collected at: {datetime.now().isoformat()}",
            "",
            "## Function Usage Examples",
            ""
        ]
        
        # Group by function
        usage_by_func = {}
        for usage in self.documentation_log:
            func_name = usage['function']
            if func_name not in usage_by_func:
                usage_by_func[func_name] = []
            usage_by_func[func_name].append(usage)
        
        for func_name, usages in usage_by_func.items():
            doc_parts.append(f"### `{func_name}`")
            doc_parts.append("")
            
            for i, usage in enumerate(usages[:3], 1):  # Show first 3 examples
                doc_parts.append(f"**Example {i}:**")
                doc_parts.append(f"- Args: {usage['args']}")
                doc_parts.append(f"- Kwargs: {usage['kwargs']}")
                doc_parts.append("")
        
        content = "\n".join(doc_parts)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filename


def create_automated_documentation():
    """
    Create automated documentation for the entire health economic evaluation toolkit.
    """
    print("Generating automated documentation...")
    
    # Initialize documentation generator
    doc_gen = DocumentationGenerator()
    
    # Scan modules
    print("Scanning modules...")
    modules_info = doc_gen.scan_modules()
    
    # Generate API documentation
    print("Generating API documentation...")
    api_doc_path = doc_gen.generate_api_documentation(modules_info)
    
    # Generate parameter documentation
    print("Generating parameter documentation...")
    param_doc_path = doc_gen.generate_parameter_documentation()
    
    # Generate analysis documentation
    print("Generating analysis workflow documentation...")
    analysis_doc_path = doc_gen.generate_analysis_documentation()
    
    # Initialize knowledge management system
    print("Setting up knowledge management system...")
    kms = KnowledgeManagementSystem()
    
    # Create a summary of the documentation
    print("Creating documentation summary...")
    summary = {
        "generation_time": datetime.now().isoformat(),
        "api_documentation": api_doc_path,
        "parameter_documentation": param_doc_path,
        "analysis_documentation": analysis_doc_path,
        "module_count": len(modules_info)
    }
    
    # Store summary in knowledge base
    kms.store_knowledge(
        topic="Documentation Summary",
        content=json.dumps(summary, indent=2),
        category="system_documentation",
        tags=["documentation", "summary", "automated"],
        metadata={"doc_types": ["api", "parameters", "analysis"], "module_count": len(modules_info)}
    )
    
    # Generate knowledge base summary
    kb_summary = kms.generate_knowledge_summary()
    
    print(f"Documentation generation completed!")
    print(f"- API Documentation: {api_doc_path}")
    print(f"- Parameter Documentation: {param_doc_path}")
    print(f"- Analysis Documentation: {analysis_doc_path}")
    print(f"- Knowledge Base Summary: {kb_summary}")
    
    return {
        "api_docs": api_doc_path,
        "parameter_docs": param_doc_path,
        "analysis_docs": analysis_doc_path,
        "knowledge_base_summary": kb_summary,
        "module_count": len(modules_info)
    }


if __name__ == "__main__":
    # Generate comprehensive documentation
    doc_results = create_automated_documentation()
    print(f"Generated documentation for {doc_results['module_count']} modules")