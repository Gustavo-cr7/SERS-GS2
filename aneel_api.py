import csv
import json
import os
import urllib.parse
import urllib.request
from datetime import date

from base_dados import DISTRIBUIDORAS

URL_API = "https://dadosabertos.aneel.gov.br/api/3/action/datastore_search"
RESOURCE_ID = "fcf2906c-7c32-4b9b-a637-054e7a5234f4"
URL_DATASET = "https://dadosabertos.aneel.gov.br/dataset/tarifas-distribuidoras-energia-eletrica"

PASTA_DADOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
ARQUIVO_CSV = os.path.join(PASTA_DADOS, "tarifas_aneel_b3.csv")

CAMPOS_CSV = [
    "sigla", "uf", "distribuidora", "resolucao", "inicio_vigencia", "fim_vigencia",
    "tusd_r_mwh", "te_r_mwh", "tarifa_r_kwh_sem_impostos", "data_consulta",
]


def _para_float(valor_br):
    texto = str(valor_br).strip().replace(".", "").replace(",", ".")
    if texto.startswith("."):
        texto = "0" + texto
    return float(texto) if texto else 0.0


def _consultar_api(filtros, limite=10):
    parametros = {
        "resource_id": RESOURCE_ID,
        "limit": limite,
        "sort": "DatInicioVigencia desc",
        "filters": json.dumps(filtros, ensure_ascii=False),
    }
    url = URL_API + "?" + urllib.parse.urlencode(parametros)
    with urllib.request.urlopen(url, timeout=60) as resposta:
        dados = json.loads(resposta.read().decode("utf-8"))
    return dados["result"]["records"]


def buscar_tarifa_b3(sigla, hoje=None):
    hoje = hoje or date.today().isoformat()
    filtros = {
        "SigAgente": sigla,
        "DscSubGrupo": "B3",
        "DscModalidadeTarifaria": "Convencional",
        "DscBaseTarifaria": "Tarifa de Aplicação",
        "DscDetalhe": "Não se aplica",
        "NomPostoTarifario": "Não se aplica",
    }
    registros = _consultar_api(filtros)
    for reg in registros:
        if reg["DatInicioVigencia"] <= hoje <= reg["DatFimVigencia"]:
            tusd = _para_float(reg["VlrTUSD"])
            te = _para_float(reg["VlrTE"])
            return {
                "sigla": sigla,
                "uf": DISTRIBUIDORAS[sigla]["uf"],
                "distribuidora": DISTRIBUIDORAS[sigla]["nome"],
                "resolucao": reg["DscREH"],
                "inicio_vigencia": reg["DatInicioVigencia"],
                "fim_vigencia": reg["DatFimVigencia"],
                "tusd_r_mwh": round(tusd, 2),
                "te_r_mwh": round(te, 2),
                "tarifa_r_kwh_sem_impostos": round((tusd + te) / 1000, 5),
                "data_consulta": hoje,
            }
    return None


def atualizar_tarifas(mostrar_progresso=True):
    os.makedirs(PASTA_DADOS, exist_ok=True)
    resultados = []
    for sigla in DISTRIBUIDORAS:
        try:
            tarifa = buscar_tarifa_b3(sigla)
            if tarifa:
                resultados.append(tarifa)
                if mostrar_progresso:
                    print(f"  [OK] {sigla:<22} R$ {tarifa['tarifa_r_kwh_sem_impostos']:.4f}/kWh "
                          f"(vigência desde {tarifa['inicio_vigencia']})")
            elif mostrar_progresso:
                print(f"  [--] {sigla:<22} sem tarifa B3 vigente encontrada")
        except Exception as erro:
            if mostrar_progresso:
                print(f"  [ERRO] {sigla:<20} {erro}")

    if resultados:
        with open(ARQUIVO_CSV, "w", newline="", encoding="utf-8") as arq:
            escritor = csv.DictWriter(arq, fieldnames=CAMPOS_CSV, delimiter=";")
            escritor.writeheader()
            escritor.writerows(resultados)
    return resultados


def carregar_tarifas():
    if not os.path.exists(ARQUIVO_CSV):
        return {}
    tarifas = {}
    with open(ARQUIVO_CSV, encoding="utf-8") as arq:
        for linha in csv.DictReader(arq, delimiter=";"):
            linha["tusd_r_mwh"] = float(linha["tusd_r_mwh"])
            linha["te_r_mwh"] = float(linha["te_r_mwh"])
            linha["tarifa_r_kwh_sem_impostos"] = float(linha["tarifa_r_kwh_sem_impostos"])
            tarifas[linha["sigla"]] = linha
    return tarifas


if __name__ == "__main__":
    print("Consultando o Portal de Dados Abertos da ANEEL...")
    print(f"Fonte: {URL_DATASET}\n")
    dados = atualizar_tarifas()
    print(f"\n{len(dados)} distribuidoras salvas em: {ARQUIVO_CSV}")
