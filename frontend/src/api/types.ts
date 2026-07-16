export type ClubType = "driver" | "wood" | "hybrid" | "iron" | "wedge";

export const CLUB_TYPES: ClubType[] = ["driver", "wood", "hybrid", "iron", "wedge"];

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
