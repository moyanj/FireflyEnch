# Use Python slim image to reduce size
FROM python:3.14.5-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install uv
RUN pip install --no-cache-dir uv

# Set the working directory
WORKDIR /moyan

# Copy only the requirements file initially
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy the rest of the application
COPY . .

# Copy frontend assets
COPY frontend/dist ./files

# Create a non-root user for running the application
RUN adduser --system --group moyan \
    && chown -R moyan:moyan /moyan

# Switch to the non-root user
USER moyan

# Expose the port that the app runs on
EXPOSE 8896

# Command to run the application
CMD ["uv", "run", "app.py"]
