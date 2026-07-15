from dataclasses import dataclass


@dataclass
class WeightPort:
    name: str
    mass: float        # grams
    toe_heel: float     # inches from head center; positive = toe, negative = heel
    face_back: float    # inches from head center; positive = back, negative = face

    def __post_init__(self):
        if self.mass <= 0:
            raise ValueError(f"mass {self.mass} must be positive")


@dataclass
class ClubHeadComposition:
    weight_ports: list[WeightPort]

    def __post_init__(self):
        if not self.weight_ports:
            raise ValueError("a club head composition needs at least one weight port")


def calculate_head_cg(composition: ClubHeadComposition) -> tuple[float, float]:
    total_mass = sum(port.mass for port in composition.weight_ports)

    toe_heel_moment = sum(port.mass * port.toe_heel for port in composition.weight_ports)
    face_back_moment = sum(port.mass * port.face_back for port in composition.weight_ports)

    return (toe_heel_moment / total_mass, face_back_moment / total_mass)


if __name__ == "__main__":
    driver_head = ClubHeadComposition(weight_ports=[
        WeightPort(name="Heel port", mass=8.0, toe_heel=-1.1, face_back=-0.3),
        WeightPort(name="Toe port", mass=6.0, toe_heel=1.2, face_back=-0.2),
        WeightPort(name="Back port", mass=10.0, toe_heel=0.0, face_back=1.3),
    ])
    cg = calculate_head_cg(driver_head)
    print(f"Head CG: toe/heel {cg[0]:.3f}\", face/back {cg[1]:.3f}\"")
