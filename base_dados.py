DISTRIBUIDORAS = {
    "ELETROPAULO":   {"uf": "SP", "nome": "Enel São Paulo (ex-Eletropaulo)"},
    "CPFL-PAULISTA": {"uf": "SP", "nome": "CPFL Paulista"},
    "EDP SP":        {"uf": "SP", "nome": "EDP São Paulo"},
    "ELEKTRO":       {"uf": "SP", "nome": "Neoenergia Elektro"},
}

IRRADIACAO_SP = 5.06

PREMISSAS = {
    "fator_tributos": 1.30,
    "custo_disponibilidade_kwh": {"monofasico": 30, "bifasico": 50, "trifasico": 100},
    "performance_ratio": 0.78,
    "potencia_modulo_kw": 0.55,
    "custo_kwp_reais": 4000.00,
    "area_m2_por_kwp": 5.5,
    "perda_fio_b": 0.17,
    "desconto_assinatura": 0.15,
    "fator_co2_kg_kwh": 0.0545,
}

EQUIPAMENTOS = {
    "lampada": {
        "nome": "Lâmpada fluorescente tubular 40 W (com reator)",
        "potencia_base": 48,
        "potencia_led": 18,
        "custo_led": 35.00,
        "fonte": "INMETRO - PBE Lâmpadas LED (ESTIMADO)",
    },
    "freezer": {
        "nome": "Freezer / expositor refrigerado (compressor ~16h/dia)",
        "potencia_base": 320,
        "fonte": "INMETRO - PBE Refrigeradores Comerciais (ESTIMADO)",
    },
    "ar_condicionado": {
        "nome": "Ar-condicionado split 12.000 BTU",
        "potencia_base": 1100,
        "fonte": "INMETRO - PBE Condicionadores de Ar (ESTIMADO)",
    },
    "computador_pdv": {
        "nome": "Computador do caixa (PDV) + impressora",
        "potencia_base": 150,
        "fonte": "Etiqueta típica de fabricantes (ESTIMADO)",
    },
}

PERFIS_COMERCIO = {
    "mercadinho": {
        "nome": "Mercadinho / mercearia de bairro (SP)",
        "ligacao": "trifasico",
        "itens": {
            "lampada": (12, 12, 26),
            "freezer": (3, 16, 30),
            "ar_condicionado": (1, 8, 26),
            "computador_pdv": (1, 12, 26),
        },
    },
    "padaria": {
        "nome": "Padaria / lanchonete pequena (SP)",
        "ligacao": "trifasico",
        "itens": {
            "lampada": (10, 14, 26),
            "freezer": (2, 16, 30),
            "ar_condicionado": (1, 8, 26),
            "computador_pdv": (1, 14, 26),
        },
    },
    "salao": {
        "nome": "Salão de beleza / barbearia (SP)",
        "ligacao": "bifasico",
        "itens": {
            "lampada": (10, 10, 26),
            "ar_condicionado": (1, 9, 26),
            "computador_pdv": (1, 10, 26),
        },
    },
}

FONTES = [
    ("ANEEL - Dados Abertos: Tarifas de Aplicação das Distribuidoras (SP - B3)",
     "https://dadosabertos.aneel.gov.br/dataset/tarifas-distribuidoras-energia-eletrica"),
    ("ANEEL - Resolução Normativa nº 1.000/2021 (custo de disponibilidade)",
     "https://www2.aneel.gov.br/cedoc/ren20211000.html"),
    ("Lei nº 14.300/2022 - Marco Legal da Micro e Minigeração Distribuída",
     "https://www.planalto.gov.br/ccivil_03/_ato2019-2022/2022/lei/l14300.htm"),
    ("INPE/LABREN - Atlas Brasileiro de Energia Solar, 2ª ed. (2017)",
     "https://labren.ccst.inpe.br/atlas_2017.html"),
    ("INMETRO / PROCEL - Tabelas de Eficiência Energética (PBE)",
     "https://www.gov.br/inmetro/pt-br/assuntos/avaliacao-da-conformidade/programa-brasileiro-de-etiquetagem/tabelas-de-eficiencia-energetica"),
    ("MCTI - Fatores de emissão de CO2 do Sistema Interligado Nacional",
     "https://www.gov.br/mcti/pt-br/acompanhe-o-mcti/sirene/dados-e-ferramentas/fatores-de-emissao"),
]
