import { CheckCircle2, Star, MapPin } from "lucide-react";

export function TrustBadges() {
  const badges = [
    { icon: CheckCircle2, label: "Transparent pricing", color: "text-[#003888]" },
    { icon: Star, label: "Real reviews", color: "text-amber-500" },
    { icon: MapPin, label: "Nearby results", color: "text-primary" },
  ];

  return (
    <div className="flex flex-wrap items-center justify-center gap-6">
      {badges.map(({ icon: Icon, label, color }) => (
        <div key={label} className="flex items-center gap-1.5 text-sm text-muted-foreground">
          <Icon className={`h-4 w-4 ${color}`} />
          <span>{label}</span>
        </div>
      ))}
    </div>
  );
}
