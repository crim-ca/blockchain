FROM python:3.6-alpine

WORKDIR /app

# Install dependencies.
ADD requirements.txt /app
RUN cd /app && \
    pip install -r requirements.txt

# Add actual source code.
ADD blockchain/ /app/blockchain

EXPOSE 5000

CMD ["python", "/app/blockchain/app.py", "--port", "5000"]
