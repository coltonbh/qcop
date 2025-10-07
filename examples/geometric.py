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

# Define the program input
prog_inp = CompositeCalcSpec(
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
    output = compute("geometric", prog_inp, propagate_wfn=True, rm_scratch_dir=False)
except exceptions.QCOPBaseError as e:
    # Calculation failed
    output = e.results
    print(output.logs)
    # Input data used to generate the calculation
    print(output.input_data)
    # Provenance of generated calculation
    print(output.provenance)
    print(output.traceback)
    raise

else:
    # Check results
    print("Energies:", output.data.energies)
    print("Structures:", output.data.structures)
    print("Trajectory:", output.data.trajectory)
    # Stdout from the program
    print(output.logs)
    # Input data used to generate the calculation
    print(output.input_data)
    # Provenance of generated calculation
    print(output.provenance)
