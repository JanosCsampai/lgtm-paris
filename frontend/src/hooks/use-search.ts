"use client";

import { useQuery } from "@tanstack/react-query";
import { searchProviders } from "@/lib/api";
import type { SearchParams } from "@/lib/types";

export function useSearch(params: SearchParams | null) {
  return useQuery({
    queryKey: ["search", params],
    queryFn: () => searchProviders(params!),
    enabled: !!params && params.q.length > 0,
    staleTime: 1000 * 60 * 2,
    retry: 1,
    refetchInterval: (query) =>
      query.state.data?.scraping_in_progress ? 3000 : false,
  });
}
