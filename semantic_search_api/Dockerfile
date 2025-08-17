# ---- Builder Stage ----
FROM python:3.12-slim AS builder

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt


# ---- Final Stage ----
FROM python:3.12-slim

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy the application source code
COPY . .

# Grant ownership to the new user
RUN chown -R appuser:appuser /app /home/appuser

# Add packages to PATH
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to the non-root user
USER appuser

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]