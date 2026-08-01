FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir pytest
ENV PYTHONPATH=/app
CMD ["python3", "main.py"]
# Health: python3 -c "from emailagent import *; print('ok')"
