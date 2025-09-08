# Base image
FROM --platform=linux/amd64 python:3.9-slim

# Set working directory
WORKDIR /app

# Copy all files
COPY . .

# Install dependencies
RUN pip install --no-cache-dir \
    PyMuPDF \
    sentence-transformers \
    scikit-learn

# Default command
CMD ["python", "main.py"]
