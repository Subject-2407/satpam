"""Generator data sintetik SATPAM dengan planted ground truth.

Ground truth (`gt_illicit`, `gt_operator_id`, `gt_ecosystem`) ditanam lebih
dulu oleh paket ini, baru jejak bukti ditaburkan di atasnya.

Paket ini DILARANG mengimpor apa pun dari `rules/` atau `scoring.py` — ini
aturan keras yang tidak boleh dilanggar, dijaga oleh
`tests/test_no_circularity.py`.
"""

from generator.config import GENERATOR_VERSION

__version__ = GENERATOR_VERSION

__all__ = ["GENERATOR_VERSION", "__version__"]
