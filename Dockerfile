# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Install uv for package management
RUN pip install uv

# Copy dependency definition files
COPY pyproject.toml uv.lock ./

# Install dependencies from the lock file using uv
RUN uv pip sync uv.lock

# Copy the rest of the application's code from the host to the container
COPY . .

# Command to run the server
CMD ["python", "-m", "mcp_obsidian_advanced.server"]