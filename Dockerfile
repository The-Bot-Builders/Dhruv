# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.11-slim

# Open Port
EXPOSE 3000

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Make this prod
ENV STAGE=prod

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
COPY overrides/pgvector.py /usr/local/lib/python3.11/site-packages/langchain/vectorstores/pgvector.py

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "app.py"]
