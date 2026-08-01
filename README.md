# knx2mqtt - a KNX-to-MQTT bridge supporting bidirectional telegram transfer

## Build and Run as a Container

### Build Container Image
To run the app in a container, you need to have a running Docker installation.
You can either build the container manually or use the provided `docker-compose` file.  

Using plain docker:
```bash
(...)
cd knx2mqtt
docker build -t knx2mqtt .
```

Using docker-compose, the image build process is covered automatically. 
If you want to trigger the build manually, run:
```bash
(...)
cd knx2mqtt
docker-compose build
```

### Run Container
You can either run the container manually or use the provided `docker-compose` file.  

The configuration file `knx2mqtt.yaml` must be mounted into the container at `/config/knx2mqtt.yaml`, otherwise the container won't start (see also the *Configuration* section below).

Using plain docker:
```bash
docker run --rm --name knx2mqtt -v $PWD/knx2mqtt.yaml:/config/knx2mqtt.yaml knx2mqtt
```

Using docker-compose adjust your settings in `docker-compose.yaml` first. Then run:
```bash
cd knx2mqtt
docker-compose up -d
```


## Configuration
- **app configuration**: The full configuration is defined in only one single configuration file: `knx2mqtt.yaml`. It contains the configuration for KNX and MQTT.
- **log configuration**: python logging configuration for the application is defined in `logging.conf`.

In the container, both files must be present under `/config`. This enables you to mount the path to a host directory holding your persistent configuration files. Mount as read-only is supported.


## App Confuguration Items
### MQTT
Configuration of the MQTT broker connection:
```yaml
mqtt:
  client_id: knx2mqtt
  host: your.mqtt-server.name
  port: 1883
  user: knx2mqtt
  password: topsecret
  topic: "home/bus/knx"
  qos: 0
  retain: true
  keepalive: 60
```

Usually, you only need to change the `host`, `user` and `password` as well as the MQTT `topic`.
Other values can be left to their defaults.


### KNX
Configuration of the KNX IP gateway connection:
```yaml
knx:
  general:
    #address_format: long
    #rate_limit: 200
    #multicast_group: '224.0.23.12'
    #multicast_port: 3671
  connection:
    #routing:
      #local_ip: 192.168.0.12
    tunneling:
      individual_address: '15.15.249'
      gateway_ip: '192.168.0.11'
      gateway_port: 3671
      local_ip: '192.168.0.12'
      local_port: 12399
      route_back: true
```
Since the knx2mqtt bridge runs as a container, `route_back` must be set to `true` or the  network mode `host` has to be used for the container. The port `12399/udp` will be exposed by the container by default.

As of today, the bridge supports `sensors` and `switches` as native entities:
```yaml
knx:
  sensors: []
  switches: []
```

Each entity requires the corresponding group address to be set as `address`, and the related KNX DPT type as `type`.

The default operating mode for configured objects is to listen on the KNX and publish the telegram values to MQTT. This can be changed by setting `expose` or `subscribe` to `true`:
- if `expose` is set to `true`, values published on MQTT will be sent as telegram to KNX. Values from KNX are never published to MQTT.
  ```yaml
  knx:
    sensors:
      - address: 0/0/1
        type: DPTDate
        expose: true
  ```
- if `subscribe` is set to `true`, the bridge operates in *bidirectional* mode. Values from KNX are published to MQTT and vice versa.
  ```yaml
  knx:
    switches:
      - address: 0/1/1
        type: DPTBinary
        subscribe: true
  ```

## Container Evironment Variables for Configurationcontainer
  
You can also use the following environment variables for the container:  
- `LOGDIR` path to log files.  
- `LOGCONFIG_FILE` path to configuration file for logging options (use `/config/logging.production.conf` for producation and `/config/logging.conf` for debugging).  
- `CONFIG_FILE` path to main knx2mqqt configuration file.  
- `KNX_LOCAL_PORT` default local UDP port used by knx2mqtt for KNX gateway communication.  

The default values are defined in the file `Dockerfile`.
