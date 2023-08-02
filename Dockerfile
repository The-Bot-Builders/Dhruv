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
RUN python -m pip install torch==2.0.1+cpu -f https://download.pytorch.org/whl/torch_stable.html
RUN python -m pip install torchvision==0.15.2+cpu -f https://download.pytorch.org/whl/torch_stable.html
COPY heavy_requirements.txt .
RUN python -m pip install -r heavy_requirements.txt

COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
CMD ["python", "app.py"]
