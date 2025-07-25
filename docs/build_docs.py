#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QakeAPI Documentation Builder

This script automates the documentation building process for QakeAPI.
It can generate HTML, PDF, and EPUB documentation with various options.
"""

import os
import sys
import subprocess
import argparse
import shutil
from pathlib import Path

class DocumentationBuilder:
    def __init__(self, docs_dir="docs"):
        self.docs_dir = Path(docs_dir)
        self.build_dir = self.docs_dir / "_build"
        self.source_dir = self.docs_dir
        
    def run_command(self, command, cwd=None):
        """Run a command and return success status."""
        try:
            result = subprocess.run(
                command,
                cwd=cwd or str(self.docs_dir),
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ {command[0]} completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ {command[0]} failed:")
            print(f"STDOUT: {e.stdout}")
            print(f"STDERR: {e.stderr}")
            return False
    
    def install_dependencies(self):
        """Install required documentation dependencies."""
        print("📦 Installing documentation dependencies...")
        
        dependencies = [
            "sphinx>=4.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "sphinx-autodoc-typehints>=1.12.0",
            "sphinxcontrib-spelling>=7.0.0",
            "sphinxcontrib-httpdomain>=1.8.0"
        ]
        
        for dep in dependencies:
            if not self.run_command([sys.executable, "-m", "pip", "install", dep]):
                return False
        
        return True
    
    def clean_build(self):
        """Clean the build directory."""
        print("🧹 Cleaning build directory...")
        
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        
        return True
    
    def generate_api_docs(self):
        """Generate API documentation from source code."""
        print("📚 Generating API documentation...")
        
        qakeapi_dir = self.docs_dir.parent / "qakeapi"
        if not qakeapi_dir.exists():
            print(f"❌ QakeAPI source directory not found: {qakeapi_dir}")
            return False
        
        return self.run_command([
            "sphinx-apidoc",
            "-o", str(self.source_dir),
            str(qakeapi_dir),
            "--force",
            "--module-first",
            "--separate"
        ])
    
    def build_html(self, theme="sphinx_rtd_theme"):
        """Build HTML documentation."""
        print(f"🌐 Building HTML documentation with theme: {theme}")
        
        return self.run_command([
            "sphinx-build",
            "-b", "html",
            "-D", f"html_theme={theme}",
            str(self.source_dir),
            str(self.build_dir / "html")
        ])
    
    def build_pdf(self):
        """Build PDF documentation."""
        print("📄 Building PDF documentation...")
        
        # Build LaTeX first
        if not self.run_command([
            "sphinx-build",
            "-b", "latex",
            str(self.source_dir),
            str(self.build_dir / "latex")
        ]):
            return False
        
        # Build PDF from LaTeX
        latex_dir = self.build_dir / "latex"
        if not self.run_command(["make", "all-pdf"], cwd=str(latex_dir)):
            return False
        
        return True
    
    def build_epub(self):
        """Build EPUB documentation."""
        print("📖 Building EPUB documentation...")
        
        return self.run_command([
            "sphinx-build",
            "-b", "epub",
            str(self.source_dir),
            str(self.build_dir / "epub")
        ])
    
    def check_links(self):
        """Check for broken links."""
        print("🔗 Checking for broken links...")
        
        return self.run_command([
            "sphinx-build",
            "-b", "linkcheck",
            str(self.source_dir),
            str(self.build_dir / "linkcheck")
        ])
    
    def check_spelling(self):
        """Check spelling in documentation."""
        print("📝 Checking spelling...")
        
        return self.run_command([
            "sphinx-build",
            "-b", "spelling",
            str(self.source_dir),
            str(self.build_dir / "spelling")
        ])
    
    def serve_docs(self, port=8080):
        """Serve documentation locally."""
        print(f"🚀 Serving documentation at http://localhost:{port}")
        
        html_dir = self.build_dir / "html"
        if not html_dir.exists():
            print("❌ HTML documentation not built. Run 'build html' first.")
            return False
        
        try:
            subprocess.run([
                sys.executable, "-m", "http.server", str(port)
            ], cwd=str(html_dir))
        except KeyboardInterrupt:
            print("\n🛑 Server stopped.")
        
        return True
    
    def deploy_to_github_pages(self):
        """Deploy documentation to GitHub Pages."""
        print("🚀 Deploying to GitHub Pages...")
        
        html_dir = self.build_dir / "html"
        if not html_dir.exists():
            print("❌ HTML documentation not built. Run 'build html' first.")
            return False
        
        # Initialize git repository in build directory
        if not self.run_command(["git", "init"], cwd=str(html_dir)):
            return False
        
        if not self.run_command(["git", "add", "."], cwd=str(html_dir)):
            return False
        
        if not self.run_command(["git", "commit", "-m", "Deploy documentation"], cwd=str(html_dir)):
            return False
        
        if not self.run_command([
            "git", "push", "-f", "git@github.com:Craxti/qakeapi.git", "main:gh-pages"
        ], cwd=str(html_dir)):
            return False
        
        return True
    
    def build_all(self, check_quality=True):
        """Build all documentation formats with quality checks."""
        print("🏗️ Building all documentation formats...")
        
        # Install dependencies
        if not self.install_dependencies():
            return False
        
        # Clean build directory
        if not self.clean_build():
            return False
        
        # Generate API docs
        if not self.generate_api_docs():
            return False
        
        # Build HTML
        if not self.build_html():
            return False
        
        # Build PDF
        if not self.build_pdf():
            print("⚠️ PDF build failed, continuing...")
        
        # Build EPUB
        if not self.build_epub():
            print("⚠️ EPUB build failed, continuing...")
        
        # Quality checks
        if check_quality:
            print("🔍 Running quality checks...")
            
            if not self.check_links():
                print("⚠️ Link check found issues")
            
            if not self.check_spelling():
                print("⚠️ Spelling check found issues")
        
        print("✅ Documentation build completed!")
        print(f"📁 Build directory: {self.build_dir}")
        print(f"🌐 HTML: {self.build_dir / 'html' / 'index.html'}")
        print(f"📄 PDF: {self.build_dir / 'latex' / 'qakeapi.pdf'}")
        print(f"📖 EPUB: {self.build_dir / 'epub' / 'qakeapi.epub'}")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="QakeAPI Documentation Builder")
    parser.add_argument("command", choices=[
        "install", "clean", "api", "html", "pdf", "epub", 
        "links", "spelling", "serve", "deploy", "all"
    ], help="Command to execute")
    
    parser.add_argument("--theme", default="sphinx_rtd_theme", 
                       help="HTML theme to use")
    parser.add_argument("--port", type=int, default=8080,
                       help="Port for serving documentation")
    parser.add_argument("--no-quality", action="store_true",
                       help="Skip quality checks for 'all' command")
    parser.add_argument("--docs-dir", default="docs",
                       help="Documentation source directory")
    
    args = parser.parse_args()
    
    builder = DocumentationBuilder(args.docs_dir)
    
    if args.command == "install":
        success = builder.install_dependencies()
    elif args.command == "clean":
        success = builder.clean_build()
    elif args.command == "api":
        success = builder.generate_api_docs()
    elif args.command == "html":
        success = builder.build_html(args.theme)
    elif args.command == "pdf":
        success = builder.build_pdf()
    elif args.command == "epub":
        success = builder.build_epub()
    elif args.command == "links":
        success = builder.check_links()
    elif args.command == "spelling":
        success = builder.check_spelling()
    elif args.command == "serve":
        success = builder.serve_docs(args.port)
    elif args.command == "deploy":
        success = builder.deploy_to_github_pages()
    elif args.command == "all":
        success = builder.build_all(not args.no_quality)
    else:
        print(f"❌ Unknown command: {args.command}")
        return 1
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 