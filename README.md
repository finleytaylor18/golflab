# GolfLab

An engineering platform for golf club design, analysis, and R&D — built to support real club fitting and performance calculations, not a consumer app or chatbot.

## Overview

GolfLab models golf clubs as structured engineering data and provides validated calculations used in real club design:

- **Swing weight** — measures how a club's mass is distributed relative to a 14-inch fulcrum point, expressed on the industry-standard Lorythmic scale (e.g. D2).
- **Moment of Inertia (MOI)** — measures a club's resistance to rotation, a key factor in how "forgiving" or head-heavy a club feels through impact.
- **Prototype comparison** — compares two saved clubs side by side, showing not just their individual results but the calculated delta between them, so a designer can see exactly what effect a design change had.

Club specifications are validated on creation and can be saved and reloaded, so prototypes persist across sessions rather than existing only for a single run.

## Features

- Typed, validated club specification model (rejects physically unrealistic inputs)
- Swing weight calculation with Lorythmic scale conversion
- Moment of Inertia calculation
- JSON-based persistence (save/load club prototypes by name)
- Prototype comparison with calculated deltas
- Command-line interface with input validation and error handling
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

These are documented, intentional simplifications for a first version — refining them with real calibration data (from actual measured clubs) is a planned future improvement.

## Tech stack

- Python 3
- pytest

## Roadmap

- [x] Swing weight calculator
- [x] Moment of Inertia calculator
- [x] Persistence (save/load club specifications)
- [x] Prototype comparison
- [ ] Center of gravity visualization
- [ ] Materials database
- [ ] Web-based interface