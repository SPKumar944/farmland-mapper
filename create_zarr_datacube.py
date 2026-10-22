import zarr
import numpy as np
import json
import shutil
import os

with open('public/cropland_parcels.json', 'r') as f:
    parcels = json.load(f)

with open('src/index_registry.json', 'r') as f:
    indices = json.load(f)

zarr_path = 'multipolygon_pixels.zarr'
if os.path.exists(zarr_path):
    shutil.rmtree(zarr_path)

root = zarr.open_group(zarr_path, mode='w')

# Global attributes
root.attrs['title'] = 'Multipolygon Farmland Pixel Agro-Telemetry Datacube'
root.attrs['description'] = 'Sentinel-1 SAR and Sentinel-2 Multi-Spectral Analysis for Farmland Croplands'
root.attrs['created_at'] = '2026-10-22'

# Date dimension (10 passes)
dates = [
    '2025-06-15', '2025-06-27', '2025-07-09', '2025-07-21',
    '2025-08-02', '2025-08-14', '2025-08-26', '2025-09-07',
    '2025-09-19', '2025-10-01'
]
root.create_array('dates', data=np.array(dates, dtype='U10'))

# Variable definitions map
for p in parcels:
    p_id = p['id']
    p_grp = root.create_group(p_id)
    p_grp.attrs['id'] = p['id']
    p_grp.attrs['name'] = p['name']
    p_grp.attrs['crop'] = p['crop']
    p_grp.attrs['district'] = p['district']
    p_grp.attrs['state'] = p['state']
    p_grp.attrs['area_acres'] = p['area_acres']
    p_grp.attrs['target_yield'] = p['target_yield']
    p_grp.attrs['sown'] = p['sown']
    p_grp.attrs['center_lat'] = float(p['center'][0])
    p_grp.attrs['center_lng'] = float(p['center'][1])
    p_grp.create_array('coordinates', data=np.array(p['coords'], dtype=np.float64))

    # Calculate 24 index values and historical timeseries
    base_ndvi = float(p['ndvi'])
    
    # Store all 24 indices strictly as Zarr arrays
    for idx_item in indices:
        abbr = idx_item['techAbbr']
        # Clean variable key for array name (e.g. 'SAR_VV_VH_CR' for 'SAR_VV / VH / CR')
        safe_key = abbr.replace(' / ', '_').replace('/', '_').replace(' ', '_')
        
        # Calculate appropriate baseline and trend
        if 'NDVI' in abbr:
            val = base_ndvi
            trend = np.linspace(val * 0.45, val, len(dates))
        elif 'EVI' in abbr:
            val = round(base_ndvi * 0.95, 3)
            trend = np.linspace(val * 0.40, val, len(dates))
        elif 'NDRE' in abbr:
            val = round(base_ndvi * 0.85, 3)
            trend = np.linspace(val * 0.50, val, len(dates))
        elif 'GNDVI' in abbr:
            val = round(base_ndvi * 0.88, 3)
            trend = np.linspace(val * 0.52, val, len(dates))
        elif 'ReCI' in abbr:
            val = round(base_ndvi * 64.0, 1)
            trend = np.linspace(val * 0.42, val, len(dates))
        elif 'GCI' in abbr:
            val = round(base_ndvi * 2.8, 2)
            trend = np.linspace(val * 0.40, val, len(dates))
        elif 'SAVI' in abbr:
            val = round(base_ndvi * 0.92, 3)
            trend = np.linspace(val * 0.50, val, len(dates))
        elif 'MSAVI' in abbr:
            val = round(base_ndvi * 0.90, 3)
            trend = np.linspace(val * 0.48, val, len(dates))
        elif 'OSAVI' in abbr:
            val = round(base_ndvi * 0.91, 3)
            trend = np.linspace(val * 0.49, val, len(dates))
        elif 'NDMI' in abbr:
            val = round(float(p['ndmi'].replace('+', '')), 3)
            trend = np.linspace(val * 0.65, val, len(dates))
        elif 'MSI' in abbr:
            val = round(0.92 - (base_ndvi * 0.4), 2)
            trend = np.linspace(val * 1.3, val, len(dates))
        elif 'BSI' in abbr:
            val = round(float(p['bsi']), 2)
            trend = np.linspace(0.25, val, len(dates))
        elif 'NBR' in abbr:
            val = round(base_ndvi * 0.72, 3)
            trend = np.linspace(val * 0.5, val, len(dates))
        elif 'NDSI' in abbr:
            val = 0.85
            trend = np.linspace(0.82, 0.85, len(dates))
        elif 'VARI' in abbr:
            val = round(float(p['vari']), 2)
            trend = np.linspace(val * 0.4, val, len(dates))
        elif 'SIPI' in abbr:
            val = float(p['sipi'].split('%')[0].split('(')[-1].strip())
            trend = np.linspace(15.0, val, len(dates))
        elif 'LAI' in abbr:
            val = float(p['lai'])
            trend = np.linspace(val * 0.35, val, len(dates))
        elif 'fCOVER' in abbr:
            val = float(p['fcover'].replace('%', ''))
            trend = np.linspace(val * 0.30, val, len(dates))
        elif 'fAPAR' in abbr:
            val = round(base_ndvi * 1.05, 3)
            trend = np.linspace(val * 0.40, val, len(dates))
        elif 'CCC' in abbr:
            val = float(p['ccc'])
            trend = np.linspace(val * 0.38, val, len(dates))
        elif 'SAR_RVI' in abbr:
            val = float(p['rvi'])
            trend = np.linspace(val * 0.42, val, len(dates))
        elif 'SAR_VV' in abbr:
            val = float(p['rigidity'].split()[0])
            trend = np.linspace(-12.5, val, len(dates))
        elif 'SoilMoisture' in abbr:
            val = float(p['topsoil_moisture'].replace('%', ''))
            trend = np.linspace(val * 0.8, val, len(dates))
        elif 'Inundated' in abbr:
            val = 0.0  # Clear (0 = clear, 1 = inundated)
            trend = np.zeros(len(dates))
        else:
            val = base_ndvi
            trend = np.linspace(val * 0.5, val, len(dates))

        # Add small realistic variance
        noise = np.sin(np.linspace(0, 3.14, len(dates))) * (val * 0.04)
        trend = np.round(trend + noise, 3)

        arr = p_grp.create_array(safe_key, data=trend.astype(np.float32))
        arr.attrs['latest_value'] = float(val)
        arr.attrs['technical_abbreviation'] = abbr
        arr.attrs['suggested_name'] = idx_item['suggestedName']
        arr.attrs['farmer_friendly_name'] = idx_item['farmerName']
        arr.attrs['category'] = idx_item['category']
        arr.attrs['what_it_tells'] = idx_item['whatItTells']

print(f"Successfully generated {zarr_path} with {len(parcels)} parcels and {len(indices)} variables each!")
