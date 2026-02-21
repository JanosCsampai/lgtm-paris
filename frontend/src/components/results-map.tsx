"use client";

import { useEffect, useMemo, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { ProviderWithPrices } from "@/lib/types";

function formatPrice(price: number, currency: string): string {
  const symbols: Record<string, string> = { GBP: "£", EUR: "€", USD: "$" };
  return `${symbols[currency] ?? currency}${Math.round(price)}`;
}

function getLowestPrice(p: ProviderWithPrices): string {
  if (p.observations.length === 0) return "";
  const sorted = [...p.observations].sort((a, b) => a.price - b.price);
  return formatPrice(sorted[0].price, sorted[0].currency);
}

function makePriceIcon(label: string) {
  return new L.DivIcon({
    className: "price-marker-wrapper",
    html: `<div class="price-marker">${escapeHtml(label)}</div>`,
    iconSize: [52, 22],
    iconAnchor: [26, 22],
  });
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

const userIcon = new L.DivIcon({
  className: "",
  html: `<div style="width:14px;height:14px;border-radius:50%;background:#003888;border:3px solid #fff;box-shadow:0 0 0 3px rgba(0,56,136,0.25);"></div>`,
  iconSize: [14, 14],
  iconAnchor: [7, 7],
});

const dotIcon = new L.DivIcon({
  className: "",
  html: `<div style="width:22px;height:22px;border-radius:50%;background:#E32017;border:2.5px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,0.2);"></div>`,
  iconSize: [22, 22],
  iconAnchor: [11, 11],
});

function FitBounds({
  results,
  userLat,
  userLng,
}: {
  results: ProviderWithPrices[];
  userLat: number;
  userLng: number;
}) {
  const map = useMap();

  useEffect(() => {
    if (results.length === 0) return;

    const points: [number, number][] = results.map((r) => [
      r.location.coordinates[1],
      r.location.coordinates[0],
    ]);
    points.push([userLat, userLng]);

    const bounds = L.latLngBounds(points);
    map.fitBounds(bounds, { padding: [45, 45], maxZoom: 15 });
  }, [results, userLat, userLng, map]);

  return null;
}

interface ResultsMapProps {
  results: ProviderWithPrices[];
  userLat: number;
  userLng: number;
  isLoading: boolean;
}

function ResultsMapInner({
  results,
  userLat,
  userLng,
  isLoading,
}: ResultsMapProps) {
  const mapRef = useRef<L.Map | null>(null);

  const center = useMemo<[number, number]>(() => {
    if (results.length > 0) {
      const avgLat =
        results.reduce((s, r) => s + r.location.coordinates[1], 0) /
        results.length;
      const avgLng =
        results.reduce((s, r) => s + r.location.coordinates[0], 0) /
        results.length;
      return [avgLat, avgLng];
    }
    return [userLat, userLng];
  }, [results, userLat, userLng]);

  if (isLoading) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-muted">
        <span className="text-sm text-muted-foreground">Loading map...</span>
      </div>
    );
  }

  return (
    <MapContainer
      center={center}
      zoom={13}
      className="h-full w-full"
      ref={mapRef}
      zoomControl={false}
      attributionControl={false}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/">CARTO</a>'
      />

      <Marker position={[userLat, userLng]} icon={userIcon}>
        <Popup>Your location</Popup>
      </Marker>

      {results.map((r) => {
        const price = getLowestPrice(r);
        const icon = price ? makePriceIcon(price) : dotIcon;

        return (
          <Marker
            key={r.id}
            position={[
              r.location.coordinates[1],
              r.location.coordinates[0],
            ]}
            icon={icon}
          >
            <Popup>
              <strong>{r.name}</strong>
              <br />
              <span style={{ color: "#666", fontSize: "12px" }}>
                {r.address}
              </span>
            </Popup>
          </Marker>
        );
      })}

      <FitBounds results={results} userLat={userLat} userLng={userLng} />
    </MapContainer>
  );
}

export default ResultsMapInner;
