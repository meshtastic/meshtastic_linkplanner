from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from rasterio.io import MemoryFile
from io import BytesIO
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from geoprop import Tiles, Itm, Point, Climate
from dotenv import dotenv_values
from regions import meshtastic_regions
from scipy.interpolate import griddata
from rasterio.transform import from_origin
import numpy as np
import logging
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
    grid_resolution: int = Field(
        1000, ge=128, le=10000, description="geo tiff resolution in pixels"
    )


async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != config["api_key"]:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.post("/predict", dependencies=[Depends(verify_api_key)])
async def predict(payload: PredictRequest) -> StreamingResponse:
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
    grid_resolution = payload.grid_resolution  # Change this value as needed

    prediction_geo = []
    for sample in prediction_h3:
        sample_h3, sample_elevation, sample_loss_db = sample
        sample_lat, sample_lon = h3.h3_to_geo(hex(sample_h3))
        sample_rssi = tx_power + payload.tx_gain + payload.rx_gain - sample_loss_db
        prediction_geo.append((sample_lat, sample_lon, sample_rssi))

    prediction_geo = np.array(prediction_geo)
    values = prediction_geo[:, 2]

    # Create grid and perform interpolation
    try:
        grid_x, grid_y = np.mgrid[
            np.min(prediction_geo[:, 0]) : np.max(prediction_geo[:, 0]) : complex(
                0, grid_resolution
            ),
            np.min(prediction_geo[:, 1]) : np.max(prediction_geo[:, 1]) : complex(
                0, grid_resolution
            ),
        ]
        grid_values = griddata(
            prediction_geo[:, :2], values, (grid_x, grid_y), method="cubic"
        )
    except Exception as e:
        logging.error(f"Image interpolation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error during interpolation.")

    # Calculate transform for GeoTIFF
    min_x, max_x = np.min(prediction_geo[:, 0]), np.max(prediction_geo[:, 0])
    min_y, max_y = np.min(prediction_geo[:, 1]), np.max(prediction_geo[:, 1])
    pixel_size_x = (max_x - min_x) / grid_resolution
    pixel_size_y = (max_y - min_y) / grid_resolution
    transform = from_origin(min_x, max_y, pixel_size_x, pixel_size_y)

    if np.isnan(grid_values).any():
        logging.warning("NaN values found in grid_values. Replacing them with 0.")
        grid_values = np.nan_to_num(grid_values, nan=0)
    # Normalize the grid_values to a 0-255 scale for uint8
    grid_values = np.interp(grid_values, (np.min(grid_values), np.max(grid_values)), (0, 255))

    with open("grid.txt","w") as f:
        for value in grid_values:
            f.write(str(value))
        f.close()

    # Use BytesIO to create an in-memory file for GeoTIFF
    file_bytes = BytesIO()
    try:
        with MemoryFile() as memfile:
            with memfile.open(
                driver="GTiff",
                height=grid_values.shape[0],
                width=grid_values.shape[1],
                count=1,
                dtype=grid_values.dtype,
                crs="EPSG:4326",
                transform=transform,
            ) as dataset:
                dataset.write(grid_values, 1)

            # Write the GeoTIFF data to BytesIO
            file_bytes.write(memfile.read())

        # Reset buffer to the beginning before returning it
        file_bytes.seek(0)

        return StreamingResponse(
            file_bytes,
            media_type="image/tiff",
            headers={
                "Content-Disposition": 'attachment; filename="predicted_field.tif"'
            },
        )
    except Exception as e:
        logging.error(f"GeoTIFF generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error generating GeoTIFF.")
