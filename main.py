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
from api_schemas import (
    ClubSpecificationRequest, to_club_specification,
    to_swing_profile,
    ClubHeadCompositionRequest, to_clubhead_composition,
    CompareRequest, BallFlightRequest, SaveClubRequest,
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


# Serves the built frontend (frontend/dist, from `npm run build`) so the
# whole app runs from this one process/port instead of needing a separate
# Vite server. Mounted last and deliberately at "/" -- every API route above
# is registered on app.router before this, and Starlette matches routes in
# registration order, so /calculations/* and /clubs* are handled by their
# explicit handlers first and everything else falls through to static files.
FRONTEND_DIST = Path(__file__).parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
