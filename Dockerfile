# ---- Simplified Airflow Dockerfile ----
# This version installs dependencies directly into the main environment,
# which is the recommended pattern for the official Airflow image.
FROM apache/airflow:3.0.2

# Copy and install requirements
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

# Copy the application source code
COPY src/ /opt/airflow/src/

# Set the PYTHONPATH, preserving the ability to pass a default value
ARG DEFAULT_PYTHONPATH=""
ENV PYTHONPATH="${DEFAULT_PYTHONPATH}"
ENV PYTHONPATH="/opt/airflow/src/:${PYTHONPATH}"
