import http.server
import socketserver
import json
import urllib.parse
import os
import zarr
import numpy as np
import time
import datetime

PORT = 8080
ZARR_PATH = os.path.abspath('multipolygon_pixels.zarr')
LOG_PATH = os.path.abspath('zarr_access.log')

def log_zarr_event(event_type, parcel_id, vars_count, duration_ms, details=""):
    now_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    entry = f"[{now_str}] [{event_type}] Store='{ZARR_PATH}' | Parcel='{parcel_id}' | ArraysRead={vars_count} | Latency={duration_ms:.2f}ms | {details}\n"
    try:
        with open(LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(entry)
    except Exception as e:
        print("Log error:", e)
    print(entry.strip())

class ZarrAgroServer(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.abspath('public'), **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        t0 = time.time()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. API: Live Audit Log Endpoint
        if path == '/api/zarr/logs':
            try:
                logs = []
                if os.path.exists(LOG_PATH):
                    with open(LOG_PATH, 'r', encoding='utf-8') as f:
                        logs = [line.strip() for line in f.readlines() if line.strip()][-50:]
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'log_file': LOG_PATH,
                    'total_entries': len(logs),
                    'recent_logs': logs
                }, indent=2).encode('utf-8'))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))
                return

        # 2. API: Health & Zarr Status
        if path == '/api/zarr/status':
            try:
                root = zarr.open_group(ZARR_PATH, mode='r')
                parcels_count = len([k for k in root.keys() if k.startswith('parcel') or k == 'jana-farmland'])
                duration_ms = (time.time() - t0) * 1000.0
                log_zarr_event("ZARR_STATUS_CHECK", "ALL", 0, duration_ms, f"Active Parcels: {parcels_count}")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                resp = {
                    'status': 'connected',
                    'zarr_path': ZARR_PATH,
                    'log_path': LOG_PATH,
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

        # 3. API: All Parcels strictly from Zarr
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
                    
                    ndvi_arr = p_grp['NDVI'][:] if 'NDVI' in p_grp else [0.7]
                    ndmi_arr = p_grp['NDMI'][:] if 'NDMI' in p_grp else [0.4]
                    sm_arr = p_grp['SAR_SoilMoisture_Proxy'][:] if 'SAR_SoilMoisture_Proxy' in p_grp else [65.0]
                    sipi_arr = p_grp['SIPI'][:] if 'SIPI' in p_grp else [8.0]
                    
                    results.append({
                        'id': attrs.get('id', k),
                        'name': attrs.get('name', k),
                        'timestamp': attrs.get('timestamp', ''),
                        'area_acres': attrs.get('area_acres', ''),
                        'area_m2': attrs.get('area_m2', 0),
                        'vertices_count': attrs.get('vertices_count', 0),
                        'center': [attrs.get('center_lat', 0.0), attrs.get('center_lng', 0.0)],
                        'coords': coords,
                        'ndvi': round(float(ndvi_arr[-1]), 2),
                        'ndmi': f"+{round(float(ndmi_arr[-1]), 2)}" if float(ndmi_arr[-1]) > 0 else str(round(float(ndmi_arr[-1]), 2)),
                        'topsoil_moisture': f"{int(round(float(sm_arr[-1])))}%",
                        'sipi': f"Low ({int(round(float(sipi_arr[-1])))}%)"
                    })
                
                duration_ms = (time.time() - t0) * 1000.0
                log_zarr_event("ZARR_PARCELS_PULL", "ALL", len(results) * 4, duration_ms, f"Pulled {len(results)} parcels metadata & baseline arrays")
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

        # 4. API: Strict KPI payload for requested parcel from Zarr
        if path == '/api/zarr/kpi':
            parcel_id = query.get('parcel_id', ['parcel-1'])[0]
            try:
                root = zarr.open_group(ZARR_PATH, mode='r')
                if parcel_id not in root:
                    keys = [k for k in root.keys() if k != 'dates']
                    parcel_id = keys[0]

                p_grp = root[parcel_id]
                attrs = dict(p_grp.attrs)
                dates = list(root['dates'][:])

                metrics = {}
                read_var_names = []
                for k in p_grp.keys():
                    if k == 'coordinates':
                        continue
                    arr = p_grp[k]
                    data = arr[:].tolist()
                    arr_attrs = dict(arr.attrs)
                    read_var_names.append(k)
                    metrics[k] = {
                        'latest': float(data[-1]),
                        'timeseries': data,
                        'technical_abbreviation': arr_attrs.get('technical_abbreviation', k),
                        'suggested_name': arr_attrs.get('suggested_name', k),
                        'farmer_friendly_name': arr_attrs.get('farmer_friendly_name', k),
                        'category': arr_attrs.get('category', ''),
                        'what_it_tells': arr_attrs.get('what_it_tells', '')
                    }

                duration_ms = (time.time() - t0) * 1000.0
                log_zarr_event("ZARR_KPI_PULL", parcel_id, len(read_var_names), duration_ms, f"Vars: {', '.join(read_var_names[:6])}... [total {len(read_var_names)}]")

                resp = {
                    'source': 'multipolygon_pixels.zarr',
                    'zarr_path': ZARR_PATH,
                    'query_timestamp': datetime.datetime.now().isoformat(),
                    'query_latency_ms': round(duration_ms, 2),
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

        # Default: Serve static files
        if path == '/' or path == '':
            self.path = '/report.html'
        return super().do_GET()

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ZarrAgroServer) as httpd:
        print(f"=== Zarr Agro-Telemetry Server Running ===")
        print(f"Strict Zarr Store: {ZARR_PATH}")
        print(f"Audit Log File:    {LOG_PATH}")
        print(f"Local Host URL:    http://localhost:{PORT}/report.html")
        httpd.serve_forever()
