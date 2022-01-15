ARG VERSION
FROM alpine:${VERSION}

RUN  apk update && \
     apk add nodejs-current-17.3.1-r0 && \
     rm -rf /var/cache/apk/*