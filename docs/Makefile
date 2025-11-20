# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

# Custom targets for QakeAPI documentation

# Install dependencies
install:
	pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

# Clean build directory
clean:
	rm -rf $(BUILDDIR)
	rm -rf ../qakeapi.egg-info

# Build HTML documentation
html: clean
	$(SPHINXBUILD) -b html $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html
	@echo
	@echo "Build finished. The HTML pages are in $(BUILDDIR)/html."

# Build PDF documentation
pdf: clean
	$(SPHINXBUILD) -b latex $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/latex
	@echo "Running LaTeX files through pdflatex..."
	$(MAKE) -C $(BUILDDIR)/latex all-pdf
	@echo "pdflatex finished; the PDF files are in $(BUILDDIR)/latex."

# Build EPUB documentation
epub: clean
	$(SPHINXBUILD) -b epub $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/epub
	@echo
	@echo "Build finished. The epub file is in $(BUILDDIR)/epub."

# Serve documentation locally
serve: html
	cd $(BUILDDIR)/html && python -m http.server 8080
	@echo "Documentation served at http://localhost:8080"

# Auto-generate API documentation
autodoc:
	sphinx-apidoc -o . ../qakeapi --force --module-first --separate

# Build all formats
all: html pdf epub
	@echo "All documentation formats built successfully!"

# Check for broken links
linkcheck:
	$(SPHINXBUILD) -b linkcheck $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/linkcheck
	@echo
	@echo "Link check finished; look for any errors in the above output " \
	      "or in $(BUILDDIR)/linkcheck/output.txt."

# Spell check
spelling:
	$(SPHINXBUILD) -b spelling $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/spelling
	@echo
	@echo "Spell check finished; look for any errors in the above output " \
	      "or in $(BUILDDIR)/spelling/output.txt."

# Coverage report
coverage:
	$(SPHINXBUILD) -b coverage $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/coverage
	@echo "Coverage finished; the report is in $(BUILDDIR)/coverage."

# Development server with auto-reload
dev: html
	@echo "Starting development server with auto-reload..."
	@echo "Press Ctrl+C to stop"
	cd $(BUILDDIR)/html && python -m http.server 8080 &
	@while true; do \
		sleep 2; \
		$(SPHINXBUILD) -b html $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html > /dev/null 2>&1; \
	done

# Deploy to GitHub Pages
deploy: html
	@echo "Deploying to GitHub Pages..."
	cd $(BUILDDIR)/html && \
	git init && \
	git add . && \
	git commit -m "Deploy documentation" && \
	git push -f git@github.com:Craxti/qakeapi.git main:gh-pages

# Generate sitemap
sitemap: html
	@echo "Generating sitemap..."
	cd $(BUILDDIR)/html && \
	find . -name "*.html" | sed 's|^\./||' | sed 's|\.html$||' > sitemap.txt

# Build with custom theme
custom-theme: clean
	$(SPHINXBUILD) -b html -D html_theme=alabaster $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html
	@echo "Build finished with custom theme."

# Quick build for development
quick: clean
	$(SPHINXBUILD) -b html -D html_theme=sphinx_rtd_theme $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html
	@echo "Quick build finished."

# Build with warnings as errors
strict: clean
	$(SPHINXBUILD) -b html -W $(SPHINXOPTS) $(SOURCEDIR) $(BUILDDIR)/html
	@echo "Strict build finished."

# Generate requirements for documentation
requirements:
	@echo "sphinx>=4.0.0" > requirements-docs.txt
	@echo "sphinx-rtd-theme>=1.0.0" >> requirements-docs.txt
	@echo "sphinx-autodoc-typehints>=1.12.0" >> requirements-docs.txt
	@echo "Requirements file generated: requirements-docs.txt"

# Install documentation requirements
install-docs: requirements
	pip install -r requirements-docs.txt

# Full documentation build process
full: install-docs autodoc html linkcheck spelling
	@echo "Full documentation build completed!"
	@echo "HTML: $(BUILDDIR)/html/index.html"
	@echo "Link check: $(BUILDDIR)/linkcheck/output.txt"
	@echo "Spelling: $(BUILDDIR)/spelling/output.txt" 