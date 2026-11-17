import sys

import aneel_api
import assistente
import calculos
from base_dados import EQUIPAMENTOS, PERFIS_COMERCIO

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


def perguntar(texto, padrao=None):
    sufixo = f" [{padrao}]" if padrao is not None else ""
    resposta = input(f"{texto}{sufixo}: ").strip()
    if assistente.contem_dado_pessoal(resposta):
        print("  ! Não precisamos de dados pessoais (CPF, telefone, e-mail). Tente de novo.")
        return perguntar(texto, padrao)
    return resposta if resposta else (str(padrao) if padrao is not None else "")


def perguntar_numero(texto, padrao=None, minimo=0.0, maximo=1e9, inteiro=False):
    while True:
        bruto = perguntar(texto, padrao).replace("R$", "").replace(" ", "")
        if "," in bruto:
            bruto = bruto.replace(".", "").replace(",", ".")
        try:
            valor = int(float(bruto)) if inteiro else float(bruto)
            if minimo <= valor <= maximo:
                return valor
        except ValueError:
            pass
        print(f"  ! Digite um número entre {minimo:g} e {maximo:g}.")


def perguntar_sim_nao(texto, padrao="s"):
    while True:
        r = assistente._normalizar(perguntar(texto + " (s/n)", padrao))
        if r in ("s", "sim"):
            return True
        if r in ("n", "nao"):
            return False
        print("  ! Responda s ou n.")


def escolher(titulo, opcoes):
    print(f"\n{titulo}")
    for n, (_, texto) in enumerate(opcoes, 1):
        print(f"  {n}. {texto}")
    n = perguntar_numero("Escolha o número", 1, 1, len(opcoes), inteiro=True)
    return opcoes[n - 1][0]


def obter_tarifas():
    tarifas = aneel_api.carregar_tarifas()
    if not tarifas:
        print("Baixando tarifas de SP na ANEEL...")
        aneel_api.atualizar_tarifas()
        tarifas = aneel_api.carregar_tarifas()
    if not tarifas:
        print("Não foi possível obter tarifas da ANEEL. Verifique a internet.")
        sys.exit(1)
    return tarifas


def escolher_distribuidora_sp(tarifas):
    opcoes = [
        (s, f"{t['distribuidora']} - {assistente.reais_kwh(t['tarifa_r_kwh_sem_impostos'])}/kWh (ANEEL, s/ impostos)")
        for s, t in tarifas.items()
    ]
    sigla = escolher("Qual é a sua distribuidora em São Paulo (SP)?", opcoes)
    return tarifas[sigla]


def escolher_ligacao(padrao):
    opcoes = [("monofasico", "Monofásica (2 fios)"), ("bifasico", "Bifásica (3 fios)"),
              ("trifasico", "Trifásica (4 fios - comum em comércio)")]
    if perguntar_sim_nao(f"\nUsar ligação padrão ({padrao})?", "s"):
        return padrao
    return escolher("Tipo de ligação:", opcoes)


def diagnostico_completo(tarifas):
    print("\n=== DIAGNÓSTICO DO COMÉRCIO EM SP ===")
    dist = escolher_distribuidora_sp(tarifas)
    chave = escolher("Tipo de comércio:", [(k, v["nome"]) for k, v in PERFIS_COMERCIO.items()])
    perfil = PERFIS_COMERCIO[chave]
    itens = dict(perfil["itens"])

    print("\nAparelhos padrão do perfil:")
    for eq_id, (qtd, horas, dias) in itens.items():
        print(f"  - {EQUIPAMENTOS[eq_id]['nome']}: {qtd} un., {horas} h/dia, {dias} dias/mês")

    if perguntar_sim_nao("\nAjustar quantidades e horas para o seu caso?", "n"):
        ajustados = {}
        for eq_id, (qtd, horas, dias) in itens.items():
            q = perguntar_numero(f"  Qtd de {EQUIPAMENTOS[eq_id]['nome']}", qtd, 0, 500, inteiro=True)
            if q == 0:
                continue
            h = perguntar_numero("  Horas/dia", horas, 0.1, 24)
            d = perguntar_numero("  Dias/mês", dias, 1, 31, inteiro=True)
            ajustados[eq_id] = (q, h, d)
        itens = ajustados or itens

    ligacao = escolher_ligacao(perfil["ligacao"])
    proprio = perguntar_sim_nao("\nO imóvel do comércio é PRÓPRIO?", "s")
    dinheiro = perguntar_sim_nao("Tem capital ou crédito para investir agora?", "s")

    sim = calculos.simular(itens, dist["tarifa_r_kwh_sem_impostos"], ligacao)
    print("\n" + assistente.gerar_relatorio(sim, perfil["nome"], dist, proprio, dinheiro))
    salvar(sim, perfil["nome"], dist, "diagnostico_sp")


def simulacao_rapida(tarifas):
    print("\n=== SIMULAÇÃO RÁPIDA PELA CONTA DE LUZ (SP) ===")
    dist = escolher_distribuidora_sp(tarifas)
    valor = perguntar_numero("Valor médio da conta de luz (R$/mês)", 1000, 50, 100000)
    ligacao = escolher_ligacao("trifasico")
    proprio = perguntar_sim_nao("O imóvel é PRÓPRIO?", "s")
    sim = calculos.simular_pela_conta(valor, dist["tarifa_r_kwh_sem_impostos"], ligacao)
    print("\n" + assistente.gerar_relatorio_rapido(sim, dist, proprio))
    salvar(sim, "Simulação pela conta (SP)", dist, "rapida_sp")


def duvidas():
    print("\n=== DÚVIDAS SOBRE ENERGIA === (digite 'voltar' para sair)")
    while True:
        pergunta = input("\nSua dúvida: ").strip()
        if assistente._normalizar(pergunta) in ("voltar", "sair", "0", ""):
            return
        print(assistente.responder_duvida(pergunta))


def ver_tarifas(tarifas):
    print("\nTARIFAS ANEEL (SP) - Subgrupo B3 Comercial Convencional (sem impostos)")
    print(f"{'Distribuidora':<36}{'TUSD R$/MWh':>12}{'TE R$/MWh':>11}{'R$/kWh':>9}  Vigência")
    for t in tarifas.values():
        print(f"{t['distribuidora'][:35]:<36}{t['tusd_r_mwh']:>12.2f}{t['te_r_mwh']:>11.2f}"
              f"{t['tarifa_r_kwh_sem_impostos']:>9.4f}  {t['inicio_vigencia']} a {t['fim_vigencia']}")


def salvar(sim, nome_perfil, dist, prefixo):
    arquivos = assistente.exportar(sim, nome_perfil, dist, prefixo)
    print("\nDados salvos em:")
    for a in arquivos:
        print(f"  - {a}")


def demo(tarifas):
    dist = tarifas.get("ELETROPAULO") or next(iter(tarifas.values()))
    perfil = PERFIS_COMERCIO["mercadinho"]
    sim = calculos.simular(perfil["itens"], dist["tarifa_r_kwh_sem_impostos"], perfil["ligacao"])
    print(assistente.gerar_relatorio(sim, perfil["nome"], dist, imovel_proprio=True, tem_dinheiro=True))
    salvar(sim, perfil["nome"], dist, "demo_mercadinho_sp")


def menu():
    tarifas = obter_tarifas()
    print("=" * 78)
    print("  CITIZEN ASSIST AI - Soluções em Energia para Pequenos Comerciantes (SP)")
    print("=" * 78)
    while True:
        print("\nO que você quer fazer?")
        print("  1. Diagnóstico do comércio em SP (consumo + 3 soluções)")
        print("  2. Simulação rápida pelo valor da conta de luz")
        print("  3. Tirar dúvidas sobre energia (LED, solar, Lei 14.300...)")
        print("  4. Ver tarifas oficiais da ANEEL em SP")
        print("  5. Atualizar tarifas de SP na ANEEL (online)")
        print("  6. Fontes e limitações")
        print("  0. Sair")
        opcao = perguntar("Opção", "1")
        if opcao == "1":
            diagnostico_completo(tarifas)
        elif opcao == "2":
            simulacao_rapida(tarifas)
        elif opcao == "3":
            duvidas()
        elif opcao == "4":
            ver_tarifas(tarifas)
        elif opcao == "5":
            aneel_api.atualizar_tarifas()
            tarifas = obter_tarifas()
        elif opcao == "6":
            print("\nFONTES:\n" + assistente.listar_fontes())
            print("\n" + assistente.AVISO_LIMITACOES)
        elif opcao == "0":
            print("Até logo!")
            break
        else:
            print("  ! Opção inválida.")


if __name__ == "__main__":
    try:
        if "--demo" in sys.argv:
            demo(obter_tarifas())
        else:
            menu()
    except (KeyboardInterrupt, EOFError):
        print("\nAté logo!")
