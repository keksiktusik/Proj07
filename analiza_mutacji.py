"""Niezalezny, ograniczony eksperyment mutacyjny na 8 wskazanych zmianach.
Nie zastępuje pełnego raportu mutmut. Każdy mutant to jedna podmiana tekstowa.
"""
import subprocess, sys, pathlib, os
root=pathlib.Path(__file__).resolve().parent
source=root/'zespol_A.py'
original=source.read_text(encoding='utf-8')
mutations=[
('M1','if kwota <= 0:', 'if kwota < 0:',1,'wplata: granica zero'),
('M2','konto.saldo += kwota','konto.saldo -= kwota',1,'wplata: kierunek zmiany salda'),
('M3','if kwota > konto_z.saldo:', 'if kwota >= konto_z.saldo:',1,'przelew: rownosc salda'),
('M4','if kwota > Decimal("1000000"):', 'if kwota >= Decimal("1000000"):',1,'przelew: granica limitu'),
('M5','if od <= data_operacji <= do:', 'if od < data_operacji < do:',1,'historia: domkniete granice'),
('M6','for _ in range(miesiace - 1):','for _ in range(miesiace):',1,'odsetki: liczba iteracji'),
('M7','return cyfry[9] == suma_kontrolna','return cyfry[9] != suma_kontrolna',1,'numer: suma kontrolna'),
('M8','data_operacji.year == rok and data_operacji.month == miesiac','data_operacji.year != rok and data_operacji.month == miesiac',1,'wyciag: filtrowanie roku'),
]
def run(extra):
    tests=['test_zespol_A.py']+(['test_mutacje_dodatkowe.py'] if extra else [])
    cmd=[sys.executable,'-m','pytest','-q',*tests,'-k','not test_wyplac_brak_srodkow']
    r=subprocess.run(cmd,cwd=root,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env={**os.environ,"PYTEST_DISABLE_PLUGIN_AUTOLOAD":"1"},timeout=20)
    return r.returncode,r.stdout
try:
    baseline=run(False)
    print('BAZA (z pominieciem znanego bledu):', 'PASS' if baseline[0]==0 else 'FAIL')
    for mid,old,new,count,desc in mutations:
        if original.count(old)<count: raise RuntimeError('Nie znaleziono wzorca '+mid)
        source.write_text(original.replace(old,new,count),encoding='utf-8')
        before=run(False)
        after=run(True)
        print(f'{mid} | {desc} | stare: {"ZABITY" if before[0] else "PRZETRWAL"} | rozszerzone: {"ZABITY" if after[0] else "PRZETRWAL"}')
        source.write_text(original,encoding='utf-8')
finally:
    source.write_text(original,encoding='utf-8')
