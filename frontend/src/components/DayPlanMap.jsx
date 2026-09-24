import React, { useMemo, useState, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

/**
 * DayPlanMap - shows the rep's location and the planned visit order on an
 * OpenStreetMap tile map (free, no API key), with a line connecting the
 * stops in visiting sequence.
 *
 * Live tracking: watches the browser's GPS (navigator.geolocation.
 * watchPosition) and moves the "You" marker as the rep's real position
 * changes, all on this same screen - no redirect to another app/tab. This
 * gives an in-app "live map" feel similar to what a driver sees in Uber's
 * own screen, but it's honestly NOT full turn-by-turn navigation: there
 * are no voice directions and no automatic re-routing if the rep takes a
 * different road - that needs a paid, much more complex routing/navigation
 * engine. The "Navigate" button (Google Maps deep link) remains the way to
 * get real turn-by-turn directions when the rep actually starts driving.
 *
 * Uses plain Leaflet divIcons instead of the default marker images,
 * because Leaflet's default marker icon path breaks under most bundlers
 * (Vite/webpack) unless manually reconfigured - a numbered divIcon avoids
 * that entirely and also doubles as the stop's rank label.
 */
const buildDivIcon = (label, background, pulse = false) =>
  L.divIcon({
    html: `<div style="
      display:flex;align-items:center;justify-content:center;
      width:30px;height:30px;border-radius:50%;
      background:${background};color:#fff;font-weight:700;font-size:13px;
      border:2px solid #ffffff;box-shadow:0 2px 6px rgba(15,23,42,0.35);
      ${pulse ? 'animation: dayPlanPulse 1.6s ease-in-out infinite;' : ''}
    ">${label}</div>
    ${pulse ? `<style>
      @keyframes dayPlanPulse {
        0% { box-shadow: 0 0 0 0 rgba(37,99,235,0.5), 0 2px 6px rgba(15,23,42,0.35); }
        70% { box-shadow: 0 0 0 12px rgba(37,99,235,0), 0 2px 6px rgba(15,23,42,0.35); }
        100% { box-shadow: 0 0 0 0 rgba(37,99,235,0), 0 2px 6px rgba(15,23,42,0.35); }
      }
    </style>` : ''}`,
    className: '',
    iconSize: [30, 30],
    iconAnchor: [15, 15],
    popupAnchor: [0, -15],
  });

const STOP_ICON_COLOR = '#7c3aed';

export const DayPlanMap = ({ repLocation, stops }) => {
  const [liveLocation, setLiveLocation] = useState(repLocation);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    if (!navigator.geolocation) return undefined;

    const watchId = navigator.geolocation.watchPosition(
      (position) => {
        setLiveLocation({
          latitude: position.coords.latitude,
          longitude: position.coords.longitude,
        });
        setIsLive(true);
      },
      () => setIsLive(false),
      { enableHighAccuracy: true, maximumAge: 5000, timeout: 10000 }
    );

    return () => navigator.geolocation.clearWatch(watchId);
  }, []);

  // The planned route line is fixed to where the rep started when the
  // plan was generated (so it doesn't jump around as they move) - only
  // the "You" marker itself tracks their live position.
  const routePoints = useMemo(() => {
    const pts = [[repLocation.latitude, repLocation.longitude]];
    stops.forEach((s) => pts.push([s.latitude, s.longitude]));
    return pts;
  }, [repLocation, stops]);

  const bounds = useMemo(() => {
    if (routePoints.length === 1) return null;
    return L.latLngBounds(routePoints);
  }, [routePoints]);

  const repIcon = useMemo(() => buildDivIcon('You', '#2563eb', isLive), [isLive]);

  return (
    <div style={{ height: '320px', borderRadius: '12px', overflow: 'hidden', border: '1px solid #e2e8f0' }}>
      <MapContainer
        center={[repLocation.latitude, repLocation.longitude]}
        zoom={12}
        bounds={bounds || undefined}
        boundsOptions={{ padding: [30, 30] }}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <Marker position={[liveLocation.latitude, liveLocation.longitude]} icon={repIcon}>
          <Popup>{isLive ? 'Your live location' : 'Your location'}</Popup>
        </Marker>

        {stops.map((stop, index) => (
          <Marker
            key={stop.hcp_id}
            position={[stop.latitude, stop.longitude]}
            icon={buildDivIcon(index + 1, STOP_ICON_COLOR)}
          >
            <Popup>
              <strong>{stop.name}</strong>
              {stop.specialty && <div>{stop.specialty}</div>}
              <div>Priority {Math.round(stop.priority_score ?? 0)}</div>
            </Popup>
          </Marker>
        ))}

        {routePoints.length > 1 && (
          <Polyline positions={routePoints} pathOptions={{ color: '#7c3aed', weight: 3, opacity: 0.7, dashArray: '6 6' }} />
        )}
      </MapContainer>
    </div>
  );
};

export default DayPlanMap;