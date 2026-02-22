export interface GeoJSONPoint {
  type: "Point";
  coordinates: [number, number]; // [longitude, latitude]
}

export interface ObservationSummary {
  service_type: string;
  price: number;
  currency: string;
  source_type: string;
  observed_at: string;
}

export interface ProviderWithPrices {
  id: string;
  name: string;
  category: string;
  category_label: string;
  address: string;
  city: string;
  location: GeoJSONPoint;
  distance_meters: number;
  rating: number | null;
  review_count: number | null;
  description: string | null;
  website: string | null;
  observations: ObservationSummary[];
  inquiry_status: "none" | "sent" | "replied" | null;
}

export interface PriceStats {
  avg_price: number;
  min_price: number;
  max_price: number;
  median_price: number;
  currency: string;
  sample_size: number;
}

export interface MatchedServiceType {
  slug: string;
  name: string;
  match_source: "text" | "vector";
  score: number;
}

export interface SearchResponse {
  query: string;
  matched_service_types: MatchedServiceType[];
  results: ProviderWithPrices[];
  discovery_triggered: boolean;
  price_stats: PriceStats | null;
}

export interface SearchParams {
  q: string;
  lat: number;
  lng: number;
  radius_meters: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  status: "ready" | "clarifying";
  message: string;
  search_query: string | null;
}
