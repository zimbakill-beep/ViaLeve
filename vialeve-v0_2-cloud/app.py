import streamlit as st
from typing import Dict, Any, Tuple, List

st.set_page_config(page_title="ViaLeve - Pré-elegibilidade", page_icon="💊", layout="centered")

# ------------------------------
# Utilidades
# ------------------------------
def init_state():
    defaults = {
        "step": 0,
        "answers": {},
        "eligibility": None,
        "exclusion_reasons": [],
        "consent_ok": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def next_step():
    st.session_state.step += 1

def prev_step():
    st.session_state.step -= 1

def reset_flow():
    for k in list(st.session_state.keys()):
        del st.session_state[k]
    init_state()

# ------------------------------
# Regras (expandido v0.2)
# ------------------------------
EXCIPIENTES_COMUNS = [
    "Polietilenoglicol (PEG)",
    "Metacresol / Fenol",
    "Fosfatos (fosfato dissódico etc.)",
    "Látex (agulhas/rolhas)",
    "Carboximetilcelulose",
    "Trometamina (TRIS)",
]

def evaluate_rules(a: Dict[str, Any]) -> Tuple[str, List[str]]:
    """
    Aplica regras de triagem inicial (v0.2). NÃO substitui avaliação médica.
    Retorna (status, motivos_exclusao)
    """
    exclusion = []

    def g(key, default=None):
        return a.get(key, default)

    # Idade mínima
    if g("idade") is not None and g("idade") < 18:
        exclusion.append("Menor de 18 anos.")

    # Gravidez / Amamentação
    if g("gravidez") == "sim":
        exclusion.append("Gestação em curso.")
    if g("amamentando") == "sim":
        exclusion.append("Amamentação em curso.")

    # Oncologia atual
    if g("tratamento_cancer") == "sim":
        exclusion.append("Tratamento oncológico ativo.")

    # Pancreatite prévia
    if g("pancreatite_previa") == "sim":
        exclusion.append("História de pancreatite prévia.")

    # MTC / MEN2
    if g("historico_mtc_men2") == "sim":
        exclusion.append("História pessoal/familiar de carcinoma medular de tireoide (MTC) ou MEN2.")

    # Alergia/hipersensibilidade a GLP-1 ou excipientes
    if g("alergia_glp1") == "sim":
        exclusion.append("Hipersensibilidade conhecida a análogos de GLP-1.")
    if g("alergias_componentes"):
        exclusion.append("Alergia relatada a excipientes comuns de formulações injetáveis (ver detalhes).")

    # Doenças GI relevantes
    if g("gi_grave") == "sim":
        exclusion.append("Doença gastrointestinal grave ativa.")
    if g("gastroparesia") == "sim":
        exclusion.append("Gastroparesia diagnosticada.")

    # Vesícula biliar
    if g("colecistite_12m") == "sim":
        exclusion.append("Colecistite/colelitíase sintomática nos últimos 12 meses.")

    # Função renal/hepática
    if g("insuf_renal") in ["moderada", "grave"]:
        exclusion.append("Insuficiência renal moderada/grave (necessita avaliação médica antes de prosseguir).")
    if g("insuf_hepatica") in ["moderada", "grave"]:
        exclusion.append("Insuficiência hepática moderada/grave (necessita avaliação médica).")

    # Transtorno alimentar ativo
    if g("transtorno_alimentar") == "sim":
        exclusion.append("Transtorno alimentar ativo.")

    # Uso de fármacos que impactam conduta
    if g("uso_corticoide") == "sim":
        exclusion.append("Uso crônico de corticoide (requer ajuste/avaliação médica).")
    if g("antipsicoticos") == "sim":
        exclusion.append("Uso de antipsicóticos (requer avaliação).")

    # IMC
    imc = None
    peso = g("peso")
    altura = g("altura")
    if peso and altura:
        try:
            imc = float(peso) / (float(altura) ** 2)
            st.session_state.answers["imc"] = round(imc, 1)
        except Exception:
            pass

    if imc is not None:
        if imc < 27 and g("tem_comorbidades") == "nao":
            exclusion.append("IMC < 27 sem comorbidades relevantes.")

    status = "excluido" if exclusion else "potencialmente_elegivel"
    return status, exclusion

# ------------------------------
# UI
# ------------------------------
init_state()

st.markdown("### ViaLeve — Pré-elegibilidade de tratamento farmacológico para emagrecimento")
st.caption("Protótipo interativo • Este fluxo é uma triagem inicial e **não** substitui avaliação médica.")

with st.expander("Termo de ciência (resumo)", expanded=True):
    st.write(
        "- Este questionário é uma **pré-triagem** para avaliar **elegibilidade inicial**.\n"
        "- As respostas serão verificadas por um **médico** antes de qualquer prescrição.\n"
        "- Em caso de dúvida clínica, procure atendimento.\n"
    )

# Barra de progresso (6 passos)
total_steps = 6
progress = (st.session_state.step + 1) / total_steps
st.progress(progress)

# ------------------------------
# Step 0 — Identificação
# ------------------------------
if st.session_state.step == 0:
    st.subheader("1) Identificação")
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome completo *", value=st.session_state.answers.get("nome", ""))
        email = st.text_input("E-mail *", value=st.session_state.answers.get("email", ""))
    with col2:
        idade = st.number_input("Idade *", min_value=10, max_value=100, step=1, value=st.session_state.answers.get("idade", 30))
        sexo = st.selectbox("Sexo", ["feminino", "masculino", "prefiro não informar"], index=["feminino", "masculino", "prefiro não informar"].index(st.session_state.answers.get("sexo", "feminino")) if st.session_state.answers.get("sexo") else 0)

    st.session_state.answers.update({"nome": nome, "email": email, "idade": idade, "sexo": sexo})

    ok = bool(nome.strip()) and bool(email.strip())
    st.button("Continuar ▶️", on_click=next_step, disabled=not ok)

# ------------------------------
# Step 1 — Medidas e comorbidades
# ------------------------------
elif st.session_state.step == 1:
    st.subheader("2) Medidas e comorbidades")
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Peso (kg) *", min_value=30.0, max_value=400.0, step=0.1, value=st.session_state.answers.get("peso", 90.0))
        tem_comorbidades = st.radio("Possui comorbidades relevantes (DM2, HAS, apneia, dislipidemia etc.)?", options=["sim", "nao"], index=0 if st.session_state.answers.get("tem_comorbidades","sim")=="sim" else 1, horizontal=True)
    with col2:
        altura = st.number_input("Altura (m) *", min_value=1.3, max_value=2.2, step=0.01, value=st.session_state.answers.get("altura", 1.70))
        comorbidades = st.text_area("Se sim, quais comorbidades?", value=st.session_state.answers.get("comorbidades", ""))

    st.session_state.answers.update({"peso": peso, "altura": altura, "tem_comorbidades": tem_comorbidades, "comorbidades": comorbidades})

    cols = st.columns(2)
    with cols[0]:
        st.button("⬅️ Voltar", on_click=prev_step)
    with cols[1]:
        st.button("Continuar ▶️", on_click=next_step)

# ------------------------------
# Step 2 — Contraindicações principais (GLP-1 e correlatos)
# ------------------------------
elif st.session_state.step == 2:
    st.subheader("3) Contraindicações principais")
    col1, col2 = st.columns(2)
    with col1:
        gravidez = st.radio("Está grávida?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("gravidez","nao")=="nao" else 1)
        amamentando = st.radio("Está amamentando?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("amamentando","nao")=="nao" else 1)
        tratamento_cancer = st.radio("Em tratamento oncológico ativo?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("tratamento_cancer","nao")=="nao" else 1)
        gi_grave = st.radio("Doença gastrointestinal grave ativa?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("gi_grave","nao")=="nao" else 1)
        gastroparesia = st.radio("Diagnóstico de gastroparesia?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("gastroparesia","nao")=="nao" else 1)
    with col2:
        pancreatite_previa = st.radio("Já teve pancreatite?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("pancreatite_previa","nao")=="nao" else 1)
        historico_mtc_men2 = st.radio("História pessoal/familiar de MTC/MEN2?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("historico_mtc_men2","nao")=="nao" else 1)
        colecistite_12m = st.radio("Colecistite/colelitíase sintomática nos últimos 12 meses?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("colecistite_12m","nao")=="nao" else 1)
        outras_contra = st.text_area("Outras condições clínicas relevantes?")

    st.session_state.answers.update({
        "gravidez": gravidez,
        "amamentando": amamentando,
        "tratamento_cancer": tratamento_cancer,
        "gi_grave": gi_grave,
        "gastroparesia": gastroparesia,
        "pancreatite_previa": pancreatite_previa,
        "historico_mtc_men2": historico_mtc_men2,
        "colecistite_12m": colecistite_12m,
        "outras_contra": outras_contra,
    })

    cols = st.columns(2)
    with cols[0]:
        st.button("⬅️ Voltar", on_click=prev_step)
    with cols[1]:
        st.button("Continuar ▶️", on_click=next_step)

# ------------------------------
# Step 3 — Função renal/hepática, uso de fármacos e alergias a componentes
# ------------------------------
elif st.session_state.step == 3:
    st.subheader("4) Condições adicionais e alergias a componentes")
    col1, col2 = st.columns(2)
    with col1:
        insuf_renal = st.selectbox("Função renal:", ["normal", "leve", "moderada", "grave"], index=["normal","leve","moderada","grave"].index(st.session_state.answers.get("insuf_renal","normal")) if st.session_state.answers.get("insuf_renal") else 0)
        insuf_hepatica = st.selectbox("Função hepática:", ["normal", "leve", "moderada", "grave"], index=["normal","leve","moderada","grave"].index(st.session_state.answers.get("insuf_hepatica","normal")) if st.session_state.answers.get("insuf_hepatica") else 0)
        transtorno_alimentar = st.radio("Transtorno alimentar ativo (AN/BN/TCAP)?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("transtorno_alimentar","nao")=="nao" else 1)
        uso_corticoide = st.radio("Uso crônico de corticoide?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("uso_corticoide","nao")=="nao" else 1)
        antipsicoticos = st.radio("Uso de antipsicóticos atualmente?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("antipsicoticos","nao")=="nao" else 1)
    with col2:
        alergia_glp1 = st.radio("Alergia conhecida a GLP-1?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("alergia_glp1","nao")=="nao" else 1)
        alergias_componentes = st.multiselect("Alguma alergia a componentes comuns de injetáveis?", options=EXCIPIENTES_COMUNS, default=st.session_state.answers.get("alergias_componentes", []))
        outros_componentes = st.text_input("Outros componentes ou excipientes aos quais é alérgico?")

    st.session_state.answers.update({
        "insuf_renal": insuf_renal,
        "insuf_hepatica": insuf_hepatica,
        "transtorno_alimentar": transtorno_alimentar,
        "uso_corticoide": uso_corticoide,
        "antipsicoticos": antipsicoticos,
        "alergia_glp1": alergia_glp1,
        "alergias_componentes": alergias_componentes,
        "outros_componentes": outros_componentes,
    })

    cols = st.columns(2)
    with cols[0]:
        st.button("⬅️ Voltar", on_click=prev_step)
    with cols[1]:
        st.button("Continuar ▶️", on_click=next_step)

# ------------------------------
# Step 4 — Histórico de fármacos e objetivos
# ------------------------------
elif st.session_state.step == 4:
    st.subheader("5) Histórico de tratamento e objetivos")
    col1, col2 = st.columns(2)
    with col1:
        usou_antes = st.radio("Já usou medicação para emagrecimento?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("usou_antes","nao")=="nao" else 1)
        quais = st.multiselect("Quais?", options=["Semaglutida","Tirzepatida","Liraglutida","Orlistate","Bupropiona/Naltrexona","Outros"], default=st.session_state.answers.get("quais", []))
        efeitos = st.text_area("Teve efeitos colaterais? Quais?")
    with col2:
        objetivo = st.selectbox("Objetivo principal", options=["Perda de peso","Controle de comorbidades","Manutenção"], index=["Perda de peso","Controle de comorbidades","Manutenção"].index(st.session_state.answers.get("objetivo","Perda de peso")) if st.session_state.answers.get("objetivo") else 0)
        gestao_expectativas = st.slider("Quão pronto(a) está para mudanças de rotina (0-10)?", 0, 10, value=st.session_state.answers.get("pronto_mudar", 7))

    st.session_state.answers.update({
        "usou_antes": usou_antes,
        "quais": quais,
        "efeitos": efeitos,
        "objetivo": objetivo,
        "pronto_mudar": gestao_expectativas,
    })

    cols = st.columns(2)
    with cols[0]:
        st.button("⬅️ Voltar", on_click=prev_step)
    with cols[1]:
        if st.button("Calcular elegibilidade ✅"):
            status, reasons = evaluate_rules(st.session_state.answers)
            st.session_state.eligibility = status
            st.session_state.exclusion_reasons = reasons
            next_step()

# ------------------------------
# Step 5 — Resultado + Consentimentos
# ------------------------------
elif st.session_state.step == 5:
    st.subheader("6) Resultado da pré-triagem")

    status = st.session_state.eligibility
    reasons = st.session_state.exclusion_reasons

    if status == "potencialmente_elegivel":
        st.success("Resultado: **Potencialmente elegível** para avaliação médica de tratamento farmacológico.")
        if "imc" in st.session_state.answers:
            st.write(f"IMC estimado: **{st.session_state.answers['imc']}**")
        st.info("Próximos passos:\n- Agendar consulta médica para confirmação da indicação e prescrição.\n- Avaliação nutricional e plano de mudanças comportamentais.\n- Exames laboratoriais conforme necessidade clínica.")
    else:
        st.error("Resultado: **Necessita avaliação médica antes de prosseguir**.")
        if reasons:
            st.write("Motivos identificados na pré-triagem:")
            for r in reasons:
                st.write(f"- {r}")
        st.warning("Esta é uma triagem inicial. Em muitos casos, é possível ajustar o plano terapêutico após avaliação especializada.")

    st.divider()
    st.subheader("Consentimento e autorização")
    with st.expander("Leia o termo completo", expanded=False):
        st.markdown("""
**Termo de Consentimento Informado e Autorização de Teleconsulta (ViaLeve)**

1. **Natureza do serviço**: declaro compreender que este questionário constitui **pré‑triagem** e **não** substitui consulta médica presencial.
2. **Riscos e benefícios**: entendo que tratamentos farmacológicos para emagrecimento podem apresentar efeitos adversos (náuseas, vômitos, dor abdominal, colelitíase, pancreatite, entre outros) e que a indicação depende de avaliação clínica individualizada.
3. **Alternativas**: reconheço que existem alternativas como mudanças de estilo de vida, terapia nutricional, atividade física e, quando cabível, procedimentos cirúrgicos.
4. **Privacidade e dados (LGPD)**: autorizo o tratamento dos meus dados pessoais e de saúde para fins de prestação do serviço, conforme política de privacidade da ViaLeve, com medidas de segurança e direito de revogação do consentimento.
5. **Teleconsulta**: autorizo a realização de **consulta on‑line** (telemedicina) para avaliação e acompanhamento, ciente de suas limitações e da possibilidade de conversão para consulta presencial quando necessário.
6. **Veracidade das informações**: declaro que as informações fornecidas são verdadeiras e completas.
7. **Aceite eletrônico**: ciente de que meu aceite eletrônico possui validade jurídica.
        """)

    c1, c2 = st.columns(2)
    with c1:
        aceite_termo = st.checkbox("Li e **aceito** o Termo de Consentimento.", value=st.session_state.answers.get("aceite_termo", False))
        autoriza_teleconsulta = st.checkbox("**Autorizo** a consulta on‑line (telemedicina).", value=st.session_state.answers.get("autoriza_teleconsulta", False))
    with c2:
        lgpd = st.checkbox("Autorizo o tratamento dos meus dados (LGPD).", value=st.session_state.answers.get("lgpd", False))
        veracidade = st.checkbox("Declaro veracidade das informações.", value=st.session_state.answers.get("veracidade", False))

    st.session_state.answers.update({
        "aceite_termo": aceite_termo,
        "autoriza_teleconsulta": autoriza_teleconsulta,
        "lgpd": lgpd,
        "veracidade": veracidade,
    })

    st.session_state.consent_ok = all([aceite_termo, autoriza_teleconsulta, lgpd, veracidade])

    st.caption("Você receberá um e‑mail com este resumo.")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("⬅️ Voltar", on_click=prev_step)
    with col2:
        if st.button("Reiniciar fluxo 🔄"):
            reset_flow()
            st.experimental_rerun()
    with col3:
        st.download_button(
            "Baixar respostas (JSON)",
            data=str(st.session_state.answers),
            file_name="vialeve_respostas.json",
            mime="application/json",
            disabled=not st.session_state.consent_ok
        )

st.markdown("---")
st.caption("ViaLeve • Protótipo v0.2 — uso interno • Desenvolvido em Streamlit (Python)")