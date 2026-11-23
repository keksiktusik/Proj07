
import pytest
from decimal import Decimal
from datetime import date, timedelta
from unittest.mock import patch

from zespol_A import (
    BankSystem,
    Konto,
    KontoZablokowane,
    KontoNieIstnieje,
    ProcesorNiedostepny,
    ZewnetrznyProcesor,
)


# ==========================================
# PRZYGOTOWANIE SYSTEMU DO TESTOW
# ==========================================

@pytest.fixture
def bank():
    system = BankSystem()

    system.utworz_konto(
        "1234567895", "Anna Kowalska", 1000
    )

    system.utworz_konto(
        "1111111119", "Jan Nowak", 500
    )

    return system


# ==========================================
# CZESC 1 - TESTY METODY WPLAC()
# ==========================================

def test_wplac_poprawna_kwota(bank):
    wynik = bank.wplac("1234567895", 200)

    assert wynik == Decimal("1200")
    assert len(bank.konta["1234567895"].historia) == 1


def test_wplac_kwota_zero(bank):
    with pytest.raises(ValueError):
        bank.wplac("1234567895", 0)


def test_wplac_kwota_ujemna(bank):
    with pytest.raises(ValueError):
        bank.wplac("1234567895", -100)


def test_wplac_nieprawidlowy_typ(bank):
    with pytest.raises(TypeError):
        bank.wplac("1234567895", "abc")


def test_wplac_nieistniejace_konto(bank):
    with pytest.raises(KontoNieIstnieje):
        bank.wplac("9999999999", 100)


# ==========================================
# CZESC 2 - TESTY METODY WYPLAC()
# ==========================================

def test_wyplac_poprawna_kwota(bank):
    wynik = bank.wyplac("1234567895", 200)

    assert wynik == Decimal("800")
    assert len(bank.konta["1234567895"].historia) == 1


def test_wyplac_kwota_zero(bank):
    with pytest.raises(ValueError):
        bank.wyplac("1234567895", 0)


def test_wyplac_kwota_ujemna(bank):
    with pytest.raises(ValueError):
        bank.wyplac("1234567895", -50)


def test_wyplac_konto_zablokowane(bank):
    bank.zablokuj_konto("1234567895")

    with pytest.raises(KontoZablokowane):
        bank.wyplac("1234567895", 100)


def test_wyplac_nieistniejace_konto(bank):
    with pytest.raises(KontoNieIstnieje):
        bank.wyplac("9999999999", 100)


def test_wyplac_brak_srodkow(bank):
    with pytest.raises(
        ValueError, match="Niewystarczajace srodki"
    ):
        bank.wyplac("1234567895", 2000)


# ==========================================
# CZESC 3 - TESTY METODY PRZELEW()
# ==========================================

def test_przelew_poprawny(bank):
    wynik = bank.przelew(
        "1234567895", "1111111119", 200
    )

    assert wynik == Decimal("800")
    assert bank.konta["1111111119"].saldo == Decimal("700")
    assert len(bank.konta["1234567895"].historia) == 1
    assert len(bank.konta["1111111119"].historia) == 1


def test_przelew_kwota_zero(bank):
    with pytest.raises(ValueError):
        bank.przelew(
            "1234567895", "1111111119", 0
        )


def test_przelew_kwota_ujemna(bank):
    with pytest.raises(ValueError):
        bank.przelew(
            "1234567895", "1111111119", -50
        )


def test_przelew_brak_srodkow(bank):
    with pytest.raises(
        ValueError, match="Niewystarczajace srodki"
    ):
        bank.przelew(
            "1234567895", "1111111119", 2000
        )


def test_przelew_konto_zablokowane(bank):
    bank.zablokuj_konto("1234567895")

    with pytest.raises(KontoZablokowane):
        bank.przelew(
            "1234567895", "1111111119", 100
        )


def test_przelew_nieistniejace_konto(bank):
    with pytest.raises(KontoNieIstnieje):
        bank.przelew(
            "1234567895", "9999999999", 100
        )


def test_przelew_przekroczony_limit(bank):
    bank.konta["1234567895"].saldo = Decimal("2000000")

    with pytest.raises(
        ValueError, match="dzienny limit"
    ):
        bank.przelew(
            "1234567895", "1111111119", 1000001
        )


# ==========================================
# CZESC 4 - NOWE TESTY NUMEROW KONT
# ==========================================

def test_numer_konta_za_krotki():
    assert BankSystem._numer_poprawny("123") is False


def test_numer_konta_nie_jest_napisem():
    assert BankSystem._numer_poprawny(1234567895) is False


def test_numer_konta_zawiera_litery():
    assert BankSystem._numer_poprawny("12345abcde") is False


def test_numer_konta_bledna_suma_kontrolna():
    assert BankSystem._numer_poprawny("1234567890") is False


def test_utworz_konto_nieprawidlowy_numer(bank):
    with pytest.raises(ValueError, match="Nieprawidlowy"):
        bank.utworz_konto("123", "Test")


def test_utworz_konto_duplikat(bank):
    with pytest.raises(ValueError, match="juz istnieje"):
        bank.utworz_konto("1234567895", "Druga Anna")


# ==========================================
# CZESC 5 - NOWE TESTY HISTORII I BLOKAD
# ==========================================

def test_dodaj_wpis_z_podana_data():
    konto = Konto("1234567895", "Anna", 1000)
    data = date(2026, 1, 15)

    konto.dodaj_wpis("wplata", Decimal("100"), data)

    assert konto.historia == [
        (data, "wplata", Decimal("100"))
    ]


def test_odblokuj_konto(bank):
    bank.zablokuj_konto("1234567895")

    assert bank.konta["1234567895"].status == "zablokowane"

    bank.odblokuj_konto("1234567895")

    assert bank.konta["1234567895"].status == "aktywne"

    wynik = bank.wyplac("1234567895", 100)

    assert wynik == Decimal("900")


def test_suma_dzisiejszych_wyplat(bank):
    konto = bank.konta["1234567895"]

    konto.dodaj_wpis("wyplata", Decimal("100"))
    konto.dodaj_wpis("przelew_wychodzacy", Decimal("200"))
    konto.dodaj_wpis("wplata", Decimal("300"))

    wynik = bank._suma_dzisiejszych_wyplat(konto)

    assert wynik == Decimal("300")


def test_suma_wyplat_z_innego_dnia(bank):
    konto = bank.konta["1234567895"]

    wczoraj = date.today() - timedelta(days=1)

    konto.dodaj_wpis(
        "wyplata", Decimal("100"), wczoraj
    )

    wynik = bank._suma_dzisiejszych_wyplat(konto)

    assert wynik == Decimal("0")


def test_suma_wyplat_pusta_historia(bank):
    konto = bank.konta["1234567895"]

    wynik = bank._suma_dzisiejszych_wyplat(konto)

    assert wynik == Decimal("0")


# ==========================================
# CZESC 6 - NOWE TESTY ODSETEK
# ==========================================

def test_nalicz_odsetki(bank):
    wynik = bank.nalicz_odsetki(
        "1234567895", 12, 2
    )

    assert wynik == Decimal("1010.00")
    assert len(bank.konta["1234567895"].historia) == 1


def test_nalicz_odsetki_jeden_miesiac(bank):
    wynik = bank.nalicz_odsetki(
        "1234567895", 12, 1
    )

    assert wynik == Decimal("1000")
    assert len(bank.konta["1234567895"].historia) == 0


# ==========================================
# CZESC 7 - NOWE TESTY HISTORII W OKRESIE
# ==========================================

def test_historia_w_okresie(bank):
    konto = bank.konta["1234567895"]

    konto.dodaj_wpis(
        "wplata", Decimal("100"), date(2026, 1, 10)
    )

    konto.dodaj_wpis(
        "wyplata", Decimal("50"), date(2026, 2, 10)
    )

    wynik = bank.historia_w_okresie(
        "1234567895",
        date(2026, 1, 1),
        date(2026, 1, 31)
    )

    assert len(wynik) == 1
    assert wynik[0][1] == "wplata"


def test_historia_w_okresie_brak_operacji(bank):
    wynik = bank.historia_w_okresie(
        "1234567895",
        date(2026, 1, 1),
        date(2026, 1, 31)
    )

    assert wynik == []


# ==========================================
# CZESC 8 - NOWE TESTY WYCIAGU MIESIECZNEGO
# ==========================================

def test_wyciag_miesieczny(bank):
    konto = bank.konta["1234567895"]

    konto.dodaj_wpis(
        "wplata", Decimal("200"), date(2026, 1, 10)
    )

    konto.dodaj_wpis(
        "wyplata", Decimal("100"), date(2026, 1, 11)
    )

    konto.dodaj_wpis(
        "przelew_przychodzacy",
        Decimal("50"),
        date(2026, 1, 12)
    )

    konto.dodaj_wpis(
        "przelew_wychodzacy",
        Decimal("30"),
        date(2026, 1, 13)
    )

    konto.dodaj_wpis(
        "odsetki", Decimal("10"), date(2026, 1, 14)
    )

    wynik = bank.wyciag_miesieczny(
        "1234567895", 2026, 1
    )

    assert wynik["wplaty"] == Decimal("260")
    assert wynik["wyplaty"] == Decimal("130")
    assert wynik["saldo_koncowe"] == Decimal("1000")


def test_wyciag_miesieczny_inny_miesiac(bank):
    konto = bank.konta["1234567895"]

    konto.dodaj_wpis(
        "wplata", Decimal("100"), date(2026, 2, 10)
    )

    wynik = bank.wyciag_miesieczny(
        "1234567895", 2026, 1
    )

    assert wynik["wplaty"] == Decimal("0")
    assert wynik["wyplaty"] == Decimal("0")


# ==========================================
# CZESC 9 - NOWE TESTY PROCESORA PLATNOSCI
# ==========================================

class GeneratorTestowy:
    def __init__(self, wartosc):
        self.wartosc = wartosc

    def random(self):
        return self.wartosc


def test_procesor_platnosci_sukces():
    procesor = ZewnetrznyProcesor(
        prawdopodobienstwo_awarii=0.3,
        generator=GeneratorTestowy(0.9)
    )

    wynik = procesor.wyslij_przelew(
        "9999999999", Decimal("100")
    )

    assert wynik["status"] == "zaksiegowano"
    assert wynik["numer_referencyjny"] == "REF000001"
    assert procesor.licznik_wywolan == 1


def test_procesor_platnosci_awaria():
    procesor = ZewnetrznyProcesor(
        prawdopodobienstwo_awarii=0.3,
        generator=GeneratorTestowy(0.1)
    )

    with pytest.raises(ProcesorNiedostepny):
        procesor.wyslij_przelew(
            "9999999999", Decimal("100")
        )

    assert procesor.licznik_wywolan == 1


def test_procesor_platnosci_opoznienie():
    procesor = ZewnetrznyProcesor(
        prawdopodobienstwo_awarii=0,
        opoznienie_s=0.01,
        generator=GeneratorTestowy(0.9)
    )

    with patch("zespol_A.time.sleep") as mock_sleep:
        wynik = procesor.wyslij_przelew(
            "9999999999", Decimal("100")
        )

    mock_sleep.assert_called_once_with(0.01)
    assert wynik["status"] == "zaksiegowano"


def test_procesor_domyslny_generator():
    procesor = ZewnetrznyProcesor(
        prawdopodobienstwo_awarii=0
    )

    wynik = procesor.wyslij_przelew(
        "9999999999", Decimal("100")
    )

    assert wynik["status"] == "zaksiegowano"


# ==========================================
# CZESC 10 - NOWE TESTY PRZELEWU ZEWN.
# ==========================================

def test_przelew_zewnetrzny_poprawny(bank):
    procesor = ZewnetrznyProcesor(
        prawdopodobienstwo_awarii=0,
        generator=GeneratorTestowy(0.9)
    )

    wynik = bank.przelew_zewnetrzny(
        "1234567895", "9999999999", 200, procesor
    )

    assert wynik["status"] == "zaksiegowano"
    assert bank.konta["1234567895"].saldo == Decimal("800")
    assert len(bank.konta["1234567895"].historia) == 1


def test_przelew_zewnetrzny_konto_zablokowane(bank):
    bank.zablokuj_konto("1234567895")

    with pytest.raises(KontoZablokowane):
        bank.przelew_zewnetrzny(
            "1234567895", "9999999999", 100
        )


def test_przelew_zewnetrzny_kwota_zero(bank):
    with pytest.raises(ValueError):
        bank.przelew_zewnetrzny(
            "1234567895", "9999999999", 0
        )


def test_przelew_zewnetrzny_brak_srodkow(bank):
    with pytest.raises(
        ValueError, match="Niewystarczajace srodki"
    ):
        bank.przelew_zewnetrzny(
            "1234567895", "9999999999", 2000
        )


def test_przelew_zewnetrzny_awaria_procesora(bank):
    procesor = ZewnetrznyProcesor(
        prawdopodobienstwo_awarii=1,
        generator=GeneratorTestowy(0.1)
    )

    with pytest.raises(ProcesorNiedostepny):
        bank.przelew_zewnetrzny(
            "1234567895", "9999999999", 100, procesor
        )

    assert bank.konta["1234567895"].saldo == Decimal("1000")
    assert len(bank.konta["1234567895"].historia) == 0


def test_przelew_zewnetrzny_domyslny_procesor(bank):
    with patch(
        "zespol_A.ZewnetrznyProcesor"
    ) as mock_klasa:

        mock_procesor = mock_klasa.return_value
        mock_procesor.wyslij_przelew.return_value = {
            "status": "zaksiegowano",
            "numer_referencyjny": "REF000001"
        }

        wynik = bank.przelew_zewnetrzny(
            "1234567895", "9999999999", 100
        )

    assert wynik["status"] == "zaksiegowano"
    assert bank.konta["1234567895"].saldo == Decimal("900")
    mock_procesor.wyslij_przelew.assert_called_once_with(
        "9999999999", Decimal("100")
    )


# ==========================================
# TEST DOMYKAJACY OSTATNIA GALAZ
# ==========================================

def test_wyciag_miesieczny_inny_typ_operacji(bank):
    konto = bank.konta["1234567895"]

    konto.dodaj_wpis(
        "operacja_testowa",
        Decimal("100"),
        date(2026, 1, 15)
    )

    wynik = bank.wyciag_miesieczny(
        "1234567895", 2026, 1
    )

    assert wynik["wplaty"] == Decimal("0")
    assert wynik["wyplaty"] == Decimal("0")
    assert wynik["saldo_koncowe"] == Decimal("1000")
