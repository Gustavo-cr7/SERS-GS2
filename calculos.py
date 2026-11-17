import math

from base_dados import EQUIPAMENTOS, IRRADIACAO_SP, PREMISSAS


def energia_kwh(potencia_w, horas_dia, dias):
    return potencia_w * horas_dia * dias / 1000


def tarifa_final(tarifa_sem_impostos):
    return tarifa_sem_impostos * PREMISSAS["fator_tributos"]


def custo_reais(kwh, tarifa):
    return kwh * tarifa


def payback_meses(investimento, economia_mensal):
    if economia_mensal <= 0:
        return math.inf
    return investimento / economia_mensal


def co2_kg(kwh):
    return kwh * PREMISSAS["fator_co2_kg_kwh"]


def percentual(parte, total):
    return (parte / total * 100) if total else 0.0


def montar_itens(itens_perfil):
    itens = []
    for eq_id, (qtd, horas, dias) in itens_perfil.items():
        eq = EQUIPAMENTOS[eq_id]
        p_base = eq["potencia_base"]
        itens.append({
            "id": eq_id,
            "nome": eq["nome"],
            "quantidade": qtd,
            "horas_dia": horas,
            "dias_mes": dias,
            "potencia_w": p_base,
            "kwh_mes": energia_kwh(p_base * qtd, horas, dias),
            "fonte": eq["fonte"],
        })
    return itens


def cenario_base(itens, tarifa):
    kwh = sum(i["kwh_mes"] for i in itens)
    for i in itens:
        i["custo_mes"] = custo_reais(i["kwh_mes"], tarifa)
        i["participacao_pct"] = percentual(i["kwh_mes"], kwh)
    return {
        "kwh_mes": kwh,
        "kwh_ano": kwh * 12,
        "custo_mes": custo_reais(kwh, tarifa),
        "custo_ano": custo_reais(kwh, tarifa) * 12,
        "co2_kg_ano": co2_kg(kwh * 12),
        "maiores_consumidores": sorted(itens, key=lambda x: x["kwh_mes"], reverse=True)[:3],
    }


def solucao_led(itens, tarifa):
    eq = EQUIPAMENTOS["lampada"]
    item_lamp = next((i for i in itens if i["id"] == "lampada"), None)
    consumo_total = sum(i["kwh_mes"] for i in itens)
    custo_total = custo_reais(consumo_total, tarifa)

    if not item_lamp:
        return {
            "nome": "1. Troca das lâmpadas por LED",
            "renovavel": False,
            "qtd_lampadas": 0,
            "economia_kwh_mes": 0.0,
            "economia_r_mes": 0.0,
            "economia_r_ano": 0.0,
            "economia_pct": 0.0,
            "investimento": 0.0,
            "payback_meses": math.inf,
            "co2_evitado_kg_ano": 0.0,
            "conta_nova_mes": custo_total,
        }

    qtd = item_lamp["quantidade"]
    kwh_led = energia_kwh(eq["potencia_led"] * qtd, item_lamp["horas_dia"], item_lamp["dias_mes"])
    eco_kwh = item_lamp["kwh_mes"] - kwh_led
    eco_r = custo_reais(eco_kwh, tarifa)
    invest = eq["custo_led"] * qtd
    return {
        "nome": "1. Troca das lâmpadas por LED",
        "renovavel": False,
        "qtd_lampadas": qtd,
        "economia_kwh_mes": eco_kwh,
        "economia_r_mes": eco_r,
        "economia_r_ano": eco_r * 12,
        "economia_pct": percentual(eco_kwh, consumo_total),
        "investimento": invest,
        "payback_meses": payback_meses(invest, eco_r),
        "co2_evitado_kg_ano": co2_kg(eco_kwh * 12),
        "conta_nova_mes": custo_total - eco_r,
    }


def solucao_paineis_solares(consumo_kwh_mes, tarifa, ligacao="trifasico"):
    p = PREMISSAS
    minimo = p["custo_disponibilidade_kwh"][ligacao]
    energia_compensar = max(consumo_kwh_mes - minimo, 0)
    geracao_por_kwp = IRRADIACAO_SP * 30 * p["performance_ratio"]
    kwp_necessario = energia_compensar / geracao_por_kwp if geracao_por_kwp else 0
    modulos = math.ceil(kwp_necessario / p["potencia_modulo_kw"]) if kwp_necessario else 0
    kwp = modulos * p["potencia_modulo_kw"]
    geracao_mes = kwp * geracao_por_kwp
    energia_compensada = min(geracao_mes, energia_compensar)

    investimento = kwp * p["custo_kwp_reais"]
    economia_r = custo_reais(energia_compensada, tarifa) * (1 - p["perda_fio_b"])
    custo_atual = custo_reais(consumo_kwh_mes, tarifa)

    return {
        "nome": "2. Painéis solares no telhado [RENOVÁVEL]",
        "renovavel": True,
        "irradiacao_sp": IRRADIACAO_SP,
        "minimo_faturavel_kwh": minimo,
        "kwp": kwp,
        "modulos": modulos,
        "area_m2": kwp * p["area_m2_por_kwp"],
        "geracao_kwh_mes": geracao_mes,
        "economia_kwh_mes": energia_compensada,
        "economia_r_mes": economia_r,
        "economia_r_ano": economia_r * 12,
        "economia_pct": percentual(economia_r, custo_atual),
        "investimento": investimento,
        "payback_meses": payback_meses(investimento, economia_r),
        "co2_evitado_kg_ano": co2_kg(energia_compensada * 12),
        "conta_nova_mes": custo_atual - economia_r,
    }


def solucao_solar_assinatura(consumo_kwh_mes, tarifa, ligacao="trifasico"):
    p = PREMISSAS
    minimo = p["custo_disponibilidade_kwh"][ligacao]
    energia_compensavel = max(consumo_kwh_mes - minimo, 0)
    economia_r = custo_reais(energia_compensavel, tarifa) * p["desconto_assinatura"]
    custo_atual = custo_reais(consumo_kwh_mes, tarifa)
    return {
        "nome": "3. Energia solar por assinatura [RENOVÁVEL]",
        "renovavel": True,
        "desconto_pct": p["desconto_assinatura"] * 100,
        "economia_kwh_mes": energia_compensavel,
        "economia_r_mes": economia_r,
        "economia_r_ano": economia_r * 12,
        "economia_pct": percentual(economia_r, custo_atual),
        "investimento": 0.0,
        "payback_meses": 0.0,
        "co2_evitado_kg_ano": co2_kg(energia_compensavel * 12),
        "conta_nova_mes": custo_atual - economia_r,
    }


def simular(itens_perfil, tarifa_sem_impostos, ligacao):
    tarifa = tarifa_final(tarifa_sem_impostos)
    itens = montar_itens(itens_perfil)
    base = cenario_base(itens, tarifa)
    return {
        "tarifa_sem_impostos": tarifa_sem_impostos,
        "tarifa_final": tarifa,
        "ligacao": ligacao,
        "itens": itens,
        "base": base,
        "led": solucao_led(itens, tarifa),
        "solar": solucao_paineis_solares(base["kwh_mes"], tarifa, ligacao),
        "assinatura": solucao_solar_assinatura(base["kwh_mes"], tarifa, ligacao),
    }


def simular_pela_conta(valor_conta, tarifa_sem_impostos, ligacao):
    tarifa = tarifa_final(tarifa_sem_impostos)
    kwh = valor_conta / tarifa if tarifa > 0 else 0.0
    return {
        "tarifa_sem_impostos": tarifa_sem_impostos,
        "tarifa_final": tarifa,
        "ligacao": ligacao,
        "kwh_mes": kwh,
        "custo_mes": valor_conta,
        "solar": solucao_paineis_solares(kwh, tarifa, ligacao),
        "assinatura": solucao_solar_assinatura(kwh, tarifa, ligacao),
    }
