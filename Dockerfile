FROM python:3-alpine

# User Configuration
ENV LOGDIR="/var/log/knx2mqtt"
ENV LOGCONFIG_FILE="/config/logging.production.conf"
ENV CONFIG_FILE="/config/knx2mqtt.yaml"
ENV KNX_LOCAL_PORT="12399"

COPY ./knx2mqtt /app
COPY ./config /config
WORKDIR /app

RUN apk add --no-cache gcc musl-dev libffi-dev linux-headers \
    && pip install -r /app/requirements.txt \
    && apk del --purge gcc musl-dev libffi-dev linux-headers \
    && rm -rf /var/cache/apk/* \
    # Logging
    && mkdir -p ${LOGDIR}

# Remove default config file -> require mount
RUN rm /config/knx2mqtt.yaml

VOLUME ["/config"]
EXPOSE ${KNX_LOCAL_PORT}/udp
CMD ["/bin/sh", "-c", "python3 /app/knx2mqtt.py -c $CONFIG_FILE -l $LOGCONFIG_FILE"]
