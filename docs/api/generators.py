"""
API Documentation Generation System

This module provides automated documentation generation for the V4 Health Economic
Framework, including API documentation, engine documentation, and user guides.

The documentation system generates:
- API reference documentation from docstrings
- Engine capability documentation
- Configuration schema documentation
- Usage examples and tutorials
- Performance and testing reports
"""

import inspect
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Type, Callable
from dataclasses import dataclass, field
from datetime import datetime
import importlib

try:
    import jinja2
    JINJA2_AVAILABLE = True
except ImportError:
    JINJA2_AVAILABLE = False


@dataclass
class DocumentationMetadata:
    """Metadata for documentation generation."""
    title: str
    version: str
    description: str
    author: str
    generated_date: str = field(default_factory=lambda: datetime.now().isoformat())
    framework_version: str = "4.0.0"
    output_formats: List[str] = field(default_factory=lambda: ["markdown", "html"])


@dataclass
class APIDocumentation:
    """Container for API documentation."""
    module_name: str
    classes: List[Dict[str, Any]] = field(default_factory=list)
    functions: List[Dict[str, Any]] = field(default_factory=list)
    constants: List[Dict[str, Any]] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    cross_references: List[str] = field(default_factory=list)


class DocumentationGenerator:
    """
    Main documentation generator for the V4 framework.

    This class provides methods to generate comprehensive documentation
    for modules, classes, functions, and engines in various formats.
    """

    def __init__(self, metadata: Optional[DocumentationMetadata] = None):
        """Initialize documentation generator."""
        self.metadata = metadata or DocumentationMetadata(
            title="V4 Health Economic Framework",
            version="4.0.0",
            description="Comprehensive health economic evaluation framework for psychedelic therapies vs ECT",
            author="V4 Development Team"
        )

        # Defensive: tests may pass a MagicMock or partial metadata; ensure output_formats exists
        try:
            if not getattr(self.metadata, 'output_formats', None):
                self.metadata.output_formats = ["markdown", "html"]
        except Exception:
            # If metadata is a MagicMock-like object where attribute access fails, fallback
            try:
                self.metadata.output_formats = ["markdown", "html"]
            except Exception:
                pass

        # Setup Jinja2 environment if available
        if JINJA2_AVAILABLE:
            self.jinja_env = jinja2.Environment(
                loader=jinja2.PackageLoader('docs.api', 'templates'),
                autoescape=jinja2.select_autoescape(['html', 'xml'])
            )
        else:
            self.jinja_env = None

    def generate_module_documentation(self, module_path: str, output_dir: Path) -> None:
        """
        Generate documentation for a complete module.

        Args:
            module_path: Import path to the module
            output_dir: Directory to save generated documentation
        """
        try:
            # Import the module
            module = importlib.import_module(module_path)

            # Generate API documentation
            api_docs = self._extract_api_documentation(module)

            # Generate different output formats
            for format_type in self.metadata.output_formats:
                self._generate_format_documentation(api_docs, output_dir, format_type)

        except ImportError as e:
            print(f"Warning: Could not import module {module_path}: {e}")
        except Exception as e:
            print(f"Error generating documentation for {module_path}: {e}")

    def generate_engine_documentation(self, output_dir: Path) -> None:
        """
        Generate documentation for all registered engines.

        Args:
            output_dir: Directory to save generated documentation
        """
        try:
            from analysis.engines.registry import get_registry

            registry = get_registry()
            engines = registry.list_engines()

            engine_docs = []

            for engine_name in engines:
                engine_info = registry.get_engine(engine_name)
                if engine_info:
                    engine_docs.append(self._extract_engine_documentation(engine_info))

            # Generate engine documentation
            for format_type in self.metadata.output_formats:
                self._generate_engine_format_documentation(engine_docs, output_dir, format_type)

        except Exception as e:
            print(f"Error generating engine documentation: {e}")

    def generate_configuration_documentation(self, output_dir: Path) -> None:
        """
        Generate documentation for configuration schemas.

        Args:
            output_dir: Directory to save generated documentation
        """
        try:
            from analysis.core.config import V4Config, EngineConfig, AsyncConfig, PerformanceConfig

            config_docs = {
                'main_config': self._extract_class_documentation(V4Config),
                'engine_config': self._extract_class_documentation(EngineConfig),
                'async_config': self._extract_class_documentation(AsyncConfig),
                'performance_config': self._extract_class_documentation(PerformanceConfig)
            }

            # Generate configuration documentation
            for format_type in self.metadata.output_formats:
                self._generate_config_format_documentation(config_docs, output_dir, format_type)

        except Exception as e:
            print(f"Error generating configuration documentation: {e}")

    def _extract_api_documentation(self, module) -> APIDocumentation:
        """Extract API documentation from a module."""
        api_docs = APIDocumentation(module_name=module.__name__)

        for name, obj in inspect.getmembers(module):
            if name.startswith('_'):
                continue  # Skip private members

            if inspect.isclass(obj):
                class_doc = self._extract_class_documentation(obj)
                api_docs.classes.append(class_doc)
            elif inspect.isfunction(obj):
                func_doc = self._extract_function_documentation(obj)
                api_docs.functions.append(func_doc)
            elif inspect.ismodule(obj):
                continue  # Skip submodules for now
            else:
                # Check for constants and variables
                if not callable(obj):
                    const_doc = self._extract_constant_documentation(name, obj)
                    api_docs.constants.append(const_doc)

        return api_docs

    def _extract_class_documentation(self, cls: Type) -> Dict[str, Any]:
        """Extract documentation for a class."""
        doc = {
            'name': cls.__name__,
            'docstring': inspect.getdoc(cls) or "",
            'module': cls.__module__,
            'methods': [],
            'properties': [],
            'attributes': [],
            'inheritance': []
        }

        # Get method resolution order for inheritance
        try:
            doc['inheritance'] = [base.__name__ for base in cls.__mro__ if base != object]
        except AttributeError:
            pass

        # Extract methods
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            if not name.startswith('_') or name in ['__init__', '__call__']:
                method_doc = self._extract_method_documentation(name, method)
                doc['methods'].append(method_doc)

        # Extract properties
        for name, value in inspect.getmembers(cls):
            if isinstance(value, property):
                prop_doc = self._extract_property_documentation(name, value)
                doc['properties'].append(prop_doc)
            elif not name.startswith('_') and not callable(value):
                attr_doc = self._extract_attribute_documentation(name, value)
                doc['attributes'].append(attr_doc)

        return doc

    def _extract_function_documentation(self, func: Callable) -> Dict[str, Any]:
        """Extract documentation for a function."""
        sig = inspect.signature(func)

        return {
            'name': func.__name__,
            'signature': str(sig),
            'docstring': inspect.getdoc(func) or "",
            'parameters': self._extract_parameters(sig),
            'return_type': self._get_return_type_annotation(func),
            'module': func.__module__
        }

    def _extract_method_documentation(self, name: str, method: Callable) -> Dict[str, Any]:
        """Extract documentation for a method."""
        sig = inspect.signature(method)

        return {
            'name': name,
            'signature': str(sig),
            'docstring': inspect.getdoc(method) or "",
            'parameters': self._extract_parameters(sig),
            'is_static': isinstance(method, staticmethod),
            'is_classmethod': isinstance(method, classmethod)
        }

    def _extract_property_documentation(self, name: str, prop: property) -> Dict[str, Any]:
        """Extract documentation for a property."""
        return {
            'name': name,
            'docstring': inspect.getdoc(prop.fget) or "",
            'has_setter': prop.fset is not None,
            'has_deleter': prop.fdel is not None
        }

    def _extract_attribute_documentation(self, name: str, value: Any) -> Dict[str, Any]:
        """Extract documentation for an attribute."""
        return {
            'name': name,
            'type': type(value).__name__,
            'value': str(value) if len(str(value)) < 100 else f"{str(value)[:100]}...",
            'docstring': ""
        }

    def _extract_constant_documentation(self, name: str, value: Any) -> Dict[str, Any]:
        """Extract documentation for a constant."""
        return {
            'name': name,
            'type': type(value).__name__,
            'value': str(value) if len(str(value)) < 100 else f"{str(value)[:100]}...",
            'docstring': ""
        }

    def _extract_engine_documentation(self, engine_info) -> Dict[str, Any]:
        """Extract documentation for an engine."""
        metadata = engine_info.metadata

        return {
            'name': metadata.name,
            'version': metadata.version,
            'description': metadata.description,
            'author': metadata.author,
            'analysis_type': metadata.analysis_type.value,
            'capabilities': [cap.value for cap in metadata.capabilities],
            'input_schema': metadata.input_schema,
            'output_schema': metadata.output_schema,
            'dependencies': metadata.dependencies,
            'documentation_url': metadata.documentation_url,
            'module_path': engine_info.module_path
        }

    def _extract_parameters(self, signature: inspect.Signature) -> List[Dict[str, Any]]:
        """Extract parameter information from function signature."""
        parameters = []

        for param_name, param in signature.parameters.items():
            param_info = {
                'name': param_name,
                'annotation': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                'default': str(param.default) if param.default != inspect.Parameter.empty else None,
                'kind': str(param.kind)
            }
            parameters.append(param_info)

        return parameters

    def _get_return_type_annotation(self, func: Callable) -> str:
        """Get return type annotation for a function."""
        try:
            sig = inspect.signature(func)
            return_annotation = sig.return_annotation
            return str(return_annotation) if return_annotation != inspect.Signature.empty else 'Any'
        except (ValueError, TypeError):
            return 'Any'

    def _generate_format_documentation(self, api_docs: APIDocumentation, output_dir: Path, format_type: str) -> None:
        """Generate documentation in specified format."""
        if format_type == 'markdown':
            self._generate_markdown_documentation(api_docs, output_dir)
        elif format_type == 'html' and self.jinja_env:
            self._generate_html_documentation(api_docs, output_dir)
        elif format_type == 'json':
            self._generate_json_documentation(api_docs, output_dir)
        else:
            print(f"Warning: Unsupported format {format_type}")

    def _generate_markdown_documentation(self, api_docs: APIDocumentation, output_dir: Path) -> None:
        """Generate Markdown documentation."""
        output_file = output_dir / f"{api_docs.module_name.replace('.', '_')}_api.md"

        content = f"""# {self.metadata.title} - {api_docs.module_name}

**Version:** {self.metadata.version}
**Generated:** {self.metadata.generated_date}
**Author:** {self.metadata.author}

{self.metadata.description}

## Classes

"""

        for class_doc in api_docs.classes:
            content += f"""### {class_doc['name']}

{class_doc['docstring']}

**Inheritance:** {' → '.join(class_doc['inheritance'])}

#### Methods

"""

            for method in class_doc['methods']:
                content += f"""##### `{method['name']}{method['signature']}`

{method['docstring']}

"""

        content += "\n## Functions\n\n"

        for func_doc in api_docs.functions:
            content += f"""### `{func_doc['name']}{func_doc['signature']}`

{func_doc['docstring']}

"""

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(content)

    def _generate_html_documentation(self, api_docs: APIDocumentation, output_dir: Path) -> None:
        """Generate HTML documentation using Jinja2 templates."""
        if not self.jinja_env:
            print("Warning: Jinja2 not available, skipping HTML generation")
            return

        try:
            template = self.jinja_env.get_template('api_template.html')
            output_file = output_dir / f"{api_docs.module_name.replace('.', '_')}_api.html"

            html_content = template.render(
                metadata=self.metadata,
                api_docs=api_docs,
                generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(html_content)

        except Exception as e:
            print(f"Error generating HTML documentation: {e}")

    def _generate_json_documentation(self, api_docs: APIDocumentation, output_dir: Path) -> None:
        """Generate JSON documentation."""
        output_file = output_dir / f"{api_docs.module_name.replace('.', '_')}_api.json"

        # Convert to JSON-serializable format
        json_data = {
            'metadata': {
                'title': self.metadata.title,
                'version': self.metadata.version,
                'description': self.metadata.description,
                'author': self.metadata.author,
                'generated_date': self.metadata.generated_date,
                'framework_version': self.metadata.framework_version
            },
            'module': api_docs.module_name,
            'classes': api_docs.classes,
            'functions': api_docs.functions,
            'constants': api_docs.constants,
            'examples': api_docs.examples,
            'cross_references': api_docs.cross_references
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)

    def _generate_engine_format_documentation(self, engine_docs: List[Dict[str, Any]], output_dir: Path, format_type: str) -> None:
        """Generate engine documentation in specified format."""
        if format_type == 'markdown':
            self._generate_engine_markdown_documentation(engine_docs, output_dir)
        elif format_type == 'html' and self.jinja_env:
            self._generate_engine_html_documentation(engine_docs, output_dir)
        elif format_type == 'json':
            self._generate_engine_json_documentation(engine_docs, output_dir)

    def _generate_engine_markdown_documentation(self, engine_docs: List[Dict[str, Any]], output_dir: Path) -> None:
        """Generate Markdown engine documentation."""
        output_file = output_dir / "engines_reference.md"

        content = f"""# Engine Reference

**Version:** {self.metadata.version}
**Generated:** {self.metadata.generated_date}

This document provides reference information for all registered analysis engines in the V4 framework.

## Available Engines

"""

        for engine_doc in engine_docs:
            content += f"""### {engine_doc['name']} v{engine_doc['version']}

**Author:** {engine_doc['author']}
**Analysis Type:** {engine_doc['analysis_type']}
**Description:** {engine_doc['description']}

**Capabilities:**
"""

            for capability in engine_doc['capabilities']:
                content += f"- {capability}\n"

            if engine_doc['dependencies']:
                content += "\n**Dependencies:**\n"
                for dep in engine_doc['dependencies']:
                    content += f"- {dep}\n"

            content += "\n---\n\n"

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(content)

    def _generate_engine_html_documentation(self, engine_docs: List[Dict[str, Any]], output_dir: Path) -> None:
        """Generate HTML engine documentation."""
        if not self.jinja_env:
            return

        try:
            template = self.jinja_env.get_template('engines_template.html')
            output_file = output_dir / "engines_reference.html"

            html_content = template.render(
                metadata=self.metadata,
                engines=engine_docs,
                generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(html_content)

        except Exception as e:
            print(f"Error generating HTML engine documentation: {e}")

    def _generate_engine_json_documentation(self, engine_docs: List[Dict[str, Any]], output_dir: Path) -> None:
        """Generate JSON engine documentation."""
        output_file = output_dir / "engines_reference.json"

        json_data = {
            'metadata': {
                'title': self.metadata.title,
                'version': self.metadata.version,
                'generated_date': self.metadata.generated_date
            },
            'engines': engine_docs
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)

    def _generate_config_format_documentation(self, config_docs: Dict[str, Any], output_dir: Path, format_type: str) -> None:
        """Generate configuration documentation in specified format."""
        if format_type == 'markdown':
            self._generate_config_markdown_documentation(config_docs, output_dir)
        elif format_type == 'html' and self.jinja_env:
            self._generate_config_html_documentation(config_docs, output_dir)
        elif format_type == 'json':
            self._generate_config_json_documentation(config_docs, output_dir)

    def _generate_config_markdown_documentation(self, config_docs: Dict[str, Any], output_dir: Path) -> None:
        """Generate Markdown configuration documentation."""
        output_file = output_dir / "configuration_reference.md"

        content = f"""# Configuration Reference

**Version:** {self.metadata.version}
**Generated:** {self.metadata.generated_date}

This document provides reference information for V4 framework configuration schemas.

## Main Configuration (V4Config)

{config_docs['main_config'].get('docstring', 'Main configuration class for V4 framework')}

## Engine Configuration (EngineConfig)

{config_docs['engine_config'].get('docstring', 'Engine-specific configuration')}

## Async Configuration (AsyncConfig)

{config_docs['async_config'].get('docstring', 'Asynchronous execution configuration')}

## Performance Configuration (PerformanceConfig)

{config_docs['performance_config'].get('docstring', 'Performance monitoring configuration')}

"""

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(content)

    def _generate_config_html_documentation(self, config_docs: Dict[str, Any], output_dir: Path) -> None:
        """Generate HTML configuration documentation."""
        if not self.jinja_env:
            return

        try:
            template = self.jinja_env.get_template('config_template.html')
            output_file = output_dir / "configuration_reference.html"

            html_content = template.render(
                metadata=self.metadata,
                config_docs=config_docs,
                generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(html_content)

        except Exception as e:
            print(f"Error generating HTML config documentation: {e}")

    def _generate_config_json_documentation(self, config_docs: Dict[str, Any], output_dir: Path) -> None:
        """Generate JSON configuration documentation."""
        output_file = output_dir / "configuration_reference.json"

        json_data = {
            'metadata': {
                'title': self.metadata.title,
                'version': self.metadata.version,
                'generated_date': self.metadata.generated_date
            },
            'configurations': config_docs
        }

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)

    def generate_usage_examples(self, output_dir: Path) -> None:
        """Generate usage examples and tutorials."""
        examples = self._create_usage_examples()

        # Ensure output_formats is a concrete iterable and always include markdown
        formats = []
        try:
            formats = list(self.metadata.output_formats) if self.metadata.output_formats else []
        except Exception:
            formats = ['markdown']

        if 'markdown' not in formats:
            formats.insert(0, 'markdown')

        for format_type in formats:
            self._generate_examples_format_documentation(examples, output_dir, format_type)

    def _create_usage_examples(self) -> Dict[str, str]:
        """Create usage examples for the framework."""
        return {
            'basic_usage': '''
# Basic V4 Framework Usage

```python
from analysis.core.config import load_v4_config
from analysis.core.io import load_analysis_inputs
from analysis.engines.registry import get_registry

# Load configuration
config = load_v4_config()

# Load PSA data
psa_data = load_analysis_inputs(
    psa_path="data/psa.csv",
    config_path="config/strategies.yml",
    perspective="health_system"
)

# Get available engines
registry = get_registry()
engines = registry.list_engines()

print(f"Available engines: {engines}")
```''',

            'engine_usage': '''
# Using Analysis Engines

```python
from analysis.engines.base import EngineInput, EngineOutput
from analysis.engines.registry import get_registry

# Get engine registry
registry = get_registry()

# Get a specific engine
engine_class = registry.get_engine_class("CUAEngine")
if engine_class:
    # Create engine instance
    engine = engine_class(config={"wtp_range": [0, 100000]})

    # Initialize engine
    engine.initialize()

    # Prepare input data
    input_data = EngineInput(
        data=psa_data,
        config={"perspective": "health_system"},
        metadata={"analysis_type": "cost_utility"}
    )

    # Run analysis
    output = engine.run(input_data)

    # Access results
    results = output.results
    execution_time = output.execution_time
    warnings = output.warnings
```''',

            'async_usage': '''
# Asynchronous Engine Execution

```python
import asyncio
from analysis.engines.async_engine import create_async_wrapper, AsyncExecutionConfig

# Create async wrapper
async_config = AsyncExecutionConfig(
    max_workers=4,
    timeout=30.0,
    enable_progress_tracking=True
)

async_wrapper = create_async_wrapper(engine, async_config)

# Run asynchronously
async def run_analysis():
    input_data = EngineInput(data=psa_data, config={})
    result = await async_wrapper.run_async(input_data)
    return result

# Execute
analysis_result = asyncio.run(run_analysis())
```'''
        }

    def _generate_examples_format_documentation(self, examples: Dict[str, str], output_dir: Path, format_type: str) -> None:
        """Generate examples documentation in specified format."""
        if format_type == 'markdown':
            self._generate_examples_markdown_documentation(examples, output_dir)
        elif format_type == 'html' and self.jinja_env:
            self._generate_examples_html_documentation(examples, output_dir)

    def _generate_examples_markdown_documentation(self, examples: Dict[str, str], output_dir: Path) -> None:
        """Generate Markdown examples documentation."""
        output_file = output_dir / "usage_examples.md"

        content = f"""# Usage Examples

**Version:** {self.metadata.version}
**Generated:** {self.metadata.generated_date}

This document provides practical examples for using the V4 Health Economic Framework.

"""

        for example_name, example_content in examples.items():
            content += f"## {example_name.replace('_', ' ').title()}\n\n"
            content += f"{example_content}\n\n"

        # Write to file
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            f.write(content)

    def _generate_examples_html_documentation(self, examples: Dict[str, str], output_dir: Path) -> None:
        """Generate HTML examples documentation."""
        if not self.jinja_env:
            return

        try:
            template = self.jinja_env.get_template('examples_template.html')
            output_file = output_dir / "usage_examples.html"

            html_content = template.render(
                metadata=self.metadata,
                examples=examples,
                generated_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )

            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                f.write(html_content)

        except Exception as e:
            print(f"Error generating HTML examples documentation: {e}")

    def generate_complete_documentation(self, output_dir: Path) -> None:
        """
        Generate complete documentation set for the framework.

        Args:
            output_dir: Directory to save all documentation
        """
        print(f"Generating complete documentation in {output_dir}")

        # Generate API documentation for core modules
        core_modules = [
            'analysis.core.config',
            'analysis.core.io',
            'analysis.core.validation',
            'analysis.engines.base',
            'analysis.engines.registry',
            'analysis.engines.async_engine'
        ]

        for module_path in core_modules:
            print(f"Generating documentation for {module_path}")
            self.generate_module_documentation(module_path, output_dir / "api")

        # Generate engine documentation
        print("Generating engine documentation")
        self.generate_engine_documentation(output_dir / "engines")

        # Generate configuration documentation
        print("Generating configuration documentation")
        self.generate_configuration_documentation(output_dir / "config")

        # Generate usage examples
        print("Generating usage examples")
        self.generate_usage_examples(output_dir / "examples")

        # Generate index file
        self._generate_documentation_index(output_dir)

        print(f"Documentation generation complete: {output_dir}")

    def _generate_documentation_index(self, output_dir: Path) -> None:
        """Generate main documentation index."""
        index_file = output_dir / "index.md"

        content = f"""# V4 Health Economic Framework Documentation

**Version:** {self.metadata.version}
**Generated:** {self.metadata.generated_date}
**Author:** {self.metadata.author}

{self.metadata.description}

## Documentation Sections

### [API Reference](./api/)
Complete API reference for all framework modules and classes.

### [Engine Reference](./engines/)
Documentation for all available analysis engines and their capabilities.

### [Configuration Reference](./config/)
Configuration schema documentation and examples.

### [Usage Examples](./examples/)
Practical examples and tutorials for using the framework.

## Quick Start

1. **Configure the framework** using `config/v4_analysis_defaults.yml`
2. **Load your data** using `analysis.core.io.load_analysis_inputs()`
3. **Choose an engine** from the registry based on your analysis needs
4. **Run your analysis** using the engine's standardized interface
5. **Export results** in your preferred format

## Key Features

- **Modular Engine System**: Pluggable analysis engines with standardized interfaces
- **Comprehensive Validation**: Built-in data validation and integrity checking
- **Performance Monitoring**: Real-time performance tracking and optimization
- **Publication Standards**: Built-in support for journal publication requirements
- **Multi-jurisdiction Support**: Australian and New Zealand healthcare contexts
- **Provenance Tracking**: Complete data lineage and reproducibility support

## Support

For more information, see the individual documentation sections or contact the development team.
"""

        with open(index_file, 'w') as f:
            f.write(content)


# Convenience functions for documentation generation
def generate_api_docs(module_path: str, output_dir: str = "docs/api") -> None:
    """
    Generate API documentation for a module.

    Args:
        module_path: Import path to the module
        output_dir: Output directory for documentation
    """
    generator = DocumentationGenerator()
    generator.generate_module_documentation(module_path, Path(output_dir))


def generate_engine_docs(output_dir: str = "docs/engines") -> None:
    """
    Generate documentation for all registered engines.

    Args:
        output_dir: Output directory for documentation
    """
    generator = DocumentationGenerator()
    generator.generate_engine_documentation(Path(output_dir))


def generate_config_docs(output_dir: str = "docs/config") -> None:
    """
    Generate configuration documentation.

    Args:
        output_dir: Output directory for documentation
    """
    generator = DocumentationGenerator()
    generator.generate_configuration_documentation(Path(output_dir))


def generate_all_docs(output_dir: str = "docs") -> None:
    """
    Generate complete documentation set.

    Args:
        output_dir: Output directory for all documentation
    """
    generator = DocumentationGenerator()
    generator.generate_complete_documentation(Path(output_dir))
