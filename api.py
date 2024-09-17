from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from geoprop import Tiles, Itm, Point, Climate
from dotenv import dotenv_values
from regions import meshtastic_regions
import logging
import geojson
import h3
import sys


logging.basicConfig(level=logging.INFO)

config = dotenv_values(".env")
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers (x-api-key, Content-Type, etc.)
)


def load_config() -> dict:
    try:
        config = dotenv_values(".env")
        tile_dir = config["SRTM_TILE_DIR"]
        h3_res = int(config["MODEL_H3_RES"])
        max_distance_km = float(config["MAX_DISTANCE_KM"])
        api_key = config["API_KEY"]
        return {
            "tile_dir": tile_dir,
            "h3_res": h3_res,
            "max_distance_km": max_distance_km,
            "api_key": api_key,
        }
    except KeyError as e:
        logging.error(f"{e} not found in .env file, exiting.")
        sys.exit(1)
    except ValueError as e:
        logging.error(f"Invalid value for {e}, exiting.")
        sys.exit(1)


config = load_config()
tiles = Tiles(config["tile_dir"])
itm = Itm(tiles, climate=Climate.ContinentalTemperate)


class PredictRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")
    txh: float = Field(1.0, gt=0, description="Transmission height in meters")
    rxh: float = Field(1.0, gt=0, description="Reception height in meters")
    tx_gain: float = Field(1.0, ge=0, description="Transmission gain in dB")
    rx_gain: float = Field(1.0, ge=0, description="Reception gain in dB")
    region: str = Field("US", description="Region code")
    resolution: int = Field(
        8, ge=7, le=12, description="Simulation resolution in h3"
    )


async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != config["api_key"]:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.post("/predict", dependencies=[Depends(verify_api_key)])
async def predict(payload: PredictRequest) -> JSONResponse:
    if payload.region not in meshtastic_regions.keys():
        raise HTTPException(
            status_code=404, detail=f"Region '{payload.region}' not found"
        )

    try:
        center = Point(payload.lat, payload.lon, payload.txh)
        prediction_h3 = itm.coverage(
            center,
            config["h3_res"],
            meshtastic_regions[payload.region]["frequency"] * 1e6,
            config["max_distance_km"],
            payload.rxh,
            rx_threshold_db=None,
        )
    except ValueError as e:
        logging.error(f"Coverage calculation error: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Error generating model prediction: {str(e)}"
        )

    # Convert H3 data to lat/lon and RSSI
    tx_power = meshtastic_regions[payload.region]["transmit_power"]

    features = []
    for row in prediction_h3:
        hex_boundary = h3.h3_to_geo_boundary(hex(row[0]), geo_json=True)

        loss_db = row[2]
        model_rssi = tx_power + payload.tx_gain + payload.rx_gain- loss_db # simple approximation, ignoring other losses

        features.append(geojson.Feature(
            geometry=geojson.Polygon([hex_boundary]),
            properties={"model_rssi": model_rssi}
        ))

    feature_collection = geojson.FeatureCollection(features)
    print(feature_collection)

    return JSONResponse(content=feature_collection)
