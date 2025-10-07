"""Example of using geometric subprogram to optimize H2 bond length.

Constraints docs: https://geometric.readthedocs.io/en/latest/constraints.html
"""

from qcio import CompositeCalcSpec, Structure

from qcop import compute, exceptions

# Create Structure
h2 = Structure(
    symbols=["H", "H"],
    geometry=[[0, 0.0, 0.0], [0, 0, 1.4]],  # type: ignore
)

# Define the calcspec
spec = CompositeCalcSpec(
    calctype="optimization",  # type: ignore
    structure=h2,
    subprogram="terachem",
    subprogram_spec={  # type: ignore
        "model": {"method": "HF", "basis": "6-31g"},
        "keywords": {"purify": "no"},
    },
    keywords={
        "check": 3,
        # This is obviously a stupid constraint, but it's just an example to show how
        # to use them
        "constraints": {
            "freeze": [
                {"type": "distance", "indices": [0, 1], "value": 1.4},
            ],
        },
    },
)

# Run calculation
try:
    results = compute("geometric", spec, propagate_wfn=True, rm_scratch_dir=False)
except exceptions.QCOPBaseError as e:
    # Calculation failed
    results = e.results
    print(results.logs)
    # Input data used to generate the calculation
    print(results.input_data)
    # Provenance of generated calculation
    print(results.provenance)
    print(results.traceback)
    raise

else:
    # Check results
    print("Energies:", results.data.energies)
    print("Structures:", results.data.structures)
    print("Trajectory:", results.data.trajectory)
    # Stdout from the program
    print(results.logs)
    # Input data used to generate the calculation
    print(results.input_data)
    # Provenance of generated calculation
    print(results.provenance)
