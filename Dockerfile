FROM apache/airflow:3.0.2

COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt

# This line is correct as is, assuming your Dockerfile is in the 'your_project' directory
COPY src/ /opt/airflow/src/

# First, ensure PYTHONPATH is defined (even if empty)
ARG DEFAULT_PYTHONPATH=""
ENV PYTHONPATH="${DEFAULT_PYTHONPATH}"

# Then, prepend your custom path
ENV PYTHONPATH="/opt/airflow/src/:${PYTHONPATH}"