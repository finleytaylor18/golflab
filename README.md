# GolfLab

An engineering platform for golf club design, analysis, and R&D — built to support real club fitting and performance calculations, not a consumer app or chatbot.

## Overview

GolfLab models golf clubs as structured engineering data and provides validated calculations used in real club design:

- **Swing weight** — measures how a club's mass is distributed relative to a 14-inch fulcrum point, expressed on the industry-standard Lorythmic scale (e.g. D2).
- **Moment of Inertia (MOI)** — measures a club's resistance to rotation, a key factor in how "forgiving" or head-heavy a club feels through impact.
- **Center of gravity / club diagram** — computes the club's overall balance point along its length and renders a 1D positional diagram of the grip, shaft, head, and balance point.
- **Clubhead weight distribution** — models a clubhead as several discrete weight ports (e.g. toe, heel, back) at 2D positions within the head, computes the head's own local center of gravity, and renders a 2D diagram — similar in spirit to perimeter-weighting / movable-weight-system design.
- **Ball flight prediction** — combines a club specification and a player's swing profile (clubhead speed, attack angle, swing path, face angle, dynamic loft) into launch conditions and a numerically simulated trajectory (carry distance, peak height, lateral deviation, shot shape).
- **Prototype comparison** — compares two saved clubs side by side, showing not just their individual results but the calculated delta between them, so a designer can see exactly what effect a design change had.

Club specifications are validated on creation, type-specific (a driver-length shaft is rejected for a wedge), and can be saved and reloaded, so prototypes persist across sessions rather than existing only for a single run.

## Features

- Typed, validated club specification model with per-club-type length and loft ranges (driver/wood/hybrid/iron/wedge)
- Swing weight calculation with Lorythmic scale conversion
- Moment of Inertia calculation
- Center of gravity calculation with 1D matplotlib diagram
- Clubhead weight-distribution modeling with 2D matplotlib diagram
- Ball flight prediction: launch conditions and a drag/lift-simulated trajectory
- JSON-based persistence (save/load club prototypes by name)
- Prototype comparison with calculated deltas
- Command-line interface with input validation and error handling
- FastAPI backend exposing every calculation and persistence operation as an HTTP endpoint
- Full pytest test coverage, including isolated tests for file-based persistence

## Getting started

```bash
git clone https://github.com/finleytaylor18/golflab.git
cd golflab
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 cli.py
```

## Running the API

```bash
uvicorn main:app --reload --port 8000
```

Then open `http://localhost:8000/docs` for interactive API documentation (Swagger UI) — every endpoint can be tried directly from the browser without a frontend. See `main.py` for the full endpoint list (calculations under `/calculations/*`, persistence under `/clubs`).

## Running tests

```bash
pytest
```

## Engineering assumptions and known limitations

This is a v1 model, and its assumptions are documented deliberately rather than hidden:

- **Shaft mass** is modeled as a point mass at the shaft's midpoint, assuming uniform mass distribution. Real shafts taper, so this is an approximation.
- **Clubhead position** is modeled at the full club length from the butt end, without accounting for the head's actual center of gravity inset. This tends to make swing weight estimates run somewhat higher than a physically measured club.
- **Grip center of mass** is assumed to sit 5 inches from the butt end for all clubs.
- Swing weight conversion constants (A0 reference point, points-per-increment) were calibrated against publicly available reference examples, not an official manufacturer specification.
- **Mass validation ranges** (`MIN_MASS`/`MAX_MASS`) are global across all club types; club length ranges are type-specific but mass ranges are not yet.
- **Clubhead weight ports** are modeled independently of `ClubSpecification` — a weight-port composition is not persisted alongside a saved club, and its individual port masses are not currently checked against the club's overall `head_mass`.
- **Ball flight aerodynamic constants** (drag coefficient, lift-coefficient-vs-spin-ratio slope, smash factor curve, spin rate model) are simplified, physically-motivated approximations, not manufacturer or peer-reviewed aerodynamic data — see the comments in `ball_flight.py` for what each constant represents and how it was calibrated.
- **`SwingProfile.dynamic_loft`** is an independent input (the loft actually presented to the ball at impact), not derived from the club's static `loft` — this lets a player's shaft-lean/delofting be modeled without assuming a fixed relationship between the two.

These are documented, intentional simplifications for a first version — refining them with real calibration data (from actual measured clubs) is a planned future improvement.

## Tech stack

- Python 3
- pytest
- matplotlib
- FastAPI / uvicorn

## Roadmap

- [x] Swing weight calculator
- [x] Moment of Inertia calculator
- [x] Persistence (save/load club specifications)
- [x] Prototype comparison
- [x] Center of gravity visualization
- [x] Club type customization with type-specific validation
- [x] Clubhead weight-distribution modeling
- [x] Ball flight prediction
- [x] FastAPI backend
- [ ] React frontend
- [ ] 3D club visualization
- [ ] Materials database