import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default Leaflet markers in React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Helper component to recenter map when pharmacies change
const ChangeView = ({ center, zoom }) => {
    const map = useMap();
    useEffect(() => {
        map.flyTo(center, zoom, {
            duration: 1.5
        });
    }, [center, zoom, map]);
    return null;
};

const customMarkerIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

const userMarkerIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

export default function MapComponent({ pharmacies, userLocation }) {
    const defaultCenter = [11.0168, 76.9558]; // Coimbatore fallback

    // Prioritize pharmacy location if available, else user location, else default
    const center = pharmacies && pharmacies.length > 0
        ? [pharmacies[0].lat, pharmacies[0].lon]
        : (userLocation ? [userLocation.lat, userLocation.lon] : defaultCenter);

    return (
        <div style={{ height: '100%', width: '100%', borderRadius: '1.5rem', overflow: 'hidden' }}>
            <MapContainer
                center={center}
                zoom={14}
                scrollWheelZoom={false}
                style={{ height: '100%', width: '100%' }}
            >
                <ChangeView center={center} zoom={14} />
                <TileLayer
                    url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                />

                {/* User Location Marker */}
                {userLocation && (
                    <Marker position={[userLocation.lat, userLocation.lon]} icon={userMarkerIcon}>
                        <Popup>
                            <div className="text-xs font-bold">You are here</div>
                        </Popup>
                    </Marker>
                )}

                {/* Pharmacies Markers */}
                {pharmacies && pharmacies.map((pharmacy, idx) => {
                    if (!pharmacy.lat || !pharmacy.lon) return null;
                    return (
                        <Marker
                            key={idx}
                            position={[pharmacy.lat, pharmacy.lon]}
                            icon={customMarkerIcon}
                        >
                            <Popup>
                                <div className="flex flex-col gap-1">
                                    <strong className="text-sm">{pharmacy.name}</strong>
                                    <span className="text-xs text-medic-600 font-bold">{pharmacy.stock}</span>
                                    <span className="text-[10px] text-slate-500">{pharmacy.distance} away</span>
                                    <a
                                        href={`https://www.google.com/maps/dir/?api=1&origin=${userLocation?.lat},${userLocation?.lon}&destination=${pharmacy.lat},${pharmacy.lon}`}
                                        target="_blank"
                                        rel="noreferrer"
                                        className="text-xs text-blue-500 font-bold hover:underline mt-1 flex items-center gap-1"
                                    >
                                        Directions →
                                    </a>
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>
        </div>
    );
}
