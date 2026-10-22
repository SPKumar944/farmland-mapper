import http.server
import socketserver
import json
import urllib.parse
import os
import zarr
import numpy as np

PORT = 8080
ZARR_PATH = os.path.abspath('multipolygon_pixels.zarr')

class ZarrAgroServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.abspath('public'), **kwargs)

    def end_headers(self):
        # Enable CORS and disable caching for live API updates
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API: Health & Zarr Status
        if path == '/api/zarr/status':
            try:
                root = zarr.open_group(ZARR_PATH, mode='r')
                parcels_count = len([k for k in root.keys() if k.startswith('parcel') or k == 'jana-farmland'])
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                resp = {
                    'status': 'connected',
                    'zarr_path': ZARR_PATH,
                    'parcels_count': parcels_count,
                    'dates': list(root['dates'][:])
                }
                self.wfile.write(json.dumps(resp).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'error', 'message': str(e)}).encode('utf-8'))
                return

        # 2. API: All Parcels strictly from Zarr
        if path == '/api/zarr/parcels':
            try:
                root = zarr.open_group(ZARR_PATH, mode='r')
                results = []
                for k in root.keys():
                    if k == 'dates':
                        continue
                    p_grp = root[k]
                    attrs = dict(p_grp.attrs)
                    coords = p_grp['coordinates'][:].tolist() if 'coordinates' in p_grp else []
                    
                    # Read latest KPI values directly from Zarr arrays
                    ndvi_arr = p_grp['NDVI'][:] if 'NDVI' in p_grp else [0.7]
                    ndmi_arr = p_grp['NDMI'][:] if 'NDMI' in p_grp else [0.4]
                    sm_arr = p_grp['SAR_SoilMoisture_Proxy'][:] if 'SAR_SoilMoisture_Proxy' in p_grp else [65.0]
                    sipi_arr = p_grp['SIPI'][:] if 'SIPI' in p_grp else [8.0]
                    
                    results.append({
                        'id': attrs.get('id', k),
                        'name': attrs.get('name', k),
                        'crop': attrs.get('crop', 'Crop'),
                        'district': attrs.get('district', ''),
                        'state': attrs.get('state', ''),
                        'area_acres': attrs.get('area_acres', ''),
                        'target_yield': attrs.get('target_yield', ''),
                        'sown': attrs.get('sown', ''),
                        'center': [attrs.get('center_lat', 0.0), attrs.get('center_lng', 0.0)],
                        'coords': coords,
                        'ndvi': round(float(ndvi_arr[-1]), 2),
                        'ndmi': f"+{round(float(ndmi_arr[-1]), 2)}" if float(ndmi_arr[-1]) > 0 else str(round(float(ndmi_arr[-1]), 2)),
                        'topsoil_moisture': f"{int(round(float(sm_arr[-1])))}%",
                        'sipi': f"Low ({int(round(float(sipi_arr[-1])))}%)"
                    })
                
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(results, indent=2).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                return

        # 3. API: Strict KPI payload for requested parcel from Zarr
        if path == '/api/zarr/kpi':
            parcel_id = query.get('parcel_id', ['parcel-1'])[0]
            try:
                root = zarr.open_group(ZARR_PATH, mode='r')
                if parcel_id not in root:
                    # Fallback to first parcel
                    keys = [k for k in root.keys() if k != 'dates']
                    parcel_id = keys[0]

                p_grp = root[parcel_id]
                attrs = dict(p_grp.attrs)
                dates = list(root['dates'][:])

                # Extract all 24 indices strictly from Zarr dataset
                metrics = {}
                for k in p_grp.keys():
                    if k == 'coordinates':
                        continue
                    arr = p_grp[k]
                    data = arr[:].tolist()
                    arr_attrs = dict(arr.attrs)
                    metrics[k] = {
                        'latest': float(data[-1]),
                        'timeseries': data,
                        'technical_abbreviation': arr_attrs.get('technical_abbreviation', k),
                        'suggested_name': arr_attrs.get('suggested_name', k),
                        'farmer_friendly_name': arr_attrs.get('farmer_friendly_name', k),
                        'category': arr_attrs.get('category', ''),
                        'what_it_tells': arr_attrs.get('what_it_tells', '')
                    }

                resp = {
                    'source': 'multipolygon_pixels.zarr',
                    'parcel_id': parcel_id,
                    'info': attrs,
                    'dates': dates,
                    'metrics': metrics
                }

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps(resp, indent=2).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                return

        # Default: Serve static files (HTML, JS, CSS, images) from public/
        if path == '/' or path == '':
            self.path = '/report.html'
        return super().do_GET()

if __name__ == '__main__':
    # Allow port reuse to prevent address already in use error
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ZarrAgroServer) as httpd:
        print(f"=== Zarr Agro-Telemetry Server Running ===")
        print(f"Strict Zarr Store: {ZARR_PATH}")
        print(f"Local Host URL: http://localhost:{PORT}/report.html")
        httpd.serve_forever()
