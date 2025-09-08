# Use the specified Python base image, ensuring compatibility with linux/amd64 architecture.
FROM --platform=linux/amd64 python:3.10-slim

# Set the working directory inside the container. All subsequent commands will run from here.
WORKDIR /app

# Copy the requirements file first to leverage Docker's layer caching.
# The dependencies will only be re-installed if this file changes.
COPY requirements.txt .

# Install the Python dependencies specified in requirements.txt.
# --no-cache-dir reduces the image size.
RUN pip install --no-cache-dir -r requirements.txt

# Copy your main processing script into the container.
COPY process_pdfs.py .

# Set the default command to execute when the container starts.
# This will run your Python script to process the PDFs.
CMD ["python", "process_pdfs.py"]
