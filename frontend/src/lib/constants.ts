export const DEFAULT_LOCATION = {
  lat: 51.5074,
  lng: -0.1278,
  label: "London",
};

export const DISTANCE_MIN_KM = 0.5;
export const DISTANCE_MAX_KM = 20;
export const DISTANCE_DEFAULT_KM = 5;
export const DISTANCE_STEP_KM = 0.5;

export const SUGGESTION_CHIPS = [
  "Screen repair under £100",
  "Battery replacement near me",
  "iPhone repair today",
  "Cheapest phone fix nearby",
];

// Tube line colours used as category swatches
export const CATEGORY_SWATCHES: Record<string, string> = {
  phone_repair: "#E32017",   // Central line
  mechanic:     "#003688",   // Piccadilly line
  electrician:  "#00782A",   // District line
};
