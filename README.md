# Meshtastic Link Planner 

If you just want to use the link planner, go to the hosted version: 

## About

This is a web utility to predict the range of a Meshtastic radio (see meshtastic.org). It generates a map of where your meshtastic radio can be received based on your location and antenna. The prediction accounts for terrain and calculates the expected RSSI (received signal strength indication) using the ITM / Longely-Rice model. The model parameters have been carefully chosen based on experimental data and practical experience to produce results which are accuate for meshtastic devices. Radio parameters are based on the selected LoRa region. 

## Building

Requirements:

* 3 arcsecond resolution NASA SRTM elevation dataset in `.hgt` format, available from https://registry.opendata.aws/terrain-tiles/
* docker
* git

copy the `.hgt` files to a convenient folder, `my_srtm_data`.

```
git clone https://github.com/mrpatrick1991/meshtastic_linkplanner/ && cd meshtastic_linkplanner

docker build -t linkplanner .

docker run --env h3_res=8 \
           --env max_distance_km=150 \
           --env tile_dir=/app/srtm_tiles \
           -v my_srtm_data:/app/srtm_tiles \
           -p 80:8080 linkplanner
```

It is recommended to leave the `max_distance` at 150 kilometers and `h3_res` as 8 so that the computation is fast.

## References


