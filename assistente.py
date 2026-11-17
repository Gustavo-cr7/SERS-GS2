import csv
import json
import math
import os
import re
import unicodedata
from datetime import datetime

from base_dados import FONTES, PREMISSAS

PASTA_RELATORIOS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "relatorios")

AVISO_LIMITACOES = (
    "ATENÇÃO: os valores são ESTIMATIVAS para ajudar na decisão, não são ganhos garantidos.\n"
    "  - Tarifa oficial ANEEL (SP) sem impostos; aplicamos fator médio de tributos (x"
    + f"{PREMISSAS['fator_tributos']:.2f}".replace(".", ",")
    + ").\n"
    "  - Não incluímos bandeira tarifária, taxa de iluminação pública nem reajustes futuros.\n"
    "  - Preços e potências são médias de mercado: confira a etiqueta e peça 3 orçamentos.\n"
    "  - A geração solar varia com sombra, inclinação do telhado, clima e sujeira dos painéis."
)


def reais(valor):
    texto = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {texto}"


def reais_kwh(valor):
    return "R$ " + f"{valor:.4f}".replace(".", ",")


def numero(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def tempo_retorno(meses):
    if meses == 0:
        return "imediato (sem investimento)"
    if math.isinf(meses):
        return "não se aplica"
    if meses < 12:
        return f"{numero(meses, 1)} meses"
    return f"{numero(meses, 0)} meses (~{numero(meses / 12, 1)} anos)"


def _linha(char="-", tam=78):
    return char * tam


def gerar_relatorio(sim, nome_perfil, distribuidora, imovel_proprio=True, tem_dinheiro=True):
    b, led, so, ass = sim["base"], sim["led"], sim["solar"], sim["assinatura"]
    t = [
        _linha("="),
        "  CITIZEN ASSIST AI - Soluções em Energia para Pequenos Comerciantes (SP)",
        _linha("="),
        f"Comércio: {nome_perfil}",
        f"Distribuidora: {distribuidora['distribuidora']} (SP) - tarifa ANEEL B3 desde {distribuidora['inicio_vigencia']}",
        f"Tarifa ANEEL s/ impostos: {reais_kwh(sim['tarifa_sem_impostos'])}/kWh  ->  c/ impostos (est.): {reais_kwh(sim['tarifa_final'])}/kWh",
        "\n" + _linha(),
        "1) DIAGNÓSTICO DO SEU CONSUMO",
        _linha(),
        f"Consumo estimado: {numero(b['kwh_mes'])} kWh/mês ({numero(b['kwh_ano'])} kWh/ano).",
        f"Gasto estimado:   {reais(b['custo_mes'])}/mês ({reais(b['custo_ano'])}/ano).",
        "\nO que mais pesa na conta:",
    ]
    for i in b["maiores_consumidores"]:
        t.append(f"  - {i['nome']} (x{i['quantidade']}): {numero(i['kwh_mes'])} kWh/mês "
                 f"= {reais(i['custo_mes'])}/mês ({numero(i['participacao_pct'])}%)")
    t.append(f"Emissão de CO2 da energia usada: ~{numero(b['co2_kg_ano'])} kg/ano.")

    t.extend(["\n" + _linha(), "2) COMPARAÇÃO DAS 3 SOLUÇÕES", _linha()])
    t.append(f"{'Solução':<38}{'Investimento':>13}{'Economia/mês':>14}{'Econ.':>7}  Retorno")
    for alt in (led, so, ass):
        t.append(f"{alt['nome']:<38}{reais(alt['investimento']):>13}{reais(alt['economia_r_mes']):>14}"
                 f"{numero(alt['economia_pct'])+'%':>7}  {tempo_retorno(alt['payback_meses'])}")

    t.append("\nDetalhes de cada solução:")
    t.append(f"  1) Lâmpadas LED: troca {led['qtd_lampadas']} fluorescentes (48 W) por LED (18 W). "
             f"Conta cai para ~{reais(led['conta_nova_mes'])}/mês. Evita {numero(led['co2_evitado_kg_ano'])} kg CO2/ano.")
    t.append(f"  2) Painéis solares (SP): {numero(so['kwp'], 2)} kWp ({so['modulos']} placas de 550 W, ~{numero(so['area_m2'])} m²). "
             f"Gera ~{numero(so['geracao_kwh_mes'])} kWh/mês (irradiação SP: 5,06 h/dia). "
             f"Já considera mínimo de {so['minimo_faturavel_kwh']} kWh e Fio B (Lei 14.300). "
             f"Evita {numero(so['co2_evitado_kg_ano'])} kg CO2/ano.")
    t.append(f"  3) Solar por assinatura: desconto de {numero(ass['desconto_pct'])}% sem obra e sem investimento. "
             f"Conta cai para ~{reais(ass['conta_nova_mes'])}/mês.")

    t.extend(["\n" + _linha(), "3) RECOMENDAÇÃO DO CITIZEN ASSIST AI", _linha()])
    t.extend(recomendacao(sim, imovel_proprio, tem_dinheiro))

    t.extend([
        "\n" + _linha(),
        "4) GLOSSÁRIO E LIMITAÇÕES",
        _linha(),
        "  kWh = energia consumida no mês | kWp = potência do sistema solar | Payback = tempo de retorno.",
        "",
        AVISO_LIMITACOES,
        "\nFontes: ANEEL (tarifas B3 SP e REN 1.000/2021), Lei 14.300/2022, INPE/Atlas Solar, INMETRO/PROCEL e MCTI.",
        _linha("="),
    ])
    return "\n".join(t)


def recomendacao(sim, imovel_proprio, tem_dinheiro):
    led, so, ass = sim["led"], sim["solar"], sim["assinatura"]
    r = [f"PASSO 1 (imediato): troque as {led['qtd_lampadas']} lâmpadas por LED "
         f"(~{reais(led['investimento'])}, economiza ~{reais(led['economia_r_mes'])}/mês, "
         f"se paga em {tempo_retorno(led['payback_meses'])})."]
    if not imovel_proprio:
        r.append(f"PASSO 2 (imóvel alugado): escolha a SOLAR POR ASSINATURA — sem obra no telhado, "
                 f"economia estimada de ~{reais(ass['economia_r_mes'])}/mês sem investimento.")
    elif not tem_dinheiro:
        r.append(f"PASSO 2 (sem capital agora): comece pela SOLAR POR ASSINATURA "
                 f"(~{reais(ass['economia_r_mes'])}/mês) ou avalie financiamento onde a parcela seja menor que {reais(so['economia_r_mes'])}/mês.")
    else:
        r.append(f"PASSO 2 (imóvel próprio): instale os PAINÉIS SOLARES ({numero(so['kwp'], 2)} kWp) — "
                 f"economia de ~{reais(so['economia_r_mes'])}/mês e retorno em {tempo_retorno(so['payback_meses'])}.")
    return r


def gerar_relatorio_rapido(sim, distribuidora, imovel_proprio=True):
    so, ass = sim["solar"], sim["assinatura"]
    t = [
        _linha("="),
        "  CITIZEN ASSIST AI - Simulação rápida pela conta de luz (SP)",
        _linha("="),
        f"Distribuidora: {distribuidora['distribuidora']} (SP) | Tarifa c/ impostos (est.): {reais_kwh(sim['tarifa_final'])}/kWh",
        f"Conta de {reais(sim['custo_mes'])} ≈ consumo de {numero(sim['kwh_mes'])} kWh/mês.\n",
        f"  - Painéis solares: {numero(so['kwp'], 2)} kWp ({so['modulos']} placas) | Inv.: ~{reais(so['investimento'])} | "
        f"Econ.: ~{reais(so['economia_r_mes'])}/mês | Retorno: {tempo_retorno(so['payback_meses'])}",
        f"  - Solar por assinatura: Inv.: R$ 0,00 | Econ.: ~{reais(ass['economia_r_mes'])}/mês | Retorno: imediato",
    ]
    if not imovel_proprio:
        t.append("\nComo o imóvel é alugado, a Solar por Assinatura é a opção renovável recomendada.")
    t.extend(["\n" + AVISO_LIMITACOES, _linha("=")])
    return "\n".join(t)


FAQ = [
    {
        "chaves": ["led", "lampada", "fluorescente", "iluminacao"],
        "pergunta": "Por que trocar lâmpadas fluorescentes por LED?",
        "resposta": "Uma tubular LED de 18 W ilumina igual a uma fluorescente de 40 W (que gasta ~48 W com reator), "
                    "reduzindo o gasto em mais de 60% e se pagando em poucos meses.",
    },
    {
        "chaves": ["assinatura", "alugad", "inquilino", "compartilhada"],
        "pergunta": "Como funciona a energia solar por assinatura?",
        "resposta": "Você recebe créditos de uma usina solar remota na sua conta da distribuidora com desconto "
                    "típico de 15%, sem precisar de telhado próprio nem fazer obras. Base legal: Lei 14.300/2022.",
    },
    {
        "chaves": ["14.300", "14300", "fio b", "taxacao", "painel", "placa", "solar"],
        "pergunta": "Vale a pena colocar painéis solares com a Lei 14.300?",
        "resposta": "Sim. Sistemas novos pagam parte do 'Fio B' sobre a energia compensada (desconto já incluído "
                    "no nosso cálculo), mas em SP ainda economizam cerca de 75% da conta com payback de ~3 a 4 anos.",
    },
    {
        "chaves": ["bandeira", "vermelha", "amarela", "imposto", "tarifa"],
        "pergunta": "Por que a tarifa da ANEEL é diferente do valor do boleto?",
        "resposta": "A ANEEL publica a tarifa base sem impostos (ICMS e PIS/COFINS) e sem bandeira tarifária. "
                    "Por isso o assistente aplica o fator x1,30 para aproximar o valor real da fatura em SP.",
    },
    {
        "chaves": ["minimo", "disponibilidade", "trifasic", "zera"],
        "pergunta": "Por que a conta não zera com energia solar?",
        "resposta": "A distribuidora sempre cobra o custo de disponibilidade: 30 kWh (monofásico), 50 kWh (bifásico) "
                    "ou 100 kWh (trifásico), além de iluminação pública e Fio B (REN ANEEL 1.000/2021).",
    },
]

_PADROES_SENSIVEIS = [
    re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b"),
    re.compile(r"\(?\b\d{2}\)?\s?9?\d{4}-?\d{4}\b"),
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+"),
]


def _normalizar(texto):
    sem_acento = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")


def contem_dado_pessoal(texto):
    return any(p.search(texto) for p in _PADROES_SENSIVEIS)


def responder_duvida(pergunta):
    if contem_dado_pessoal(pergunta):
        return "Por segurança, não digite CPF, CNPJ, telefone ou e-mail aqui. Reescreva sem dados pessoais."
    texto = _normalizar(pergunta)
    melhor, pontos = None, 0
    for item in FAQ:
        p = sum(1 for chave in item["chaves"] if _normalizar(chave) in texto)
        if p > pontos:
            melhor, pontos = item, p
    if not melhor:
        return "Tente perguntar sobre:\n" + "\n".join(f"  - {f['pergunta']}" for f in FAQ)
    return f"{melhor['pergunta']}\n{melhor['resposta']}"


def listar_fontes():
    return "\n".join(f"  - {nome}\n    {url}" for nome, url in FONTES)


def _limpar_json(obj):
    if isinstance(obj, float) and math.isinf(obj):
        return None
    if isinstance(obj, dict):
        return {k: _limpar_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_limpar_json(v) for v in obj]
    return obj


def exportar(sim, nome_perfil, distribuidora, prefixo="diagnostico"):
    os.makedirs(PASTA_RELATORIOS, exist_ok=True)
    carimbo = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_nome = os.path.join(PASTA_RELATORIOS, f"{prefixo}_{carimbo}")

    dados = {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "perfil": nome_perfil,
        "distribuidora": distribuidora,
        "premissas": PREMISSAS,
        "simulacao": {k: v for k, v in sim.items() if k != "itens"},
        "itens": sim.get("itens", []),
        "fontes": FONTES,
    }
    with open(base_nome + ".json", "w", encoding="utf-8") as arq:
        json.dump(_limpar_json(dados), arq, ensure_ascii=False, indent=2)

    arquivos = [base_nome + ".json"]
    if sim.get("itens"):
        with open(base_nome + "_consumo.csv", "w", newline="", encoding="utf-8-sig") as arq:
            w = csv.writer(arq, delimiter=";")
            w.writerow(["equipamento", "quantidade", "potencia_W", "horas_dia", "dias_mes", "kWh_mes", "custo_R$_mes", "fonte"])
            for i in sim["itens"]:
                w.writerow([i["nome"], i["quantidade"], i["potencia_w"], i["horas_dia"], i["dias_mes"],
                            round(i["kwh_mes"], 2), round(i["custo_mes"], 2), i["fonte"]])
        arquivos.append(base_nome + "_consumo.csv")
    return arquivos
