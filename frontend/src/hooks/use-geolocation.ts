"use client";

import { useEffect, useState } from "react";
import { DEFAULT_LOCATION } from "@/lib/constants";

interface GeoState {
  lat: number;
  lng: number;
  loading: boolean;
  error: string | null;
}

export function useGeolocation() {
  const [state, setState] = useState<GeoState>({
    lat: DEFAULT_LOCATION.lat,
    lng: DEFAULT_LOCATION.lng,
    loading: true,
    error: null,
  });

  useEffect(() => {
    if (!navigator.geolocation) {
      setState((s) => ({ ...s, loading: false, error: "Geolocation not supported" }));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setState({
          lat: pos.coords.latitude,
          lng: pos.coords.longitude,
          loading: false,
          error: null,
        });
      },
      () => {
        setState((s) => ({ ...s, loading: false, error: "Permission denied" }));
      },
      { enableHighAccuracy: false, timeout: 8000 }
    );
  }, []);

  return state;
}
