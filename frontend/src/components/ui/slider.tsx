"use client"

import * as React from "react"
import { Slider as SliderPrimitive } from "radix-ui"

import { cn } from "@/lib/utils"

function Slider({
  className,
  defaultValue,
  value,
  min = 0,
  max = 100,
  ...props
}: React.ComponentProps<typeof SliderPrimitive.Root>) {
  const _values = React.useMemo(
    () =>
      Array.isArray(value)
        ? value
        : Array.isArray(defaultValue)
          ? defaultValue
          : [min, max],
    [value, defaultValue, min, max]
  )

  return (
    <SliderPrimitive.Root
      data-slot="slider"
      defaultValue={defaultValue}
      value={value}
      min={min}
      max={max}
      className={cn(
        "relative flex w-full touch-none items-center select-none data-[disabled]:opacity-50 data-[orientation=vertical]:h-full data-[orientation=vertical]:min-h-44 data-[orientation=vertical]:w-auto data-[orientation=vertical]:flex-col",
        className
      )}
      {...props}
    >
      <SliderPrimitive.Track
        data-slot="slider-track"
        className={cn(
          "bg-muted relative grow overflow-hidden rounded-full data-[orientation=horizontal]:h-1.5 data-[orientation=horizontal]:w-full data-[orientation=vertical]:h-full data-[orientation=vertical]:w-1.5"
        )}
      >
        <SliderPrimitive.Range
          data-slot="slider-range"
          className={cn(
            "bg-primary absolute data-[orientation=horizontal]:h-full data-[orientation=vertical]:w-full"
          )}
        />
      </SliderPrimitive.Track>
      {Array.from({ length: _values.length }, (_, index) => (
        <SliderPrimitive.Thumb
          data-slot="slider-thumb"
          key={index}
          className="group/thumb relative flex items-center justify-center shrink-0 outline-hidden disabled:pointer-events-none disabled:opacity-50 cursor-grab active:cursor-grabbing"
          style={{ width: 24, height: 26, background: "transparent", boxShadow: "none" }}
        >
          <svg viewBox="150 444 168 178" width="24" height="26" aria-hidden="true" className="transition-transform duration-150 group-hover/thumb:scale-125 group-active/thumb:scale-110">
            <defs>
              <filter id="plum-shadow">
                <feDropShadow dx="0" dy="1" stdDeviation="2" floodOpacity="0.3"/>
              </filter>
            </defs>
            <path fill="#5C2553" fillRule="evenodd" filter="url(#plum-shadow)" d="M280.232422,597.282959 C250.624481,619.293701 214.702332,616.599182 188.795685,590.658813 C158.209869,560.033203 154.965317,504.832520 181.831039,470.909668 C188.668915,462.275574 196.991302,455.539764 207.492767,451.697235 C213.943008,449.337097 220.689804,448.742920 227.177490,450.122101 C234.720261,451.725555 241.820160,451.267059 249.335159,449.959778 C266.824432,446.917236 280.677856,454.523346 291.600098,467.346527 C309.264771,488.085541 314.788025,512.558960 311.653473,539.235229 C308.909149,562.590576 298.761078,582.026550 280.232422,597.282959 M209.151825,467.767670 C190.460205,477.158051 175.600113,509.913300 185.687454,523.331421 C190.511826,502.255615 200.524918,484.903595 213.735413,469.315247 C214.241257,468.718384 214.518616,467.842133 213.956268,466.910950 C212.469620,465.912384 211.201202,467.278534 209.151825,467.767670z"/>
          </svg>
        </SliderPrimitive.Thumb>
      ))}
    </SliderPrimitive.Root>
  )
}

export { Slider }
