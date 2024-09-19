# Meshtastic Link Planner 

If you just want to use the link planner, go to the hosted version: https://meshplanner.mpatrick.dev

## About

This is a web utility to predict the range of a Meshtastic radio (see Meshtastic.org). It generates a map of where your Meshtastic radio can be received based on your location and antenna. The prediction accounts for terrain and calculates the expected RSSI (received signal strength indication) using the ITM / Longley-Rice model. The model parameters have been carefully chosen based on experimental data and practical experience to produce results which are accurate for Meshtastic devices. Radio parameters are based on the selected LoRa region. 

This project is not affiliated with Meshtastic.

## Assumptions

This tool makes several assumptions:

* Receivers are 1 meter above the ground and have an antenna gain of 1.0 dB.
* There are no signal losses caused by obstructions other than terrain. This commonly includes trees, buildings, and glass windows.
* Antennas are isotropic and vertically polarized.
* Negligible signal losses are caused by coaxial cable.
* Radios are transmitting the maximum legal power permitted in their region.
* The sensitivity of the receiver in all cases is approximately -130 dBm.
* The terrain model is accurate to 30 meters.
* In the hosted version, signals do not travel farther than 100 kilometers from the transmitter.

These assumptions have been tested and found to be practical in typical usage scenarios. Please use discretion when applying results from this tool and verify the results if your project depends on them.


## Building

Requirements:

* 3 arcsecond resolution NASA SRTM elevation dataset in `.hgt` format, available from https://registry.opendata.aws/terrain-tiles/
* docker
* git

copy the `.hgt` files to a convenient folder, `my_srtm_data`.

```
git clone --recurse-submodules https://github.com/mrpatrick1991/meshtastic_linkplanner/ && cd meshtastic_linkplanner

docker build -t linkplanner .

docker run --env h3_res=8 \
           --env max_distance_km=100 \
           --env tile_dir=/app/srtm_tiles \
           -v my_srtm_data:/app/srtm_tiles \
           -p 80:8080 linkplanner
```

Note: It is recommended to leave the `max_distance` at 100 kilometers and `h3_res` as 8 so that the computation is fast.

## Disclaimer

Follow local radio communication laws. Some Meshtastic projects may require an amateur radio license. 

## References

* geoprop-py: https://github.com/JayKickliter/geoprop-py
* LeafletJS: https://leafletjs.com
* ITM / Longley-Rice model: https://its.ntia.gov/software/itm
* Meshtastic: https://meshtastic.org
