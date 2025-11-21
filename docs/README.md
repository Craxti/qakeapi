# QakeAPI Documentation

This directory contains the documentation for QakeAPI, a modern ASGI web framework for Python.

## 📚 Documentation Structure

```
docs/
├── index.rst              # Main documentation page
├── quickstart.rst         # Quick start guide
├── installation.rst       # Installation instructions
├── cli.rst               # CLI tool documentation
├── api-reference.rst     # API reference
├── middleware.rst        # Middleware guide
├── security.rst          # Security best practices
├── validation.rst        # Validation guide
├── websockets.rst        # WebSocket guide
├── graphql.rst           # GraphQL guide
├── versioning.rst        # API versioning guide
├── events.rst            # Event-driven architecture
├── testing.rst           # Testing guide
├── deployment.rst        # Deployment guide
├── live_reload.rst       # Live reload development
├── conf.py              # Sphinx configuration
├── Makefile             # Build automation
├── build_docs.py        # Python build script
├── _static/             # Static files (CSS, JS, images)
│   └── custom.css       # Custom styles
└── _templates/          # Custom templates
```

## 🚀 Quick Start

### Using Makefile (Recommended)

```bash
# Install dependencies
make install

# Build HTML documentation
make html

# Serve documentation locally
make serve

# Build all formats (HTML, PDF, EPUB)
make all

# Check for broken links
make linkcheck

# Check spelling
make spelling
```

### Using Python Script

```bash
# Install dependencies
python build_docs.py install

# Build HTML documentation
python build_docs.py html

# Build all formats with quality checks
python build_docs.py all

# Serve documentation locally
python build_docs.py serve --port 8080

# Deploy to GitHub Pages
python build_docs.py deploy
```

### Using Sphinx Directly

```bash
# Install Sphinx and theme
pip install sphinx sphinx-rtd-theme

# Generate API documentation
sphinx-apidoc -o . ../qakeapi --force --module-first --separate

# Build HTML
sphinx-build -b html . _build/html

# Build PDF
sphinx-build -b latex . _build/latex
cd _build/latex && make all-pdf

# Build EPUB
sphinx-build -b epub . _build/epub
```

## 📖 Available Commands

### Makefile Commands

- `make help` - Show all available commands
- `make install` - Install documentation dependencies
- `make clean` - Clean build directory
- `make html` - Build HTML documentation
- `make pdf` - Build PDF documentation
- `make epub` - Build EPUB documentation
- `make all` - Build all formats
- `make serve` - Serve documentation locally
- `make linkcheck` - Check for broken links
- `make spelling` - Check spelling
- `make coverage` - Generate coverage report
- `make dev` - Development server with auto-reload
- `make deploy` - Deploy to GitHub Pages
- `make sitemap` - Generate sitemap
- `make quick` - Quick build for development
- `make strict` - Build with warnings as errors

### Python Script Commands

- `python build_docs.py install` - Install dependencies
- `python build_docs.py clean` - Clean build directory
- `python build_docs.py api` - Generate API documentation
- `python build_docs.py html` - Build HTML documentation
- `python build_docs.py pdf` - Build PDF documentation
- `python build_docs.py epub` - Build EPUB documentation
- `python build_docs.py links` - Check for broken links
- `python build_docs.py spelling` - Check spelling
- `python build_docs.py serve` - Serve documentation locally
- `python build_docs.py deploy` - Deploy to GitHub Pages
- `python build_docs.py all` - Build all formats with quality checks

## 🎨 Customization

### Themes

The documentation uses the Read the Docs theme by default. You can change it:

```bash
# Using Makefile
make custom-theme

# Using Python script
python build_docs.py html --theme alabaster
```

### Custom CSS

Custom styles are defined in `_static/custom.css`. The styles include:

- Modern color scheme
- Responsive design
- Dark mode support
- Custom components (badges, buttons, etc.)
- Print styles

### Configuration

The Sphinx configuration is in `conf.py`. Key settings:

- **Project**: QakeAPI
- **Version**: 1.1.2
- **Theme**: sphinx_rtd_theme
- **Extensions**: autodoc, napoleon, viewcode, intersphinx, etc.
- **Mock imports**: External dependencies that shouldn't be imported

## 🔧 Development

### Adding New Documentation

1. Create a new `.rst` file in the docs directory
2. Add it to the appropriate toctree in `index.rst`
3. Write the documentation using reStructuredText
4. Build and test: `make html && make serve`

### Code Examples

Use the `code-block` directive for syntax highlighting:

```rst
.. code-block:: python

   from qakeapi import Application
   
   app = Application()
   
   @app.get("/")
   async def hello():
       return {"message": "Hello, World!"}
```

### API Documentation

API documentation is automatically generated from docstrings. Use Google or NumPy style:

```python
def my_function(param1: str, param2: int) -> dict:
    """Short description.
    
    Longer description with details.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        Description of return value
        
    Raises:
        ValueError: When something goes wrong
    """
    pass
```

### Cross-references

Link to other documentation sections:

```rst
:ref:`quickstart`
:doc:`api-reference`
:mod:`qakeapi.core.application`
:func:`qakeapi.Application`
```

## 🌐 Deployment

### GitHub Pages

The documentation can be automatically deployed to GitHub Pages:

```bash
make deploy
```

This will:
1. Build the HTML documentation
2. Initialize a git repository in the build directory
3. Commit and push to the `gh-pages` branch

### Read the Docs

To deploy to Read the Docs:

1. Connect your GitHub repository to Read the Docs
2. Configure the documentation settings
3. Set the documentation type to "Sphinx"
4. Set the Python interpreter version
5. Build and deploy automatically

### Manual Deployment

For other hosting providers:

```bash
# Build HTML documentation
make html

# Upload the contents of _build/html/ to your web server
```

## 🧪 Testing

### Quality Checks

Run quality checks to ensure documentation quality:

```bash
# Check for broken links
make linkcheck

# Check spelling
make spelling

# Run all quality checks
python build_docs.py all
```

### Local Testing

Test the documentation locally:

```bash
# Build and serve
make html && make serve

# Or use the Python script
python build_docs.py html && python build_docs.py serve
```

## 📋 Requirements

### System Requirements

- Python 3.7+
- pip
- make (for Makefile commands)
- LaTeX (for PDF generation)

### Python Dependencies

- sphinx>=4.0.0
- sphinx-rtd-theme>=1.0.0
- sphinx-autodoc-typehints>=1.12.0
- sphinxcontrib-spelling>=7.0.0
- sphinxcontrib-httpdomain>=1.8.0

Install with:

```bash
pip install -r requirements-docs.txt
```

## 🤝 Contributing

### Documentation Guidelines

1. **Write clearly**: Use simple, clear language
2. **Include examples**: Provide working code examples
3. **Keep it updated**: Update documentation when code changes
4. **Test examples**: Ensure all code examples work
5. **Use proper formatting**: Follow reStructuredText conventions

### Adding Examples

When adding new examples:

1. Create the example in `examples_app/`
2. Add it to the documentation
3. Include a link to the live demo
4. Test the example works

### Reporting Issues

If you find issues with the documentation:

1. Check if it's a build issue or content issue
2. For build issues, check the error output
3. For content issues, suggest improvements
4. Create an issue with details

## 📞 Support

For documentation issues:

- Check the troubleshooting section
- Look at the build output for errors
- Search existing issues
- Create a new issue with details

For QakeAPI issues:

- Check the main README
- Look at the examples
- Create an issue in the main repository 