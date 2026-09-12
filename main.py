from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from club_specification import ClubSpecification
from swing_weight import calculate_moment, moment_to_swing_weight
from moment_of_inertia import calculate_moi
from center_of_gravity import calculate_balance_point
from club_comparison import compare_clubs
from club_repository import save_club, load_club, list_club_names
from clubhead_composition import calculate_head_cg
from ball_flight import calculate_launch_conditions, simulate_trajectory
from ball_properties import conforming_three_piece_tour_ball
from head_mass_properties import strike_from_toe_crown_mm
from head_repository import save_head, load_head, list_head_names
from impact_model import solve_impact
from forgiveness_map import compute_forgiveness_map, compare_maps
from api_schemas import (
    ClubSpecificationRequest, to_club_specification,
    to_swing_profile,
    ClubHeadCompositionRequest, to_clubhead_composition,
    CompareRequest, BallFlightRequest, SaveClubRequest,
    HeadMassPropertiesRequest, to_head_mass_properties,
    to_swing_conditions, to_map_settings,
    ImpactRequest, ForgivenessMapRequest, ForgivenessCompareRequest, SaveHeadRequest,
    forgiveness_map_to_payload, map_comparison_to_payload, head_to_request_payload,
)

app = FastAPI(title="GolfLab API")


def _build_club(request: ClubSpecificationRequest) -> ClubSpecification:
    try:
        return to_club_specification(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


@app.post("/calculations/swing-weight")
def swing_weight_endpoint(request: ClubSpecificationRequest):
    club = _build_club(request)
    moment = calculate_moment(club)
    return {"moment": moment, "swing_weight": moment_to_swing_weight(moment)}


@app.post("/calculations/moi")
def moi_endpoint(request: ClubSpecificationRequest):
    club = _build_club(request)
    return {"moi": calculate_moi(club)}


@app.post("/calculations/balance-point")
def balance_point_endpoint(request: ClubSpecificationRequest):
    club = _build_club(request)
    return {"balance_point": calculate_balance_point(club)}


@app.post("/calculations/compare")
def compare_endpoint(request: CompareRequest):
    club_a = _build_club(request.club_a)
    club_b = _build_club(request.club_b)
    return compare_clubs(request.name_a, club_a, request.name_b, club_b)


@app.post("/calculations/ball-flight")
def ball_flight_endpoint(request: BallFlightRequest):
    club = _build_club(request.club)
    try:
        swing = to_swing_profile(request.swing)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    launch = calculate_launch_conditions(club, swing)
    trajectory = simulate_trajectory(club, swing)
    return {"launch_conditions": launch, "trajectory": trajectory}


@app.post("/calculations/clubhead-cg")
def clubhead_cg_endpoint(request: ClubHeadCompositionRequest):
    try:
        composition = to_clubhead_composition(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    toe_heel, face_back = calculate_head_cg(composition)
    return {"toe_heel": toe_heel, "face_back": face_back}


@app.post("/clubs", status_code=201)
def save_club_endpoint(request: SaveClubRequest):
    club = _build_club(request.club)
    save_club(request.name, club)
    return {"name": request.name}


@app.get("/clubs")
def list_clubs_endpoint():
    return list_club_names()


@app.get("/clubs/{name}")
def load_club_endpoint(name: str):
    try:
        return load_club(name)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))


# ---------------------------------------------------------------------------
# IMPACT MODEL AND FORGIVENESS MAPS
# ---------------------------------------------------------------------------


def _build_head(request: HeadMassPropertiesRequest):
    """Validate a head at the API boundary.

    Every domain rule -- symmetric tensor, positive-definite, triangle
    inequality, CG behind the face -- raises ValueError, and each one means
    the client sent something that describes no real object. 422 is the right
    answer: the request was well-formed JSON but not a clubhead.
    """
    try:
        return to_head_mass_properties(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


def _build_conditions(request):
    try:
        return to_swing_conditions(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


def _build_settings(request):
    try:
        return to_map_settings(request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))


@app.post("/calculations/impact")
def impact_endpoint(request: ImpactRequest):
    """One strike, in launch-monitor terms."""
    head = _build_head(request.head)
    conditions = _build_conditions(request.conditions)
    ball = conforming_three_piece_tour_ball()

    strike = strike_from_toe_crown_mm(request.strike_toe_mm, request.strike_crown_mm)
    try:
        result = solve_impact(head, ball, conditions, strike)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    return {
        "launch": result.to_display(conditions.head_speed_mps),
        "on_face": head.face.contains(strike[0], strike[1]),
        "conformance": head.conformance_report(),
        "ball_description": ball.description,
    }


@app.post("/calculations/forgiveness-map")
def forgiveness_map_endpoint(request: ForgivenessMapRequest):
    head = _build_head(request.head)
    conditions = _build_conditions(request.conditions)
    settings = _build_settings(request.settings)

    try:
        fmap = compute_forgiveness_map(head, conforming_three_piece_tour_ball(),
                                       conditions, settings)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    payload = forgiveness_map_to_payload(fmap)
    payload["conformance"] = head.conformance_report()
    return payload


@app.post("/calculations/forgiveness-compare")
def forgiveness_compare_endpoint(request: ForgivenessCompareRequest):
    head_a = _build_head(request.head_a)
    head_b = _build_head(request.head_b)
    conditions = _build_conditions(request.conditions)
    settings = _build_settings(request.settings)
    ball = conforming_three_piece_tour_ball()

    try:
        map_a = compute_forgiveness_map(head_a, ball, conditions, settings)
        map_b = compute_forgiveness_map(head_b, ball, conditions, settings)
        comparison = compare_maps(request.name_a, map_a, request.name_b, map_b)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))

    return map_comparison_to_payload(comparison)


@app.post("/heads", status_code=201)
def save_head_endpoint(request: SaveHeadRequest):
    head = _build_head(request.head)
    save_head(request.name, head)
    return {"name": request.name}


@app.get("/heads")
def list_heads_endpoint():
    return list_head_names()


@app.get("/heads/{name}")
def load_head_endpoint(name: str):
    try:
        return head_to_request_payload(load_head(name))
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error))
    except ValueError as error:
        # A hand-edited heads.json can hold a tensor that no longer validates.
        raise HTTPException(status_code=422, detail=str(error))


# Serves the built frontend (frontend/dist, from `npm run build`) so the
# whole app runs from this one process/port instead of needing a separate
# Vite server. Mounted last and deliberately at "/" -- every API route above
# is registered on app.router before this, and Starlette matches routes in
# registration order, so /calculations/* and /clubs* are handled by their
# explicit handlers first and everything else falls through to static files.
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
