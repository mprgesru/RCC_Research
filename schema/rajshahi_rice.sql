-- Rajshahi Rice Land-Use study schema
-- Engine: SQLite 3 (GeoPackage container for the canonical database)
--
-- The canonical database is a GeoPackage. Spatial layers (`zones`,
-- `reference_samples`) are created by scripts/make_db.py; this file creates the
-- attribute tables, lookup tables, views and seeds.
--
-- Run through scripts/make_db.py. Do not apply to an existing database without
-- checking foreign keys and row counts first.

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- Lookup tables
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS season_legend (
    code         TEXT PRIMARY KEY,
    label        TEXT NOT NULL,
    measure_type TEXT NOT NULL CHECK (measure_type IN ('season', 'derived')),
    description  TEXT
);

INSERT OR IGNORE INTO season_legend (code, label, measure_type, description) VALUES
    ('BORO',      'Boro',                  'season',  'Dry-season rice, labelled by harvest year'),
    ('AUS',       'Aus',                   'season',  'Summer rice'),
    ('AMAN',      'Aman',                  'season',  'Monsoon rice'),
    ('ALL_UNION', 'All-rice union',        'derived', 'Spatial union of rice in at least one season'),
    ('INTENSITY', 'Cropping intensity',    'derived', 'Number of mapped rice seasons: 0-3'),
    ('LULC',      'Land cover',            'derived', 'General land cover for transition attribution');

CREATE TABLE IF NOT EXISTS class_legend (
    code     INTEGER PRIMARY KEY,
    name     TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL CHECK (category IN ('rice', 'agriculture', 'vegetation', 'urban', 'water', 'bare', 'nodata')),
    notes    TEXT
);

INSERT OR IGNORE INTO class_legend (code, name, category, notes) VALUES
    (1,   'Boro',                    'rice',        'Rice, dry season'),
    (2,   'Aus',                     'rice',        'Rice, summer'),
    (3,   'Aman',                    'rice',        'Rice, monsoon'),
    (4,   'Other annual crop',       'agriculture', 'Non-rice annual agriculture and fallow'),
    (5,   'Orchard',                 'agriculture', 'Perennial agriculture; mango where separable'),
    (6,   'Other vegetation',        'vegetation',  'Not a substitute for rice'),
    (7,   'Built-up',                'urban',       'Urban and impervious'),
    (8,   'Water',                   'water',       'Water and wetland'),
    (9,   'Bare soil',               'bare',        'Exposed land'),
    (255, 'No data',                 'nodata',      'Insufficient observation');

-- ---------------------------------------------------------------------------
-- Operational records
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS map_runs (
    map_id             TEXT PRIMARY KEY,
    reference_year     INTEGER NOT NULL CHECK (reference_year IN (1990,1995,2000,2005,2010,2015,2020,2025)),
    season             TEXT NOT NULL REFERENCES season_legend(code),
    crop_year          INTEGER NOT NULL CHECK (crop_year BETWEEN 1989 AND 2026),
    window_start       TEXT NOT NULL,
    window_end         TEXT NOT NULL,
    sensors            TEXT NOT NULL CHECK (sensors IN ('landsat', 'landsat+sentinel1+sentinel2')),
    valid_obs_summary  TEXT,
    model_name         TEXT,
    model_version      TEXT,
    threshold          REAL CHECK (threshold IS NULL OR (threshold >= 0 AND threshold <= 1)),
    code_revision      TEXT,
    output_path        TEXT,
    low_support        INTEGER NOT NULL DEFAULT 0 CHECK (low_support IN (0, 1)),
    created_utc        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    CHECK (window_end >= window_start)
);

CREATE TABLE IF NOT EXISTS data_sources (
    source_id       TEXT PRIMARY KEY,
    title           TEXT NOT NULL,
    category        TEXT NOT NULL CHECK (category IN ('boundary', 'satellite', 'product', 'statistics', 'calendar', 'reference')),
    url             TEXT,
    version         TEXT,
    licence         TEXT,
    attribution     TEXT,
    retrieved_utc   TEXT,
    checksum_sha256 TEXT CHECK (checksum_sha256 IS NULL OR length(checksum_sha256) = 64),
    notes           TEXT
);

CREATE TABLE IF NOT EXISTS checksums (
    checksum_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    artifact_path TEXT NOT NULL,
    sha256        TEXT NOT NULL CHECK (length(sha256) = 64),
    bytes         INTEGER CHECK (bytes IS NULL OR bytes >= 0),
    stage         TEXT,
    recorded_utc  TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    UNIQUE (artifact_path, sha256)
);

-- ---------------------------------------------------------------------------
-- Analysis tables
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS area_estimates (
    estimate_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    reference_year    INTEGER NOT NULL CHECK (reference_year IN (1990,1995,2000,2005,2010,2015,2020,2025)),
    zone_id           TEXT NOT NULL REFERENCES zones(zone_id),
    season_or_measure TEXT NOT NULL CHECK (season_or_measure IN
                        ('BORO','AUS','AMAN','ALL_UNION','INTENSITY_0','INTENSITY_1','INTENSITY_2','INTENSITY_3')),
    mapped_area_ha    REAL NOT NULL CHECK (mapped_area_ha >= 0),
    adjusted_area_ha  REAL CHECK (adjusted_area_ha IS NULL OR adjusted_area_ha >= 0),
    ci95_lower_ha     REAL CHECK (ci95_lower_ha IS NULL OR ci95_lower_ha >= 0),
    ci95_upper_ha     REAL CHECK (ci95_upper_ha IS NULL OR ci95_upper_ha >= 0),
    valid_land_area_ha REAL CHECK (valid_land_area_ha IS NULL OR valid_land_area_ha >= 0),
    sample_n          INTEGER CHECK (sample_n IS NULL OR sample_n >= 0),
    ua                REAL CHECK (ua IS NULL OR (ua >= 0 AND ua <= 1)),
    pa                REAL CHECK (pa IS NULL OR (pa >= 0 AND pa <= 1)),
    f1                REAL CHECK (f1 IS NULL OR (f1 >= 0 AND f1 <= 1)),
    map_id            TEXT REFERENCES map_runs(map_id),
    UNIQUE (reference_year, zone_id, season_or_measure, map_id),
    CHECK (ci95_lower_ha IS NULL OR ci95_upper_ha IS NULL OR ci95_lower_ha <= ci95_upper_ha)
);

CREATE TABLE IF NOT EXISTS transition_estimates (
    transition_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    period_start      INTEGER NOT NULL CHECK (period_start IN (1990,1995,2000,2005,2010,2015,2020)),
    period_end        INTEGER NOT NULL CHECK (period_end IN (1995,2000,2005,2010,2015,2020,2025)),
    zone_id           TEXT NOT NULL REFERENCES zones(zone_id),
    season_or_measure TEXT NOT NULL CHECK (season_or_measure IN ('BORO','AUS','AMAN','ALL_UNION')),
    from_class        TEXT NOT NULL CHECK (from_class IN
                        ('BORO','AUS','AMAN','ALL_RICE','OTHER_CROPLAND','ORCHARD','OTHER_VEG','BUILT','WATER','BARE','NO_DATA')),
    to_class          TEXT NOT NULL CHECK (to_class IN
                        ('BORO','AUS','AMAN','ALL_RICE','OTHER_CROPLAND','ORCHARD','OTHER_VEG','BUILT','WATER','BARE','NO_DATA')),
    mapped_area_ha    REAL NOT NULL CHECK (mapped_area_ha >= 0),
    adjusted_area_ha  REAL CHECK (adjusted_area_ha IS NULL OR adjusted_area_ha >= 0),
    ci95_lower_ha     REAL CHECK (ci95_lower_ha IS NULL OR ci95_lower_ha >= 0),
    ci95_upper_ha     REAL CHECK (ci95_upper_ha IS NULL OR ci95_upper_ha >= 0),
    validation_n      INTEGER CHECK (validation_n IS NULL OR validation_n >= 0),
    UNIQUE (period_start, period_end, zone_id, season_or_measure, from_class, to_class),
    CHECK (period_end > period_start),
    CHECK (ci95_lower_ha IS NULL OR ci95_upper_ha IS NULL OR ci95_lower_ha <= ci95_upper_ha)
);

CREATE TABLE IF NOT EXISTS ward_summary (
    summary_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ward_id          TEXT NOT NULL,
    boundary_version TEXT NOT NULL,
    reference_year   INTEGER NOT NULL CHECK (reference_year IN (1990,1995,2000,2005,2010,2015,2020,2025)),
    season_or_measure TEXT NOT NULL CHECK (season_or_measure IN
                        ('BORO','AUS','AMAN','ALL_UNION','INTENSITY_0','INTENSITY_1','INTENSITY_2','INTENSITY_3')),
    mapped_area_ha    REAL NOT NULL CHECK (mapped_area_ha >= 0),
    adjusted_area_ha  REAL CHECK (adjusted_area_ha IS NULL OR adjusted_area_ha >= 0),
    ci95_lower_ha     REAL CHECK (ci95_lower_ha IS NULL OR ci95_lower_ha >= 0),
    ci95_upper_ha     REAL CHECK (ci95_upper_ha IS NULL OR ci95_upper_ha >= 0),
    UNIQUE (ward_id, boundary_version, reference_year, season_or_measure),
    CHECK (ci95_lower_ha IS NULL OR ci95_upper_ha IS NULL OR ci95_lower_ha <= ci95_upper_ha)
);

-- ---------------------------------------------------------------------------
-- Reference labels
-- ---------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS reference_labels (
    label_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    sample_id       TEXT NOT NULL,
    reference_year  INTEGER NOT NULL CHECK (reference_year IN (1990,1995,2000,2005,2010,2015,2020,2025)),
    season          TEXT NOT NULL CHECK (season IN ('LULC','BORO','AUS','AMAN')),
    reference_class TEXT,
    is_rice         INTEGER CHECK (is_rice IS NULL OR is_rice IN (0,1)),
    reference_source TEXT,
    reference_date  TEXT,
    confidence      TEXT CHECK (confidence IS NULL OR confidence IN ('high','medium','low')),
    interpreter_id  TEXT,
    notes           TEXT,
    UNIQUE (sample_id, season),
    CHECK (
        (season = 'LULC' AND reference_class IS NOT NULL AND is_rice IS NULL)
        OR (season IN ('BORO','AUS','AMAN') AND is_rice IS NOT NULL)
    )
);

CREATE INDEX IF NOT EXISTS idx_labels_year_season ON reference_labels (reference_year, season);

-- ---------------------------------------------------------------------------
-- Indexes
-- ---------------------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_map_runs_year      ON map_runs (reference_year, season);
CREATE INDEX IF NOT EXISTS idx_map_runs_support   ON map_runs (low_support);
CREATE INDEX IF NOT EXISTS idx_area_year_zone     ON area_estimates (reference_year, zone_id);
CREATE INDEX IF NOT EXISTS idx_area_measure       ON area_estimates (season_or_measure);
CREATE INDEX IF NOT EXISTS idx_area_map           ON area_estimates (map_id);
CREATE INDEX IF NOT EXISTS idx_transition_period  ON transition_estimates (period_start, period_end);
CREATE INDEX IF NOT EXISTS idx_transition_zone    ON transition_estimates (zone_id);
CREATE INDEX IF NOT EXISTS idx_ward_year          ON ward_summary (reference_year, ward_id);
CREATE INDEX IF NOT EXISTS idx_checksums_stage    ON checksums (stage);
CREATE UNIQUE INDEX IF NOT EXISTS ux_zones_zone_id ON zones (zone_id);

-- ---------------------------------------------------------------------------
-- Views
-- ---------------------------------------------------------------------------

DROP VIEW IF EXISTS v_area_estimates_full;
CREATE VIEW v_area_estimates_full AS
SELECT
    a.reference_year,
    a.zone_id,
    z.zone_name,
    z.zone_type,
    a.season_or_measure,
    a.mapped_area_ha,
    a.adjusted_area_ha,
    a.ci95_lower_ha,
    a.ci95_upper_ha,
    a.valid_land_area_ha,
    a.sample_n,
    a.ua,
    a.pa,
    a.f1,
    a.map_id,
    m.sensors,
    m.low_support,
    m.window_start,
    m.window_end
FROM area_estimates a
LEFT JOIN zones z     ON z.zone_id = a.zone_id
LEFT JOIN map_runs m  ON m.map_id  = a.map_id;

DROP VIEW IF EXISTS v_transition_full;
CREATE VIEW v_transition_full AS
SELECT
    t.period_start,
    t.period_end,
    t.zone_id,
    z.zone_name,
    z.zone_type,
    t.season_or_measure,
    t.from_class,
    t.to_class,
    t.mapped_area_ha,
    t.adjusted_area_ha,
    t.ci95_lower_ha,
    t.ci95_upper_ha,
    t.validation_n
FROM transition_estimates t
LEFT JOIN zones z ON z.zone_id = t.zone_id;

DROP VIEW IF EXISTS v_map_runs_summary;
CREATE VIEW v_map_runs_summary AS
SELECT
    reference_year,
    season,
    COUNT(*)                      AS map_runs,
    SUM(low_support)              AS low_support_runs,
    MIN(window_start)             AS first_window_start,
    MAX(window_end)               AS last_window_end
FROM map_runs
GROUP BY reference_year, season;

-- ---------------------------------------------------------------------------
-- Seed: data sources
-- ---------------------------------------------------------------------------

INSERT OR IGNORE INTO data_sources
    (source_id, title, category, url, version, licence, attribution, retrieved_utc, notes)
VALUES
    ('boundary-arcgis-rcc',
     'Rajshahi City Corporation wards and zones (EPI digital microplanning)',
     'boundary',
     'https://services.arcgis.com/5T5nSi527N4F7luB/arcgis/rest/services/Rajshahi_Wards_data/FeatureServer/0',
     '2024-10-15',
     'unstated',
     'WHO/UNICEF EPI Digital Microplanning - Rajshahi City Corporation (2024)',
     '2026-11-07T06:21:50Z',
     'Portal item bfdf7c83715a4b0781e113fb16fd2ab7. Operational boundary, not cadastral.'),

    ('stac-earth-search',
     'AWS Earth Search STAC API',
     'satellite',
     'https://earth-search.aws.element84.com/v1',
     'v1',
     'various',
     'Element 84 / AWS Open Data',
     NULL,
     'Anonymous access. Collections: landsat-c2-l2, sentinel-2-l2a, sentinel-1-grd.'),

    ('stac-planetary-computer',
     'Microsoft Planetary Computer STAC API',
     'satellite',
     'https://planetarycomputer.microsoft.com/api/stac/v1',
     'v1',
     'various',
     'Microsoft',
     NULL,
     'Anonymous access. Fallback catalog.'),

    ('landsat-c2-l2',
     'USGS Landsat Collection 2 Level-2 surface reflectance',
     'satellite',
     'https://www.usgs.gov/landsat-missions/landsat-collection-2',
     'C2 L2',
     'public-domain',
     'USGS / NASA',
     NULL,
     'Path/row 138/043 covers the study area. Landsat 4-9.'),

    ('sentinel-2-l2a',
     'Sentinel-2 Level-2A surface reflectance',
     'satellite',
     'https://developers.google.com/earth-engine/datasets/catalog/sentinel',
     'L2A',
     'copernicus',
     'ESA / Copernicus',
     NULL,
     'Available from 2015 onward.'),

    ('sentinel-1-grd',
     'Sentinel-1 ground range detected SAR',
     'satellite',
     'https://developers.google.com/earth-engine/datasets/catalog/sentinel',
     'GRD',
     'copernicus',
     'ESA / Copernicus',
     NULL,
     'Available from 2014 onward. VH and VV.'),

    ('gcd-rice',
     'Global Crop Dataset - Rice, 1990-2023',
     'product',
     'https://doi.org/10.57760/sciencedb.21665',
     'v1',
     'see-source',
     'Li et al. (2025), Scientific Data',
     NULL,
     '30 m, three seasons, 16 Asian countries. Benchmark, not ground truth.'),

    ('zhao-2026',
     'Paddy rice distribution and cropping intensity, South and Southeast Asia, 1995-2024',
     'product',
     'https://doi.org/10.5194/essd-18-5583-2026',
     '2026',
     'see-source',
     'Zhao et al. (2026), ESSD',
     NULL,
     '30 m composite maps. Benchmark at overlapping years.'),

    ('bbs-yearbooks',
     'Bangladesh Bureau of Statistics agricultural yearbooks',
     'statistics',
     'https://bbs.gov.bd/pages/static-pages/6922e0d6933eb65569e28cbf',
     'annual',
     'see-source',
     'Bangladesh Bureau of Statistics',
     NULL,
     'External consistency check only. District statistics cannot validate pixels.'),

    ('crop-calendar',
     'Bangladesh rice crop calendars (BRRI, DAE, local agronomists)',
     'calendar',
     NULL,
     NULL,
     'unstated',
     'BRRI / DAE / local experts',
     NULL,
     'Required to confirm Boro, Aus and Aman windows before production mapping.');
