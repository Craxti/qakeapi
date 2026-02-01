FROM python:3.11-slim

WORKDIR /app

# Copy package files
COPY setup.py .
COPY qakeapi/ qakeapi/

# Install qakeapi and server
RUN pip install --no-cache-dir -e . "uvicorn[standard]>=0.23.0"

# Copy examples
COPY examples/ examples/

# Expose port
EXPOSE 8000

# Default: run basic example
CMD ["uvicorn", "examples.basic_example:app", "--host", "0.0.0.0", "--port", "8000"]
