# Meshtastic Link Planner 

If you just want to use the link planner, go to the hosted version: (pending)

## About

This is a web utility to predict the range of a Meshtastic radio (see meshtastic.org). It generates a map of where your meshtastic radio can be received based on your location and antenna. The prediction accounts for terrain and calculates the expected RSSI (received signal strength indication) using the ITM / Longely-Rice model. The model parameters have been carefully chosen based on experimental data and practical experience to produce results which are accuate for meshtastic devices. Radio parameters are based on the selected LoRa region. 

This project is not affiliated with meshtastic.

## Assumptions

This tool makes several assumptions:

* Devices receiving your radio are 1 meter above the ground and have an antenna gain of 1.0 dB.
* There are no signal losses caused by obstructions other than terrain. This commonly includes trees, buildings, and glass windows.
* Antennas are isotropic and vertically polarized.
* There are negligable signal losses caused by antennas connected to radios through coaxial cable.
* Radios are transmitting the maximum legal power permitted in their region.
* The sensitivity of the receiver in all cases is approximately -130 dBm.
* The terrain model is accurate to 30 meters.

These assumptions have been tested and found to be practical approximations of how meshtastic radios work. Please use discretion when applying results from this tool and verify the results if your project depends on them.


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
           --env max_distance_km=100 \
           --env tile_dir=/app/srtm_tiles \
           -v my_srtm_data:/app/srtm_tiles \
           -p 80:8080 linkplanner
```

Note: It is recommended to leave the `max_distance` at 100 kilometers and `h3_res` as 8 so that the computation is fast.

## References

* geoprop-py: https://github.com/JayKickliter/geoprop-py
* leafletjs: https://leafletjs.com
* ITM / Longely Rice model: https://its.ntia.gov/software/itm
* meshtastic: https://meshtastic.org
