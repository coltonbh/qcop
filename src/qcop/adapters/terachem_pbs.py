from .terachem_fe import TeraChemFEAdapter


class TeraChemPBSAdapter(TeraChemFEAdapter):
    """Adapter for TeraChem's Protocol Buffer Server."""

    program = "terachem-pbs"

    def __init__(self):
        super().__init__()
        # Check that tcpb is installed.
        self.tcpb = self._ensure_tcpb()
        self.client = self.tcpb.TCProtobufClient
