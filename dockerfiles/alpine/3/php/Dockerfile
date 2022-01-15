ARG VERSION=latest
FROM alpine:${VERSION}

RUN apk update && \
    apk add php8-fpm=8.0.14-r0 && \
    rm -rf /var/cache/apk/*