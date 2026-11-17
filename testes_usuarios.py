import sys

import aneel_api
import assistente
import calculos
from base_dados import PERFIS_COMERCIO

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass


REGISTROS_TESTES_USUARIOS = [
    {
        "id": "TU-01",
        "perfil_anonimizado": "Comerciante A - Dona de mercadinho em São Paulo (SP), imóvel próprio",
        "situacao_testada": "Diagnóstico do perfil 'mercadinho' na Enel SP (ELETROPAULO), comparando LED, painéis solares e assinatura.",
        "comentario_recebido": "Não tinha dinheiro para colocar placas solares de imediato e queria saber o que fazer gastando pouco primeiro.",
        "ajuste_realizado": "Destacada a troca das 12 lâmpadas para LED como PASSO 1 imediato (custo ~R$ 420, retorno em ~3,6 meses).",
    },
    {
        "id": "TU-02",
        "perfil_anonimizado": "Comerciante B - Dono de salão/barbearia em Campinas (SP), imóvel alugado",
        "situacao_testada": "Diagnóstico do perfil 'salao' na CPFL Paulista em ponto comercial alugado (sem autorização para obra no telhado).",
        "comentario_recebido": "Perguntou como usar energia renovável sem poder instalar placas e teve dúvida nas siglas kWh e kWp.",
        "ajuste_realizado": "Incluída a Solar por Assinatura como Solução 3 (recomendada quando imovel_proprio=False) e adicionado glossário simples.",
    },
    {
        "id": "TU-03",
        "perfil_anonimizado": "Comerciante C - Dona de padaria no ABC Paulista (SP), sabia apenas o valor da conta",
        "situacao_testada": "Simulação rápida pelo valor da conta (R$ 1.200/mês) e dúvida na FAQ sobre Lei 14.300 e diferença da tarifa ANEEL.",
        "comentario_recebido": "Não sabia a potência dos aparelhos e estranhou a diferença entre a tarifa da ANEEL e o boleto final.",
        "ajuste_realizado": "Criada a Opção 2 (Simulação pela conta de luz) e exibição lado a lado da tarifa ANEEL s/ impostos e c/ impostos (x1,30).",
    },
    {
        "id": "TU-04",
        "perfil_anonimizado": "Comerciante D - Dono de lanchonete em São José dos Campos (SP), preocupado com privacidade",
        "situacao_testada": "Tentativa de digitar CNPJ e telefone na consulta da FAQ na distribuidora EDP SP.",
        "comentario_recebido": "Teve receio de informar dados da empresa ou telefone por medo de spam.",
        "ajuste_realizado": "Implementado filtro LGPD automático (`contem_dado_pessoal`) que bloqueia CPF, CNPJ, telefone e e-mail.",
    },
]


def executar_testes_tecnicos():
    print("=" * 78)
    print("  1) VERIFICAÇÃO TÉCNICA AUTOMATIZADA (SP - ANEEL, 3 SOLUÇÕES E LGPD)")
    print("=" * 78)

    tarifas = aneel_api.carregar_tarifas()
    assert len(tarifas) == 4 and all(t["uf"] == "SP" for t in tarifas.values()), "Deve conter apenas as 4 distribuidoras de SP."
    print(f"[OK] Base ANEEL (SP) carregada com {len(tarifas)} distribuidoras.")

    kwh_teste = calculos.energia_kwh(1000, 10, 30)
    assert abs(kwh_teste - 300.0) < 1e-6
    print(f"[OK] Fórmula de energia validada: 1000 W x 10 h x 30 dias = {kwh_teste:.1f} kWh.")

    dist_sp = tarifas["ELETROPAULO"]
    sim = calculos.simular(PERFIS_COMERCIO["mercadinho"]["itens"], dist_sp["tarifa_r_kwh_sem_impostos"], "trifasico")
    assert sim["led"]["economia_r_mes"] > 0
    assert sim["solar"]["renovavel"] is True and sim["solar"]["kwp"] > 0
    assert sim["assinatura"]["renovavel"] is True and sim["assinatura"]["investimento"] == 0.0
    print(f"[OK] 3 Soluções (Mercadinho Enel SP): LED = R$ {sim['led']['economia_r_mes']:.2f}/mês | "
          f"Painéis ({sim['solar']['kwp']:.2f} kWp) = R$ {sim['solar']['economia_r_mes']:.2f}/mês | "
          f"Assinatura = R$ {sim['assinatura']['economia_r_mes']:.2f}/mês.")

    rec_alugado = "\n".join(assistente.recomendacao(sim, imovel_proprio=False, tem_dinheiro=True))
    assert "ASSINATURA" in rec_alugado
    print("[OK] Imóvel alugado recomenda automaticamente Solar por Assinatura.")

    assert assistente.contem_dado_pessoal("CPF 123.456.789-00") is True
    assert assistente.contem_dado_pessoal("qual a lei 14.300?") is False
    print("[OK] Filtro LGPD validado.")


def exibir_registros_usuarios():
    print("\n" + "=" * 78)
    print("  2) REGISTRO DOS TESTES COM USUÁRIOS (SP) E AJUSTES REALIZADOS")
    print("=" * 78)
    for t in REGISTROS_TESTES_USUARIOS:
        print(f"\n[{t['id']}] {t['perfil_anonimizado']}")
        print(f"  - Situação testada : {t['situacao_testada']}")
        print(f"  - Comentário       : {t['comentario_recebido']}")
        print(f"  - Ajuste realizado : {t['ajuste_realizado']}")
    print("\n" + "=" * 78)
    print("Todos os testes passaram com sucesso!")


if __name__ == "__main__":
    executar_testes_tecnicos()
    exibir_registros_usuarios()
