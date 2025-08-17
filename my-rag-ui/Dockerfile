# my-rag-ui/Dockerfile

# ---- Builder Stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Upgrade pip
RUN pip install --upgrade pip

# Copy and install requirements
COPY requirements.txt .
RUN pip install --user -r requirements.txt


# ---- Final Stage ----
FROM python:3.11-slim

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy the application file
COPY app.py .

# Grant ownership to the new user
RUN chown -R appuser:appuser /app /home/appuser

# Add packages to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to the non-root user
USER appuser

# Run the application
CMD ["python", "-u", "app.py"]