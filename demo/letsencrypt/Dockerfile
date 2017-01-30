FROM alpine

# Install curl
RUN apk add --update curl && \
    rm -rf /var/cache/apk/*
    
# Configure cron
COPY reissue.sh /generate-certificate.sh
RUN ln -s /generate-certificate.sh /etc/periodic/monthly/reissue && \
    chmod a+x /etc/periodic/monthly/reissue

# Install the docker client
ARG DOCKER_VERSION
ADD https://get.docker.com/builds/Linux/x86_64/docker-$DOCKER_VERSION.tgz /tmp
RUN cd /tmp && \
    tar -xzf /tmp/docker-$DOCKER_VERSION.tgz && \
    cp /tmp/docker/docker /usr/local/bin/docker

COPY run.sh /run.sh
RUN chmod 777 /run.sh
WORKDIR /
CMD ["/run.sh"]
