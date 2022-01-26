FROM python:3.9-slim as BUILDER
LABEL description.short="User-Data Consents Management Blockchain"
LABEL description.long="User consents management using Blockchain technology to guarantee integrity and traceability of private data."
LABEL maintainer="Francis Charette-Migneault <francis.charette-migneault@crim.ca>"
LABEL vendor="CRIM"
LABEL version="0.11.2"

ADD requirements.txt /app/
ADD blockchain/ /app/blockchain
RUN apt-get update  \
    && apt-get install -y --no-install-recommends \
		ca-certificates \
		netbase \
		gcc \
    && python -m pip install --upgrade pip \
    && pip install --no-cache-dir --upgrade -r /app/requirements.txt \
    && rm -f /app/requirements.txt

FROM python:3.9-slim
COPY --from=BUILDER /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=BUILDER /app/blockchain /app/blockchain

ADD setup.py README.md /app/
RUN pip install --no-cache-dir -e /app \
    && rm /app/setup.py
WORKDIR /app
EXPOSE 5000
ENTRYPOINT ["python", "/app/blockchain/app.py"]
