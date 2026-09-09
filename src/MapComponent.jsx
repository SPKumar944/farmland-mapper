import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Polygon, useMapEvents, LayersControl, useMap, ZoomControl } from 'react-leaflet';
import { GeoSearchControl, OpenStreetMapProvider } from 'leaflet-geosearch';
import 'leaflet/dist/leaflet.css';
import 'leaflet-geosearch/dist/geosearch.css';
import L from 'leaflet';

import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
    iconUrl: icon,
    shadowUrl: iconShadow,
    iconSize: [25, 41],
    iconAnchor: [12, 41]
});
L.Marker.prototype.options.icon = DefaultIcon;

function MapEvents({ points, setPoints, mode, isRecording }) {
  useMapEvents({
    click(e) {
      if (mode === 'draw') {
        setPoints((prev) => [...prev, [e.latlng.lat, e.latlng.lng]]);
      }
    },
  });
  return null;
}

function SearchField() {
  const map = useMap();
  useEffect(() => {
    const provider = new OpenStreetMapProvider();
    const searchControl = new GeoSearchControl({
      provider: provider,
      style: 'bar',
      showMarker: false,
      autoClose: true,
      searchLabel: 'Search places...',
      position: 'topright'
    });
    map.addControl(searchControl);
    return () => map.removeControl(searchControl);
  }, [map]);
  return null;
}

// Component to recenter map on user when GPS updates
function RecenterOnRecord({ latestPoint, isRecording }) {
  const map = useMap();
  useEffect(() => {
    if (isRecording && latestPoint) {
      map.setView(latestPoint, map.getZoom(), { animate: true });
    }
  }, [latestPoint, isRecording, map]);
  return null;
}

export default function MapComponent({ userPhone }) {
  const [points, setPoints] = useState([]);
  const [isSaving, setIsSaving] = useState(false);
  
  // New states for GPS tracking
  const [mode, setMode] = useState('draw'); // 'draw' or 'record'
  const [isRecording, setIsRecording] = useState(false);
  const watchIdRef = useRef(null);

  const handleSave = async () => {
    if (points.length < 3) {
      alert("Please ensure you have at least 3 points for your farmland boundary.");
      return;
    }

    setIsSaving(true);
    try {
      const API_URL = "https://script.google.com/macros/s/AKfycbw7iGedtxuuuIKzmoHdu6n1IJJnV7LSmm6IujuLLB9FMGOFCjUKU4-JNiUOqlCcoYuwOA/exec";
      
      const closedPoints = [...points, points[0]];

      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "text/plain;charset=utf-8",
        },
        body: JSON.stringify({
          email: userPhone,
          polygon: closedPoints 
        }),
      });

      const result = await response.json();
      if (result.status === 'success') {
        alert("Farmland demarcated and saved to Drive successfully!");
        setPoints([]); 
      } else {
        alert("Failed to save: " + result.message);
      }
    } catch (e) {
      console.error(e);
      alert("Error saving data. Make sure the Apps Script URL is set and deployed correctly.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleClear = () => {
    if (isRecording) stopRecording();
    setPoints([]);
  };

  const startRecording = () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by your browser.");
      return;
    }

    setIsRecording(true);
    watchIdRef.current = navigator.geolocation.watchPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setPoints((prev) => {
          // Avoid adding duplicate points if the user is standing still
          if (prev.length > 0) {
            const last = prev[prev.length - 1];
            if (last[0] === latitude && last[1] === longitude) return prev;
          }
          return [...prev, [latitude, longitude]];
        });
      },
      (error) => {
        console.error("GPS Error:", error);
        alert("Failed to get GPS location. Please ensure location permissions are granted.");
        stopRecording();
      },
      {
        enableHighAccuracy: true,
        maximumAge: 0,
        timeout: 10000
      }
    );
  };

  const stopRecording = () => {
    if (watchIdRef.current !== null) {
      navigator.geolocation.clearWatch(watchIdRef.current);
      watchIdRef.current = null;
    }
    setIsRecording(false);
  };

  const toggleMode = (newMode) => {
    if (isRecording) stopRecording();
    setMode(newMode);
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      {/* Top Header / Mode Switcher */}
      <div style={{ 
        position: 'absolute', top: 10, left: '50%', transform: 'translateX(-50%)', zIndex: 1000, 
        backgroundColor: 'rgba(255,255,255,0.95)', padding: '10px', borderRadius: '8px',
        boxShadow: '0 2px 5px rgba(0,0,0,0.2)', textAlign: 'center', width: '90%', maxWidth: '350px'
      }}>
        <h3 style={{ margin: '0 0 10px 0' }}>Demarcate Farm</h3>
        
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginBottom: '10px' }}>
          <button 
            onClick={() => toggleMode('draw')}
            style={{
              padding: '8px 15px', borderRadius: '20px', border: '1px solid #4CAF50',
              backgroundColor: mode === 'draw' ? '#4CAF50' : 'white',
              color: mode === 'draw' ? 'white' : '#4CAF50', cursor: 'pointer', fontWeight: 'bold'
            }}
          >
            👆 Draw Mode
          </button>
          <button 
            onClick={() => toggleMode('record')}
            style={{
              padding: '8px 15px', borderRadius: '20px', border: '1px solid #2196F3',
              backgroundColor: mode === 'record' ? '#2196F3' : 'white',
              color: mode === 'record' ? 'white' : '#2196F3', cursor: 'pointer', fontWeight: 'bold'
            }}
          >
            🚶 Walk Mode
          </button>
        </div>

        <p style={{ margin: 0, fontSize: '14px', color: '#555' }}>
          {mode === 'draw' 
            ? `Tap map to add corners (${points.length} points)` 
            : `Walk boundary to record (${points.length} points)`
          }
        </p>
      </div>

      <MapContainer 
        center={[20.5937, 78.9629]}
        zoom={5} 
        zoomControl={false}
        style={{ width: '100%', height: '100%', zIndex: 1 }}
      >
        <SearchField />
        <RecenterOnRecord latestPoint={points[points.length - 1]} isRecording={isRecording} />
        
        <ZoomControl position="bottomright" />
        <LayersControl position="bottomleft">
          <LayersControl.BaseLayer checked name="Hybrid (Satellite + Labels)">
            <TileLayer
              attribution='&copy; Google'
              url="https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}"
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="OpenStreetMap">
            <TileLayer
              attribution='&copy; <a href="https://osm.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
          </LayersControl.BaseLayer>
          <LayersControl.BaseLayer name="Satellite Only">
            <TileLayer
              attribution='Tiles &copy; Esri'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            />
          </LayersControl.BaseLayer>
        </LayersControl>
        
        <MapEvents points={points} setPoints={setPoints} mode={mode} />

        {points.map((pos, idx) => (
          <Marker key={idx} position={pos} />
        ))}

        {points.length >= 3 && (
          <Polygon positions={points} pathOptions={{ color: 'blue', fillColor: 'blue', fillOpacity: 0.4 }} />
        )}
      </MapContainer>
      
      {/* Bottom Actions */}
      <div style={{
        position: 'absolute', bottom: 30, left: '50%', transform: 'translateX(-50%)',
        zIndex: 1000, display: 'flex', flexDirection: 'column', gap: '10px', alignItems: 'center'
      }}>
        
        {mode === 'record' && (
          <button 
            onClick={isRecording ? stopRecording : startRecording}
            style={{
              backgroundColor: isRecording ? '#f44336' : '#2196F3', color: 'white', padding: '12px 25px',
              border: 'none', borderRadius: '25px', fontWeight: 'bold', boxShadow: '0 4px 6px rgba(0,0,0,0.3)',
              cursor: 'pointer', fontSize: '16px', width: '200px'
            }}
          >
            {isRecording ? "⏹ Stop Walking" : "▶️ Start Walking"}
          </button>
        )}

        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={handleClear}
            style={{
              backgroundColor: 'white', color: '#f44336', padding: '10px 20px',
              border: '2px solid #f44336', borderRadius: '25px', fontWeight: 'bold', boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
              cursor: 'pointer'
            }}
          >
            Clear
          </button>

          <button 
            onClick={handleSave}
            disabled={isSaving || points.length < 3 || isRecording}
            style={{
              backgroundColor: (isSaving || points.length < 3 || isRecording) ? '#aaa' : '#4CAF50', 
              color: 'white', padding: '10px 20px', border: 'none', borderRadius: '25px', 
              fontWeight: 'bold', boxShadow: '0 4px 6px rgba(0,0,0,0.3)', cursor: 'pointer'
            }}
          >
            {isSaving ? "Saving..." : "Save Area"}
          </button>
        </div>
      </div>
    </div>
  );
}
