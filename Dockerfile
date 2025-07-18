# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the requirements file into the container at /usr/src/app
COPY pyproject.toml .

# Install any needed packages specified in pyproject.toml
RUN pip install .

# Copy the rest of the application's code from the host to the container
COPY . .

# Command to run the server
CMD ["python", "-m", "mcp_obsidian_advanced.server"]