import type { ClubSpecification, ClubType } from "../api/types";
import { CLUB_TYPE_CATEGORIES, CLUB_TYPE_LABELS, CLUB_LENGTH_RANGES, LOFT_RANGES } from "../api/types";
import { NumberField } from "./NumberField";

interface Props {
  value: ClubSpecification;
  onChange: (club: ClubSpecification) => void;
}

function median([min, max]: [number, number]): number {
  return Math.round(((min + max) / 2) * 10) / 10;
}

export function ClubSpecForm({ value, onChange }: Props) {
  function setField<K extends keyof ClubSpecification>(key: K, fieldValue: ClubSpecification[K]) {
    onChange({ ...value, [key]: fieldValue });
  }

  // club_length and loft are the only fields with a real type-specific valid
  // range in the domain model (CLUB_LENGTH_RANGES/LOFT_RANGES), so switching
  // type resets those two to the middle of the new range -- a value that's
  // always valid without the user having to look up what's realistic for a
  // wedge vs. a driver. shaft_length rides along with club_length since the
  // two are treated as equal everywhere else in this model. head_mass,
  // shaft_mass, grip_mass, and lie_angle don't change: they share one global
  // range that isn't type-specific, so there's no "median for this type" to
  // reset them to.
  function handleClubTypeChange(club_type: ClubType) {
    const club_length = median(CLUB_LENGTH_RANGES[club_type]);
    const loft = median(LOFT_RANGES[club_type]);
    onChange({ ...value, club_type, club_length, loft, shaft_length: club_length });
  }

  return (
    <div className="panel panel--spec">
      <h2>Club specification</h2>
      <div className="field-grid">
        <label className="field">
          <span>Club type</span>
          <select
            value={value.club_type}
            onChange={(event) => handleClubTypeChange(event.target.value as ClubType)}
          >
            {Object.entries(CLUB_TYPE_CATEGORIES).map(([category, types]) => (
              <optgroup key={category} label={category}>
                {types.map((type) => (
                  <option key={type} value={type}>
                    {CLUB_TYPE_LABELS[type]}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
        </label>
        <NumberField label="Club length" unit="in" step={0.1} value={value.club_length} onChange={(v) => setField("club_length", v)} />
        <NumberField label="Loft" unit="deg" step={0.1} value={value.loft} onChange={(v) => setField("loft", v)} />
        <NumberField label="Lie angle" unit="deg" step={0.1} value={value.lie_angle} onChange={(v) => setField("lie_angle", v)} />
        <NumberField label="Head mass" unit="g" value={value.head_mass} onChange={(v) => setField("head_mass", v)} />
        <NumberField label="Shaft mass" unit="g" value={value.shaft_mass} onChange={(v) => setField("shaft_mass", v)} />
        <NumberField label="Shaft length" unit="in" step={0.1} value={value.shaft_length} onChange={(v) => setField("shaft_length", v)} />
        <NumberField label="Grip mass" unit="g" value={value.grip_mass} onChange={(v) => setField("grip_mass", v)} />
      </div>
    </div>
  );
}
