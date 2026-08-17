"""Penanganan waktu simulasi generator.

Seluruh kolom ISO8601 pada keluaran generator (`first_seen_at`, `last_seen_at`)
berasal dari modul ini. Rentang simulasi 18 bulan diambil dari target skala
generator, dan titik awalnya adalah tanggal tetap di
`GeneratorParams.timeline_start` — bukan waktu sekarang — supaya seed yang
sama selalu menghasilkan tanggal yang sama.

Dua keputusan yang perlu diketahui pembaca lain:

1. **Granularitas detik, bukan hari.** Dengan ~5.000 node di atas 548 hari,
   granularitas hari membuat ~9 node berbagi `first_seen_at` yang sama persis.
   Batas persentil split bisa jatuh di tengah kelompok kembar itu, dan siapa
   pun yang menghitung ulang split dari persentil akan mendapat pembagian
   berbeda dari yang tertulis di kolom `split`. Granularitas detik membuat
   nilai kembar praktis tidak ada.

2. **`age_days()` adalah satu-satunya definisi `feat_age_days`.** `features.py`
   dan `validate.py` sama-sama memanggilnya, jadi angka di kolom itu tidak
   mungkin berbeda dari angka yang dipakai memeriksanya.

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang tidak
boleh dilanggar.
"""

from __future__ import annotations

import calendar
from datetime import datetime, timedelta, timezone

import numpy as np

from generator.config import GeneratorParams

#: Pembulatan `feat_age_days` (bertipe float). Dipatok agar hasil hitung ulang
#: oleh modul lain identik sampai digit terakhir.
AGE_DAYS_DECIMALS: int = 4

SECONDS_PER_DAY: float = 86_400.0


def _days_in_month(year: int, month: int) -> int:
    return calendar.monthrange(year, month)[1]


def _add_months(moment: datetime, months: int) -> datetime:
    """Tambah `months` bulan kalender, hari dipangkas bila bulan tujuan pendek."""
    month_index = moment.month - 1 + months
    year = moment.year + month_index // 12
    month = month_index % 12 + 1
    day = min(moment.day, _days_in_month(year, month))
    return moment.replace(year=year, month=month, day=day)


class Timeline:
    """Rentang waktu simulasi beserta seluruh operasi waktu generator.

    Contoh:
        >>> tl = Timeline.from_params(GeneratorParams())
        >>> tl.to_iso(tl.start)
        '2025-01-01T00:00:00+07:00'
        >>> tl.to_iso(tl.end)
        '2026-07-01T00:00:00+07:00'
        >>> tl.total_days
        546.0
    """

    def __init__(
        self,
        start_date: str,
        months: int,
        tz_offset_hours: int,
    ) -> None:
        if months <= 0:
            raise ValueError(f"months harus positif, dapat {months}")
        self.tz = timezone(timedelta(hours=tz_offset_hours))
        naive_start = datetime.strptime(start_date, "%Y-%m-%d")
        self.start = naive_start.replace(tzinfo=self.tz)
        self.end = _add_months(self.start, months)
        self.months = months
        self._total_seconds = (self.end - self.start).total_seconds()

    @classmethod
    def from_params(cls, params: GeneratorParams) -> Timeline:
        """Bangun timeline dari parameter generator."""
        return cls(
            start_date=params.timeline_start,
            months=params.simulation_months,
            tz_offset_hours=params.timezone_offset_hours,
        )

    # -- konversi fraksi <-> waktu -------------------------------------

    @property
    def total_seconds(self) -> float:
        """Panjang rentang simulasi dalam detik."""
        return self._total_seconds

    @property
    def total_days(self) -> float:
        """Panjang rentang simulasi dalam hari."""
        return self._total_seconds / SECONDS_PER_DAY

    def at_fraction(self, fraction: float) -> datetime:
        """Waktu pada posisi `fraction` (0,0 = awal rentang, 1,0 = akhir)."""
        fraction = float(np.clip(fraction, 0.0, 1.0))
        moment = self.start + timedelta(seconds=fraction * self._total_seconds)
        return moment.replace(microsecond=0)

    def fraction_of(self, moment: datetime) -> float:
        """Posisi relatif sebuah waktu di dalam rentang, 0,0–1,0."""
        elapsed = (moment - self.start).total_seconds()
        return float(np.clip(elapsed / self._total_seconds, 0.0, 1.0))

    def offset_seconds(self, moment: datetime) -> float:
        """Jarak sebuah waktu dari awal rentang, dalam detik.

        Dipakai `split.py` sebagai nilai numerik untuk menghitung persentil
        `first_seen_at`.
        """
        return (moment - self.start).total_seconds()

    # -- sampling -----------------------------------------------------

    def sample(
        self,
        rng: np.random.Generator,
        low_fraction: float = 0.0,
        high_fraction: float = 1.0,
    ) -> datetime:
        """Ambil satu waktu acak di dalam jendela `[low_fraction, high_fraction]`."""
        if low_fraction > high_fraction:
            raise ValueError(
                f"low_fraction {low_fraction} > high_fraction {high_fraction}"
            )
        return self.at_fraction(rng.uniform(low_fraction, high_fraction))

    def sample_between(
        self,
        rng: np.random.Generator,
        earliest: datetime,
        latest: datetime,
    ) -> datetime:
        """Ambil satu waktu acak antara dua waktu, keduanya dipangkas ke rentang."""
        earliest = self.clamp(earliest)
        latest = self.clamp(latest)
        if earliest > latest:
            earliest, latest = latest, earliest
        span = (latest - earliest).total_seconds()
        if span <= 0:
            return earliest
        moment = earliest + timedelta(seconds=float(rng.uniform(0.0, span)))
        return moment.replace(microsecond=0)

    # -- aritmetika ---------------------------------------------------

    def add_days(self, moment: datetime, days: float) -> datetime:
        """Geser sebuah waktu sejumlah hari, hasilnya dipangkas ke rentang."""
        return self.clamp(moment + timedelta(days=float(days)))

    def clamp(self, moment: datetime) -> datetime:
        """Pangkas sebuah waktu agar tetap di dalam `[start, end]`."""
        if moment < self.start:
            return self.start
        if moment > self.end:
            return self.end
        return moment.replace(microsecond=0)

    # -- format -------------------------------------------------------

    def to_iso(self, moment: datetime) -> str:
        """Format ISO8601 lengkap dengan offset zona waktu, presisi detik."""
        return moment.replace(microsecond=0).isoformat()

    @staticmethod
    def from_iso(text: str) -> datetime:
        """Baca kembali ISO8601 keluaran `to_iso`."""
        return datetime.fromisoformat(text)

    def __repr__(self) -> str:  # pragma: no cover - hanya untuk debugging
        return (
            f"Timeline({self.to_iso(self.start)} .. {self.to_iso(self.end)}, "
            f"{self.months} bulan, {self.total_days:.0f} hari)"
        )


def age_days(first_seen_at: datetime, last_seen_at: datetime) -> float:
    """Definisi tunggal `feat_age_days` (`last_seen_at - first_seen_at`).

    Dipakai bersama oleh `features.py` (saat menulis) dan `validate.py` (saat
    memeriksa), supaya tidak ada dua definisi yang bisa berselisih.
    """
    delta = (last_seen_at - first_seen_at).total_seconds() / SECONDS_PER_DAY
    return round(max(delta, 0.0), AGE_DAYS_DECIMALS)
