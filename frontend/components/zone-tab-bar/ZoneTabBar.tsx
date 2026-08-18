export interface Zone {
  id: string;
  label: string;
}

// Backend zone keys (see backend/app/core/zones.py) don't match the display
// labels 1:1 — "china" vs "CN" — so keep the mapping explicit here rather
// than deriving one from the other.
export const ZONES: Zone[] = [
  { id: "us", label: "US" },
  { id: "eu", label: "EU" },
  { id: "china", label: "CN" },
];

interface ZoneTabBarProps {
  activeZone: string;
  onZoneChange: (zone: string) => void;
}

export function ZoneTabBar({ activeZone, onZoneChange }: ZoneTabBarProps) {
  return (
    <div
      role="tablist"
      aria-label="Zone"
      className="flex w-full gap-1 rounded-full border border-white/10 bg-white/5 p-1"
    >
      {ZONES.map((zone) => {
        const isActive = zone.id === activeZone;
        return (
          <button
            key={zone.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onZoneChange(zone.id)}
            className={`flex-1 cursor-pointer rounded-full px-4 py-2 text-sm font-medium transition-colors ${
              isActive
                ? "bg-blue-500/20 text-blue-400 backdrop-blur-sm"
                : "text-white/40 hover:text-white/60"
            }`}
          >
            {zone.label}
          </button>
        );
      })}
    </div>
  );
}
