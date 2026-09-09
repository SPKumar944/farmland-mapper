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


// Component to recenter map on user when GPS updates

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
      position: 'topleft'
    });
    map.addControl(searchControl);
    return () => map.removeControl(searchControl);
  }, [map]);
  return null;
}

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
      {/* Top Control Panel */}
      <div style={{ 
        position: 'absolute', top: 16, left: '50%', transform: 'translateX(-50%)', zIndex: 1000, 
        backgroundColor: 'rgba(255, 255, 255, 0.85)', padding: '16px', borderRadius: '20px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.12)', textAlign: 'center', width: '92%', maxWidth: '380px',
        backdropFilter: 'blur(16px)', WebkitBackdropFilter: 'blur(16px)', border: '1px solid rgba(255,255,255,0.5)',
        display: 'flex', flexDirection: 'column', gap: '16px', boxSizing: 'border-box'
      }}>
        <h3 style={{ margin: '0', fontSize: '18px', fontWeight: '600', color: '#1d1d1f', lineHeight: '1.4' }}>
          Demarcate Farm<br/><span style={{fontSize: '14px', fontWeight: '500'}}>பண்ணையின் எல்லையை குறிக்கவும்</span>
        </h3>

        {/* Mode Toggles */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', width: '100%' }}>
          <button 
            onClick={() => toggleMode('draw')}
            style={{
              flex: 1, padding: '10px 8px', borderRadius: '12px', border: '1px solid transparent',
              backgroundColor: mode === 'draw' ? '#007AFF' : '#e5e5ea',
              color: mode === 'draw' ? 'white' : '#1d1d1f', cursor: 'pointer', fontWeight: '500',
              fontSize: '15px', transition: '0.2s', lineHeight: '1.4'
            }}
          >
            👆 Draw<br/><span style={{fontSize: '12px', fontWeight: '400'}}>வரைந்து குறிக்கவும்</span>
          </button>
          <button 
            onClick={() => toggleMode('record')}
            style={{
              flex: 1, padding: '10px 8px', borderRadius: '12px', border: '1px solid transparent',
              backgroundColor: mode === 'record' ? '#007AFF' : '#e5e5ea',
              color: mode === 'record' ? 'white' : '#1d1d1f', cursor: 'pointer', fontWeight: '500',
              fontSize: '15px', transition: '0.2s', lineHeight: '1.4'
            }}
          >
            🚶 Walk<br/><span style={{fontSize: '12px', fontWeight: '400'}}>நடந்து குறிக்கவும்</span>
          </button>
        </div>

        {/* Walk Mode Specific Button */}
        {mode === 'record' && (
          <button 
            onClick={isRecording ? stopRecording : startRecording}
            style={{
              backgroundColor: isRecording ? '#FF3B30' : '#007AFF', color: 'white', padding: '12px',
              border: 'none', borderRadius: '14px', fontWeight: '600', width: '100%', margin: '0',
              cursor: 'pointer', fontSize: '16px', boxShadow: '0 2px 8px rgba(0,0,0,0.1)', lineHeight: '1.4'
            }}
          >
            {isRecording 
              ? <>⏹ Stop<br/><span style={{fontSize: '13px', fontWeight: '400'}}>நிறுத்தவும்</span></> 
              : <>▶️ Start Walk<br/><span style={{fontSize: '13px', fontWeight: '400'}}>நடக்கத் தொடங்கவும்</span></>
            }
          </button>
        )}

        {/* Status Text */}
        <p style={{ margin: '0', fontSize: '13px', color: '#86868b', fontWeight: '500', lineHeight: '1.4' }}>
          {mode === 'draw' 
            ? <>Tap map to add corners ({points.length})<br/>மூலைகளைக் குறிக்க வரைபடத்தைத் தொடவும்</> 
            : <>Walk boundary to record ({points.length})<br/>எல்லையை பதிவு செய்ய நடக்கவும்</>
          }
        </p>

        {/* Action Buttons (Clear & Save) */}
        <div style={{ display: 'flex', gap: '10px', width: '100%' }}>
          <button 
            onClick={handleClear}
            style={{
              flex: 1, backgroundColor: '#f2f2f7', color: '#FF3B30', padding: '12px',
              border: 'none', borderRadius: '14px', fontWeight: '600', 
              cursor: 'pointer', fontSize: '15px', lineHeight: '1.4'
            }}
          >
            Clear<br/><span style={{fontSize: '12px', fontWeight: '400'}}>மீண்டும் தொடங்கவும்</span>
          </button>

          <button 
            onClick={handleSave}
            disabled={isSaving || points.length < 3 || isRecording}
            style={{
              flex: 1.5, backgroundColor: (isSaving || points.length < 3 || isRecording) ? '#d1d1d6' : '#34C759', 
              color: 'white', padding: '12px', border: 'none', borderRadius: '14px', 
              fontWeight: '600', cursor: 'pointer', fontSize: '15px', lineHeight: '1.4',
              boxShadow: (isSaving || points.length < 3 || isRecording) ? 'none' : '0 2px 8px rgba(52, 199, 89, 0.3)'
            }}
          >
            {isSaving ? "Saving..." : <>Save Area<br/><span style={{fontSize: '12px', fontWeight: '400'}}>குறித்த பகுதியை சேமிக்கவும்</span></>}
          </button>
        </div>
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
    </div>
  );
}
