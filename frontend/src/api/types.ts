// Mirrors club_specification.py's ClubType exactly -- 25 specific clubs
// instead of 5 broad categories. See that file for how each range was
// derived (irons/woods/hybrids split both length and loft by number since
// both genuinely vary in real graduated sets; wedges split only by loft,
// using real 2-degree increments, since wedge length doesn't reliably
// correlate with loft the way iron length does).
export type ClubType =
  | "driver"
  | "wood_3" | "wood_5" | "wood_7"
  | "hybrid_2" | "hybrid_3" | "hybrid_4"
  | "iron_2" | "iron_3" | "iron_4" | "iron_5" | "iron_6" | "iron_7" | "iron_8" | "iron_9"
  | "wedge_46" | "wedge_48" | "wedge_50" | "wedge_52" | "wedge_54" | "wedge_56" | "wedge_58" | "wedge_60" | "wedge_62" | "wedge_64";

export const CLUB_LENGTH_RANGES: Record<ClubType, [number, number]> = {
  driver: [43.0, 48.0],
  wood_3: [42.875, 43.5],
  wood_5: [41.625, 42.875],
  wood_7: [41.0, 41.625],
  hybrid_2: [40.25, 41.0],
  hybrid_3: [38.75, 40.25],
  hybrid_4: [38.0, 38.75],
  iron_2: [38.75, 39.0],
  iron_3: [38.25, 38.75],
  iron_4: [37.75, 38.25],
  iron_5: [37.25, 37.75],
  iron_6: [36.75, 37.25],
  iron_7: [36.25, 36.75],
  iron_8: [35.75, 36.25],
  iron_9: [35.5, 35.75],
  wedge_46: [34.5, 36.5],
  wedge_48: [34.5, 36.5],
  wedge_50: [34.5, 36.5],
  wedge_52: [34.5, 36.5],
  wedge_54: [34.5, 36.5],
  wedge_56: [34.5, 36.5],
  wedge_58: [34.5, 36.5],
  wedge_60: [34.5, 36.5],
  wedge_62: [34.5, 36.5],
  wedge_64: [34.5, 36.5],
};

export const LOFT_RANGES: Record<ClubType, [number, number]> = {
  driver: [8.0, 12.0],
  wood_3: [13.0, 15.0],
  wood_5: [15.0, 19.0],
  wood_7: [19.0, 21.0],
  hybrid_2: [16.0, 19.0],
  hybrid_3: [19.0, 25.0],
  hybrid_4: [25.0, 28.0],
  iron_2: [18.0, 20.0],
  iron_3: [20.0, 24.0],
  iron_4: [24.0, 28.0],
  iron_5: [28.0, 32.0],
  iron_6: [32.0, 36.0],
  iron_7: [36.0, 40.0],
  iron_8: [40.0, 44.0],
  iron_9: [44.0, 47.0],
  wedge_46: [46.0, 47.0],
  wedge_48: [47.0, 49.0],
  wedge_50: [49.0, 51.0],
  wedge_52: [51.0, 53.0],
  wedge_54: [53.0, 55.0],
  wedge_56: [55.0, 57.0],
  wedge_58: [57.0, 59.0],
  wedge_60: [59.0, 61.0],
  wedge_62: [61.0, 63.0],
  wedge_64: [63.0, 64.0],
};

export const CLUB_TYPE_LABELS: Record<ClubType, string> = {
  driver: "Driver",
  wood_3: "3 Wood",
  wood_5: "5 Wood",
  wood_7: "7 Wood",
  hybrid_2: "2 Hybrid",
  hybrid_3: "3 Hybrid",
  hybrid_4: "4 Hybrid",
  iron_2: "2 Iron",
  iron_3: "3 Iron",
  iron_4: "4 Iron",
  iron_5: "5 Iron",
  iron_6: "6 Iron",
  iron_7: "7 Iron",
  iron_8: "8 Iron",
  iron_9: "9 Iron",
  wedge_46: "46° Wedge",
  wedge_48: "48° Wedge",
  wedge_50: "50° Wedge",
  wedge_52: "52° Wedge",
  wedge_54: "54° Wedge",
  wedge_56: "56° Wedge",
  wedge_58: "58° Wedge",
  wedge_60: "60° Wedge",
  wedge_62: "62° Wedge",
  wedge_64: "64° Wedge",
};

export const CLUB_TYPE_CATEGORIES: Record<string, ClubType[]> = {
  Driver: ["driver"],
  Wood: ["wood_3", "wood_5", "wood_7"],
  Hybrid: ["hybrid_2", "hybrid_3", "hybrid_4"],
  Iron: ["iron_2", "iron_3", "iron_4", "iron_5", "iron_6", "iron_7", "iron_8", "iron_9"],
  Wedge: ["wedge_46", "wedge_48", "wedge_50", "wedge_52", "wedge_54", "wedge_56", "wedge_58", "wedge_60", "wedge_62", "wedge_64"],
};

export interface ClubSpecification {
  club_type: ClubType;
  head_mass: number;
  shaft_mass: number;
  shaft_length: number;
  grip_mass: number;
  club_length: number;
  loft: number;
  lie_angle: number;
}

export interface SwingProfile {
  clubhead_speed: number;
  attack_angle: number;
  swing_path: number;
  face_angle: number;
  dynamic_loft: number;
}

export interface SwingWeightResult {
  moment: number;
  swing_weight: string;
}

export interface MoiResult {
  moi: number;
}

export interface BalancePointResult {
  balance_point: number;
}

export interface LaunchConditions {
  ball_speed: number;
  launch_angle: number;
  launch_direction: number;
  backspin: number;
  sidespin: number;
  effective_deloft: number;
}

export interface TrajectoryResult {
  points: [number, number, number][];
  carry_distance: number;
  peak_height: number;
  lateral_deviation: number;
  shot_shape: string;
}

export interface BallFlightResult {
  launch_conditions: LaunchConditions;
  trajectory: TrajectoryResult;
}

export const DEFAULT_CLUB: ClubSpecification = {
  club_type: "driver",
  head_mass: 200,
  shaft_mass: 65,
  shaft_length: 45.5,
  grip_mass: 50,
  club_length: 45.5,
  loft: 10.5,
  lie_angle: 58,
};

export const DEFAULT_SWING: SwingProfile = {
  clubhead_speed: 110,
  attack_angle: 2,
  swing_path: 1,
  face_angle: 0.5,
  dynamic_loft: 13,
};

// ---------------------------------------------------------------------------
// IMPACT MODEL AND FORGIVENESS MAPS
// ---------------------------------------------------------------------------
//
// Every field is in industry units, matching api_schemas.py. The physics core
// is SI and converts at the boundary, so nothing here is ever in kg or metres.
//
// Sign conventions, which are easy to get backwards and expensive to get
// wrong (see head_mass_properties.py):
//   +x is toward the HEEL, so a toe strike is negative x
//   +y is toward the crown
//   cg_z is NEGATIVE -- the centre of mass lies behind the face plane

export interface HeadMassProperties {
  mass_g: number;
  cg_x_mm: number;
  cg_y_mm: number;
  cg_z_mm: number;
  i_xx_g_cm2: number;
  i_yy_g_cm2: number;
  i_zz_g_cm2: number;
  i_xy_g_cm2: number;
  i_xz_g_cm2: number;
  i_yz_g_cm2: number;
  face_half_width_mm: number;
  face_half_height_mm: number;
  face_shape: "ellipse" | "rectangle";
  face_outline_is_measured: boolean;
}

export interface ImpactConditions {
  clubhead_speed_mph: number;
  loft_deg: number;
}

export interface MapSettings {
  spacing_mm: number;
  retention_threshold_pct: number;
}

export interface ConformanceReport {
  rules_frame_moi_g_cm2: number;
  limit_g_cm2: number;
  limit_with_tolerance_g_cm2: number;
  conforms: boolean;
  citation: string;
}

export interface MapSummary {
  threshold_pct: number;
  threshold_is_a_chosen_setting: boolean;
  forgiving_area_mm2: number;
  face_area_mm2: number;
  forgiving_area_fraction: number;
  sweet_spot_ball_speed_mph: number;
  worst_retention_pct: number;
  max_abs_sidespin_rpm: number;
  backspin_range_rpm: [number, number];
  points_needing_more_friction: number;
  points_with_reversed_backspin: number;
  face_description: string;
}

// Null marks a grid point outside the face outline. JSON has no NaN, so the
// backend converts it (see api_schemas._grid_to_json).
export type Grid = (number | null)[][];

export interface ForgivenessMapResult {
  x_mm: number[];
  y_mm: number[];
  on_face: boolean[][];
  ball_speed_mph: Grid;
  speed_retention_pct: Grid;
  backspin_rpm: Grid;
  sidespin_rpm: Grid;
  spin_axis_deg: Grid;
  launch_angle_deg: Grid;
  required_friction: Grid;
  exceeds_friction: boolean[][];
  backspin_reversed: boolean[][];
  sweet_spot_mm: [number, number];
  face_centre_mm: [number, number];
  summary: MapSummary;
  head_description: string;
  ball_description: string;
  conditions_description: string;
  face_description: string;
  conformance: ConformanceReport;
}

export interface MapComparisonResult {
  name_a: string;
  name_b: string;
  x_mm: number[];
  y_mm: number[];
  on_face: boolean[][];
  delta_speed_retention_pct: Grid;
  delta_ball_speed_mph: Grid;
  delta_backspin_rpm: Grid;
  delta_sidespin_rpm: Grid;
  delta_launch_angle_deg: Grid;
  summary_a: MapSummary;
  summary_b: MapSummary;
}

export interface ImpactResult {
  launch: {
    ball_speed_mph: number;
    launch_angle_deg: number;
    horizontal_launch_deg: number;
    backspin_rpm: number;
    sidespin_rpm: number;
    smash_factor: number;
    effective_mass_g: number;
    contact: string;
    required_friction: number;
    energy_lost_j: number;
  };
  on_face: boolean;
  conformance: ConformanceReport;
  ball_description: string;
}

// A plausible driver head, used only to populate the form so the panel opens
// on something that runs. NOT a real product and never presented as one --
// the numbers are round because they are invented.
export const DEFAULT_HEAD: HeadMassProperties = {
  mass_g: 200,
  cg_x_mm: 0,
  cg_y_mm: 0,
  cg_z_mm: -35,
  i_xx_g_cm2: 3000,
  i_yy_g_cm2: 5000,
  i_zz_g_cm2: 4000,
  i_xy_g_cm2: 0,
  i_xz_g_cm2: 0,
  i_yz_g_cm2: 0,
  face_half_width_mm: 50,
  face_half_height_mm: 30,
  face_shape: "ellipse",
  face_outline_is_measured: false,
};

export const DEFAULT_MAP_SETTINGS: MapSettings = {
  spacing_mm: 2,
  retention_threshold_pct: 97,
};
