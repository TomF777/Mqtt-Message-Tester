FROM python:3.12-alpine

ARG TARGETARCH
ARG TARGETPLATFORM=alpine

RUN apk upgrade --no-cache && \
    apk add --no-cache \
    bash \
    nano \
    htop \
    curl

#Create non-root user
RUN addgroup -S localusers
RUN adduser -S -s /bin/ash localuser -G localusers

#Create catalog for the app and copy file there
RUN mkdir -p /src
WORKDIR /src

RUN chown -R localuser /src
USER localuser

COPY --chown=localuser:localusers . /src


RUN pip install --upgrade pip && \
    pip install -r requirements.txt
    
    
RUN rm requirements.txt

CMD ["python", "/src/message_tester.py"]
