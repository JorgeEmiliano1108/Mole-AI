from weasyprint import HTML
import inspect

try:
    import pydyf
except Exception:
    pydyf = None


class WeasyPrintReportGenerator:
    @staticmethod
    def generate_pdf(html: str) -> bytes:
        """Render HTML to PDF using WeasyPrint (standard engine).

        Provides a lightweight compatibility shim for pydyf versions whose
        `PDF.__init__` signature does not accept (version, identifier). If
        needed, we monkeypatch `pydyf.PDF` with a thin wrapper that accepts
        those arguments and delegates to the current implementation.
        """
        if pydyf is not None:
            try:
                sig = inspect.signature(pydyf.PDF.__init__)
                # If only `self` is accepted, wrap to accept (version, identifier)
                if len(sig.parameters) == 1:
                    class _PDFCompat(pydyf.PDF):
                        def __init__(self, version=None, identifier=None):
                            super().__init__()
                            # Provide attributes WeasyPrint expects when calling
                            # pydyf.PDF((version), identifier). `version` should be
                            # stored as bytes for comparison (e.g. b'1.7').
                            if version is None:
                                self.version = b'1.7'
                            elif isinstance(version, (bytes, bytearray)):
                                self.version = bytes(version)
                            else:
                                self.version = str(version).encode('ascii')
                            self.identifier = identifier

                    pydyf.PDF = _PDFCompat
            except Exception:
                # If inspection fails, continue and let WeasyPrint raise if incompatible
                pass

        return HTML(string=html).write_pdf()
