from decimal import Decimal
from datetime import date
import pytest
from zespol_A import BankSystem, Konto, ZewnetrznyProcesor, ProcesorNiedostepny

@pytest.fixture
def bank():
    b=BankSystem()
    b.utworz_konto('1234567895','Anna',1000)
    b.utworz_konto('1111111119','Jan',500)
    return b

def test_wplata_kwota_ulamkowa(bank):
    assert bank.wplac('1234567895',Decimal('0.01')) == Decimal('1000.01')

def test_wyplata_dokladnie_saldo(bank):
    assert bank.wyplac('1234567895',1000) == Decimal('0')

def test_przelew_dokladnie_saldo(bank):
    assert bank.przelew('1234567895','1111111119',1000) == Decimal('0')
    assert bank.konta['1111111119'].saldo == Decimal('1500')

def test_przelew_limit_dokladnie_milion(bank):
    bank.konta['1234567895'].saldo=Decimal('1000000')
    assert bank.przelew('1234567895','1111111119',1000000) == Decimal('0')

def test_historia_granice_przedzialu(bank):
    k=bank.konta['1234567895']
    k.dodaj_wpis('wplata',Decimal('10'),date(2026,1,1))
    k.dodaj_wpis('wplata',Decimal('20'),date(2026,1,31))
    assert len(bank.historia_w_okresie('1234567895',date(2026,1,1),date(2026,1,31))) == 2

def test_odsetki_trzy_miesiace(bank):
    assert bank.nalicz_odsetki('1234567895',12,3) == Decimal('1020.10')
    assert len(bank.konta['1234567895'].historia)==2

def test_numer_poprawny_wlasciwa_suma():
    assert BankSystem._numer_poprawny('1234567895') is True
    assert BankSystem._numer_poprawny('1234567894') is False

def test_wyciag_oddziela_rok(bank):
    k=bank.konta['1234567895']
    k.dodaj_wpis('wplata',Decimal('50'),date(2025,1,10))
    k.dodaj_wpis('wplata',Decimal('20'),date(2026,1,10))
    assert bank.wyciag_miesieczny('1234567895',2026,1)['wplaty']==Decimal('20')
