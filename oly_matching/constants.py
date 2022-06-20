VEHICLE_IDENTIFIER_COLUMNS_TECDOC = [
    "N-Type No.",
    "Manufacturer",
    "Model Series",
    "Type",
    "Body Type",
    "Model Year from",  # TODO: what does it mean if missing?
    "Model Year to",  # TODO: what does it mean if missing?
    "Engine Codes",
    "Tonnage",
    "Axle Configuration",
]

VEHICLE_IDENTIFIER_COLUMNS_LIS = [
    "type_id",
    "make",
    "model",
    "type",
    "type_year_start",
    "type_year_end",
    "component_code"
    # "axle_configuration"  # constructed in code from 'type' column
]

# Note: "type year" is not available in TecDoc, so we must make do with "model year"
MATCHING_COLUMN_MAPPING = {
    "Manufacturer": "make",
    "Model Series": "model",
    "Type": "type",  # granularity TecDoc < LIS
    "LnkTargetType": "category",  # granularity TecDoc > LIS
    "Model Year from": "model_year_start",  # granularity TecDoc > granularity LIS (month vs year)
    "Model Year to": "model_year_end",  # granularity TecDoc > granularity LIS (month vs year)
    "Engine Codes": "component_code",
    "Axle Configuration": "axle_configuration"
}

# We only keep relevant columns in the matching algorithm
LIS_COLUMNS = [x for x in MATCHING_COLUMN_MAPPING.values() if x != "axle_configuration"]
LIS_COLUMNS += ["type_id"]

TECDOC_COLUMNS = list(MATCHING_COLUMN_MAPPING.keys())
TECDOC_COLUMNS += ["N-Type No."]

# Cleaning
STR_COLS = ['make', 'model', 'type', 'category', 'component_code', 'axle_configuration']

CATEGORY_MAPPING = {
    'TecDoc Bus': "Trucks and Buses (> 7.5t)",
    'TecDoc CV': "Trucks and Buses (> 7.5t)",
    'TecDoc E-Bus': "Trucks and Buses (> 7.5t)",
    'TecDoc Tractor': "Agricultural Equipment",
}

UNIQUE_AXLE_CONFIGS = [
    "4x4",
    "4x2",
    "6x2",
    "6x2/4",
    "6x4",
    "8x2/4",
    "8x4",
    "6x6",
    "8x6/4",
    "8x8/4",
    "8x8",
    "8x2",
    "8x4/4",
    "10x2/4",
    "10x4/6",
    "8x2/6",
    "2x2",
    "8x6/6",
    "10x4/8",
    "10x6/8",
    "10x8/6",
    "10x8/8",
    "6x4/4",
    "8x4/6",
    "4x4/4",
    "10x4/4",
    "10x6/6",
    "10x6/4",
]

# Note: USA/CAN must be BEFORE USA for code below to work
ALLOWED_COUNTRY_CODES = ["usa / can", "eu", "usa", "bra", "itl", "mb", "rk"]
# ["USA / CAN", "EU", "USA", "BRA", "ITL", "MB", "RK"]

VEHICLE_TYPES_LIS = ["construction", "tractor", "chassis"]  # for cleaning model column, could be other columns too

# Matching
REQUIRED_MATCHING_COLS = ["make", "model", "type", "component_code"]
