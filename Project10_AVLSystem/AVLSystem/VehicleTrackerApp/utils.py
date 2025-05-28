import os
import struct
from datetime import datetime
import logging
import math
import re

#  (Logging configuration)
os.makedirs('./logs', exist_ok=True)
logging.basicConfig(level=logging.INFO, filename='./logs/shapefile.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Function to write a double value in Little-endian format to a binary file
def write_le_double(file, value):
    # Write the value as a little-endian double
    file.write(struct.pack('<d', value))
    logger.debug(f"Wrote double value: {value}")


# creating directory for saving
def get_storage_directory():
    # Define the directory path for storing shapefiles
    dir_path = './shapefiles'

    # Create the directory if it doesn't already exist
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)

    # Log the absolute path where shapefiles will be stored
    logger.info(f"Shapefiles will be saved in: {os.path.abspath(dir_path)}")

    # Return the directory path
    return dir_path


# writing .shp file
def write_shp(coords, file_path):
    # Log that the .shp file writing has started
    logger.info(f"Writing .shp file: {file_path}")

    with open(file_path, 'wb') as f:
        # Calculate Bounding Box from coordinates
        minX = min(p[0] for p in coords)  # longitude
        minY = min(p[1] for p in coords)  # latitude
        maxX = max(p[0] for p in coords)
        maxY = max(p[1] for p in coords)
        logger.debug(f"Bounding Box: minX={minX}, minY={minY}, maxX={maxX}, maxY={maxY}")

        # Compute content length in 16-bit words
        content_length = (44 + 4 + len(coords) * 16) // 2
        logger.debug(f"Content length: {content_length} 16-bit words")

        # Write main file header (Big-endian for main parts)
        f.write(struct.pack('>I', 9994))  # File code
        f.write(struct.pack('>5I', *[0] * 5))  # Unused bytes
        f.write(struct.pack('>I', 50 + content_length))  # File length in 16-bit words
        f.write(struct.pack('<I', 1000))  # Version
        f.write(struct.pack('<I', 3))  # Shape type: Polyline

        # Write bounding box coordinates
        write_le_double(f, minX)
        write_le_double(f, minY)
        write_le_double(f, maxX)
        write_le_double(f, maxY)

        # Write zero for Z and M ranges
        for _ in range(4):
            write_le_double(f, 0.0)

        # Write shape record
        f.write(struct.pack('>I', 1))  # Record number
        f.write(struct.pack('>I', content_length))  # Content length
        f.write(struct.pack('<I', 3))  # Shape type: Polyline
        write_le_double(f, minX)
        write_le_double(f, minY)
        write_le_double(f, maxX)
        write_le_double(f, maxY)
        f.write(struct.pack('<I', 1))  # Number of parts
        f.write(struct.pack('<I', len(coords)))  # Number of points
        f.write(struct.pack('<I', 0))  # Index of the first part

        # Write each coordinate pair (X=lon, Y=lat)
        for lon, lat in coords:
            write_le_double(f, lon)
            write_le_double(f, lat)
            logger.debug(f"Wrote coordinate: ({lon}, {lat})")


# writing.shx file
def write_shx(coords, file_path):
    # Log that the .shx file writing has started
    logger.info(f"Writing .shx file: {file_path}")

    with open(file_path, 'wb') as f:
        # Calculate content length in 16-bit words (same logic as .shp)
        content_length = (44 + 4 + len(coords) * 16) // 2

        # Write file header (Big-endian)
        f.write(struct.pack('>I', 9994))  # File code
        f.write(struct.pack('>5I', *[0] * 5))  # Unused bytes
        f.write(struct.pack('>I', 50 + 4))  # File length in 16-bit words (shx file is smaller)
        f.write(struct.pack('<I', 1000))  # Version
        f.write(struct.pack('<I', 3))  # Shape type: Polyline

        # Calculate Bounding Box from coordinates
        minX = min(p[0] for p in coords)
        minY = min(p[1] for p in coords)
        maxX = max(p[0] for p in coords)
        maxY = max(p[1] for p in coords)
        write_le_double(f, minX)
        write_le_double(f, minY)
        write_le_double(f, maxX)
        write_le_double(f, maxY)

        # Write zeros for Z and M ranges
        for _ in range(4):
            write_le_double(f, 0.0)

        # Write index record (offset and content length)
        f.write(struct.pack('>I', 50))  # Record offset (in 16-bit words)
        f.write(struct.pack('>I', content_length))  # Record content length (in 16-bit words)
        logger.debug(f"Index record: offset=50, content_length={content_length}")


# writing .dbf file
def write_dbf(feature_count, file_path, phone_id):
    # Log that the .dbf file writing has started
    logger.info(f"Writing .dbf file: {file_path}")

    with open(file_path, 'wb') as f:
        # Write dBASE III header
        f.write(struct.pack('<B', 3))  # dBASE III version
        now = datetime.now()
        f.write(struct.pack('<3B', now.year - 1900, now.month, now.day))  # Date of last update (YY/MM/DD)
        f.write(struct.pack('<I', feature_count))  # Number of records
        f.write(struct.pack('<H', 33))  # Header length (33 bytes for 1 field)
        f.write(struct.pack('<H', 11))  # Record length: 1 (deletion flag) + 10 (field length)
        f.write(bytes([0] * 20))  # Reserved space

        # Define the field "PHONE_ID" as a character field
        f.write(b'PHONE_ID' + bytes([0] * 4))  # Field name (padded to 11 bytes)
        f.write(b'C')  # Field type: Character
        f.write(struct.pack('<I', 0))  # Field data address (not used)
        f.write(struct.pack('<B', 10))  # Field length
        f.write(struct.pack('<B', 0))  # Decimal count
        f.write(bytes([0] * 14))  # Remaining field descriptor bytes
        f.write(bytes([0x0D]))  # Field descriptor terminator

        # Write each record
        for i in range(feature_count):
            f.write(bytes([0x20]))  # Not deleted flag
            f.write(phone_id[:10].encode('ascii').ljust(10))  # Write phone_id, padded/truncated to 10 characters
            logger.debug(f"Wrote dbf record: phone_id={phone_id[:10]}")


# writing .dbf file
def write_prj(file_path):
    # Log that the .prj file writing has started
    logger.info(f"Writing .prj file: {file_path}")

    # Define the WKT (Well-Known Text) for WGS 84 projection
    wgs84 = 'GEOGCS["WGS 84",DATUM["WGS_1984",SPHEROID["WGS 84",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]]'

    try:
        # Write the projection definition to the .prj file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(wgs84)

        # Log success
        logger.info(f"PRJ file written successfully: {file_path}")
    except Exception as e:
        # Log and re-raise any error that occurs during file writing
        logger.error(f"Error writing PRJ file {file_path}: {e}")
        raise


def save_shapefile(coords, phone_id,model):
    # Log the start of the shapefile saving process, including the phone_id and the number of coordinates
    logger.info(f"Starting save_shapefile for phone_id: {phone_id}, coords count: {len(coords)}")
    # Check if coordinates are provided
    if not coords:
        logger.error("No coordinates provided")
        raise ValueError("No coordinates to save")
    # Ensure that at least two coordinates are provided to form a polyline
    if len(coords) < 2:
        logger.error("Less than 2 coordinates provided")
        raise ValueError("At least 2 coordinates required for PolyLine")
    # Get the directory path for storage
    dir_path = get_storage_directory()
    # Sanitize the model name by removing non-alphanumeric characters and converting to lowercase
    sanitized_model = re.sub(r'\W+', '_', model).lower()
    # Generate a base name for the shapefile, including model and phone_id (last 4 characters), and current time
    base_name = f"track_{sanitized_model}_{phone_id[-4:]}_{datetime.now().strftime('%H%M')}"
    # Log the generated base name for the shapefile
    logger.info(f"Base name for shapefile: {base_name}")
    # Define file paths for shapefile components (shp, shx, dbf, and prj)
    shp_file = os.path.join(dir_path, base_name + ".shp")
    shx_file = os.path.join(dir_path, base_name + ".shx")
    dbf_file = os.path.join(dir_path, base_name + ".dbf")
    prj_file = os.path.join(dir_path, base_name + ".prj")

    try:
        # Write the shapefile components (shp, shx, dbf, prj) using the appropriate helper functions
        write_shp(coords, shp_file)
        write_shx(coords, shx_file)
        write_dbf(1, dbf_file, phone_id)
        write_prj(prj_file)
    except Exception as e:
        # Log and raise any errors encountered while creating the shapefile
        logger.error(f"Error creating shapefile: {e}")
        raise
    # Check if all the shapefile components were successfully created and are not empty
    files = [(shp_file, "shp"), (shx_file, "shx"), (dbf_file, "dbf"), (prj_file, "prj")]
    for file_path, ext in files:
        # If any file is missing or empty, log an error and raise an exception
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            logger.error(f"Failed to save {ext} file: {file_path} is missing or empty")
            raise ValueError(f"Failed to save {ext} file: {file_path} is missing or empty")
    # Log that the shapefile was successfully saved
    logger.info(f"Shapefile saved successfully: {shp_file}")
    # Return the base name of the shapefile
    return base_name

