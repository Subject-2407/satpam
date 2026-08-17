"""Alokator `node_id` sesuai format kontrak yang tetap.

Format: `{node_type}_{nomor 5 digit}`, contoh `domain_00042`. Nomor dihitung
per-tipe dan mulai dari 1, jadi `domain_00001` dan `phone_00001` bisa
berdampingan — keduanya tetap unik global karena prefiks tipenya berbeda.

Semua node_id di seluruh generator wajib lewat kelas ini. Tidak ada modul lain
yang boleh merangkai node_id dengan f-string sendiri: itu jalan tercepat menuju
id duplikat yang baru ketahuan saat orang lain gagal membaca berkasnya.

Modul ini tidak mengimpor apa pun dari `rules/` — ini aturan keras yang tidak
boleh dilanggar.
"""

from __future__ import annotations

from generator.schema import NODE_ID_DIGITS, NODE_TYPES, node_type_of

#: Nomor terbesar yang masih muat di lebar `NODE_ID_DIGITS`.
MAX_NUMBER_PER_TYPE: int = 10**NODE_ID_DIGITS - 1


class IdAllocator:
    """Pembagi `node_id` unik per tipe node.

    Contoh:
        >>> alloc = IdAllocator()
        >>> alloc.new_id("domain")
        'domain_00001'
        >>> alloc.new_id("domain")
        'domain_00002'
        >>> alloc.new_id("phone")
        'phone_00001'
    """

    def __init__(self) -> None:
        self._counters: dict[str, int] = {node_type: 0 for node_type in NODE_TYPES}

    def new_id(self, node_type: str) -> str:
        """Terbitkan satu `node_id` baru untuk `node_type`.

        Raises:
            ValueError: bila `node_type` bukan salah satu dari 8 tipe node yang dikenal.
            OverflowError: bila nomor melewati lebar 5 digit kontrak.
        """
        if node_type not in self._counters:
            raise ValueError(
                f"node_type {node_type!r} tidak dikenal; "
                f"harus salah satu dari {list(NODE_TYPES)}"
            )

        number = self._counters[node_type] + 1
        if number > MAX_NUMBER_PER_TYPE:
            raise OverflowError(
                f"node_id untuk tipe {node_type!r} melewati batas "
                f"{MAX_NUMBER_PER_TYPE} — format {NODE_ID_DIGITS} digit di "
                f"SRS §5.3 tidak lagi cukup"
            )
        self._counters[node_type] = number
        return f"{node_type}_{number:0{NODE_ID_DIGITS}d}"

    def new_ids(self, node_type: str, count: int) -> list[str]:
        """Terbitkan `count` buah `node_id` sekaligus untuk `node_type`."""
        if count < 0:
            raise ValueError(f"count tidak boleh negatif, dapat {count}")
        return [self.new_id(node_type) for _ in range(count)]

    def issued(self, node_type: str) -> int:
        """Jumlah id yang sudah diterbitkan untuk satu tipe."""
        if node_type not in self._counters:
            raise ValueError(f"node_type {node_type!r} tidak dikenal")
        return self._counters[node_type]

    def total_issued(self) -> int:
        """Total id yang sudah diterbitkan untuk semua tipe."""
        return sum(self._counters.values())

    def counts(self) -> dict[str, int]:
        """Salinan hitungan per tipe, untuk `manifest.counts` dan diagnostik."""
        return dict(self._counters)

    def __repr__(self) -> str:  # pragma: no cover - hanya untuk debugging
        nonzero = {k: v for k, v in self._counters.items() if v}
        return f"IdAllocator(total={self.total_issued()}, {nonzero})"


def sort_key(node_id: str) -> tuple[int, int]:
    """Kunci pengurutan `node_id`: urutan tipe node yang tetap, lalu nomor.

    Dipakai agar `nodes.csv` keluar dalam urutan tipe node yang tetap
    alih-alih alfabetis, supaya lebih mudah diperiksa mata saat orang lain
    membuka berkasnya.
    """
    node_type = node_type_of(node_id)
    number = int(node_id.rsplit("_", 1)[1])
    return NODE_TYPES.index(node_type), number
