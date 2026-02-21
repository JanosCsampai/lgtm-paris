"use client";

import { Slider } from "@/components/ui/slider";
import {
  DISTANCE_MIN_KM,
  DISTANCE_MAX_KM,
  DISTANCE_STEP_KM,
} from "@/lib/constants";

interface DistanceSliderProps {
  value: number;
  onChange: (km: number) => void;
}

export function DistanceSlider({ value, onChange }: DistanceSliderProps) {
  return (
    <div className="w-full max-w-[280px] space-y-2.5">
      <div className="flex items-baseline justify-between">
        <span className="text-[13px] text-muted-foreground">Max distance</span>
        <span className="text-[15px] font-semibold tabular-nums text-foreground">
          {value} km
        </span>
      </div>
      <Slider
        value={[value]}
        onValueChange={([v]) => onChange(v)}
        min={DISTANCE_MIN_KM}
        max={DISTANCE_MAX_KM}
        step={DISTANCE_STEP_KM}
        className="w-full"
      />
      <div className="flex justify-between text-[11px] text-muted-foreground/60">
        <span>{DISTANCE_MIN_KM}</span>
        <span>{DISTANCE_MAX_KM}</span>
      </div>
    </div>
  );
}
