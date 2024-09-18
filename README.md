# Meshtastic Link Planner 

If you just want to use the link planner, go to the hosted version: 

## About

This is a web utility to predict the range of a Meshtastic radio (see meshtastic.org). It generates a map of where your meshtastic radio can be received based on your location and antenna. The prediction accounts for terrain and calculates the expected RSSI (received signal strength indication) using the ITM / Longely-Rice model. The model parameters have been carefully chosen based on experimental data and practical experience to produce results which are accuate for meshtastic devices. Radio parameters are based on the selected LoRa region. 

## Building

Requirements:
* The 30 meter resolution NASA SRTM elevation dataset in `.hgt` format. The data is availabe from AWS open data: https://registry.opendata.aws/terrain-tiles/
* Docker
