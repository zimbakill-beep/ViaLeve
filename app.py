import os
import streamlit as st
from typing import Dict, Any, Tuple, List
from datetime import date, datetime

st.set_page_config(page_title="ViaLeve - Pré-elegibilidade", page_icon="💊", layout="centered")

# ------------------------------
# Estilo leve (toque de marca)
# ------------------------------
st.markdown("""
<style>
.small-muted { color:#6b7280; font-size:0.9rem; }
.badge { display:inline-block; padding:0.25rem 0.6rem; border-radius:999px; background:#eef2ff; }
.card { padding:1rem; border-radius:1rem; background:#f8fafc; border:1px solid #e5e7eb; }
</style>
""", unsafe_allow_html=True)

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

def calc_idade(d: date | None) -> int | None:
    if not d: 
        return None
    today = date.today()
    return today.year - d.year - ((today.month, today.day) < (d.month, d.day))

# ------------------------------
# Regras (v0.3) — mesmas do v0.2, com cálculo de idade por data de nascimento
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
    exclusion = []

    def g(key, default=None):
        return a.get(key, default)

    # idade a partir de data_nascimento (se existir)
    if g("data_nascimento"):
        try:
            dob = g("data_nascimento")
            if isinstance(dob, str):
                dob = date.fromisoformat(dob)
            idade = calc_idade(dob)
            if idade is not None:
                a["idade"] = idade
                a["idade_calculada"] = idade
        except Exception:
            pass

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
        exclusion.append("Insuficiência renal moderada/grave (necessita avaliação médica).")
    if g("insuf_hepatica") in ["moderada", "grave"]:
        exclusion.append("Insuficiência hepática moderada/grave (necessita avaliação médica).")

    # Transtorno alimentar ativo
    if g("transtorno_alimentar") == "sim":
        exclusion.append("Transtorno alimentar ativo.")

    # Uso de fármacos que impactam conduta
    if g("uso_corticoide") == "sim":
        exclusion.append("Uso crônico de corticoide (requer avaliação).")
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

st.markdown("## ViaLeve — Pré‑elegibilidade 💊")
st.caption("Uma triagem rápida e acolhedora para entender se o tratamento farmacológico pode ser adequado para você.")

with st.expander("Como funciona (rapidinho)", expanded=False):
    st.write(
        "- Em 5 min você responde perguntas simples.\n"
        "- Ao final, dizemos se **parece** uma boa ideia seguir para consulta.\n"
        "- Depois um **médico** confere tudo antes de qualquer prescrição."
    )

# Barra de progresso (6 passos)
total_steps = 6
progress = (st.session_state.step + 1) / total_steps
st.progress(progress)

# ------------------------------
# Step 0 — Identificação
# ------------------------------
if st.session_state.step == 0:
    st.subheader("1) Quem é você? 🙂")
    col1, col2 = st.columns(2)
    with col1:
        nome = st.text_input("Nome completo *", value=st.session_state.answers.get("nome", ""), help="Como aparece em seus documentos.")
        email = st.text_input("E‑mail *", value=st.session_state.answers.get("email", ""), help="Usaremos para enviar seu resumo e próximos passos.")
    with col2:
        # Data de nascimento em vez de idade
        default_dob = st.session_state.answers.get("data_nascimento")
        from datetime import date
        if isinstance(default_dob, str):
            try:
                default_dob = date.fromisoformat(default_dob)
            except Exception:
                default_dob = date(1990,1,1)
        elif not default_dob:
            default_dob = date(1990,1,1)
        data_nascimento = st.date_input("Data de nascimento *", value=default_dob, min_value=date(1900,1,1), max_value=date.today())
        sexo = st.selectbox("Sexo (opcional)", ["feminino", "masculino", "prefiro não informar"], index=["feminino", "masculino", "prefiro não informar"].index(st.session_state.answers.get("sexo", "feminino")) if st.session_state.answers.get("sexo") else 0)

    idade_calc = calc_idade(data_nascimento)
    st.session_state.answers.update({
        "nome": nome,
        "email": email,
        "data_nascimento": str(data_nascimento),
        "idade": idade_calc,
        "idade_calculada": idade_calc,
        "sexo": sexo
    })

    # Preview amigável
    if idade_calc is not None:
        st.markdown(f"<span class='small-muted'>Idade calculada: <span class='badge'><b>{idade_calc}</b> anos</span></span>", unsafe_allow_html=True)

    ok = bool(nome.strip()) and bool(email.strip())
    st.button("Continuar ▶️", on_click=next_step, disabled=not ok)

# ------------------------------
# Step 1 — Medidas e comorbidades
# ------------------------------
elif st.session_state.step == 1:
    st.subheader("2) Medidas e saúde atual 🩺")
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Peso (kg) *", min_value=30.0, max_value=400.0, step=0.1, value=st.session_state.answers.get("peso", 90.0))
        tem_comorbidades = st.radio("Possui comorbidades relevantes? (DM2, pressão alta, apneia, colesterol...)", options=["sim", "nao"], index=0 if st.session_state.answers.get("tem_comorbidades","sim")=="sim" else 1, horizontal=True)
    with col2:
        altura = st.number_input("Altura (m) *", min_value=1.3, max_value=2.2, step=0.01, value=st.session_state.answers.get("altura", 1.70))
        comorbidades = st.text_area("Se sim, quais comorbidades?", value=st.session_state.answers.get("comorbidades", ""))

    st.session_state.answers.update({"peso": peso, "altura": altura, "tem_comorbidades": tem_comorbidades, "comorbidades": comorbidades})

    # Chip de IMC (se possível)
    try:
        imc = float(peso)/(float(altura)**2)
        st.markdown(f"<div class='card'>IMC estimado: <span class='badge'><b>{imc:.1f}</b></span></div>", unsafe_allow_html=True)
    except Exception:
        pass

    cols = st.columns(2)
    with cols[0]:
        st.button("⬅️ Voltar", on_click=prev_step)
    with cols[1]:
        st.button("Continuar ▶️", on_click=next_step)

# ------------------------------
# Step 2 — Contraindicações principais (GLP-1 e correlatos)
# ------------------------------
elif st.session_state.step == 2:
    st.subheader("3) Algumas condições importantes ⚠️")
    col1, col2 = st.columns(2)
    with col1:
        gravidez = st.radio("Está grávida?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("gravidez","nao")=="nao" else 1)
        amamentando = st.radio("Está amamentando?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("amamentando","nao")=="nao" else 1)
        tratamento_cancer = st.radio("Em tratamento oncológico ativo?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("tratamento_cancer","nao")=="nao" else 1)
        gi_grave = st.radio("Doença gastrointestinal grave ativa?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("gi_grave","nao")=="nao" else 1)
        gastroparesia = st.radio("Diagnóstico de gastroparesia (esvaziamento gástrico lento)?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("gastroparesia","nao")=="nao" else 1)
    with col2:
        pancreatite_previa = st.radio("Já teve pancreatite?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("pancreatite_previa","nao")=="nao" else 1)
        historico_mtc_men2 = st.radio("História pessoal/familiar de MTC/MEN2?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("historico_mtc_men2","nao")=="nao" else 1)
        colecistite_12m = st.radio("Cólica de vesícula/colecistite nos últimos 12 meses?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("colecistite_12m","nao")=="nao" else 1)
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
    st.subheader("4) Medicações e alergias 💉")
    col1, col2 = st.columns(2)
    with col1:
        insuf_renal = st.selectbox("Como estão seus rins?", ["normal", "leve", "moderada", "grave"], index=["normal","leve","moderada","grave"].index(st.session_state.answers.get("insuf_renal","normal")) if st.session_state.answers.get("insuf_renal") else 0)
        insuf_hepatica = st.selectbox("E o fígado?", ["normal", "leve", "moderada", "grave"], index=["normal","leve","moderada","grave"].index(st.session_state.answers.get("insuf_hepatica","normal")) if st.session_state.answers.get("insuf_hepatica") else 0)
        transtorno_alimentar = st.radio("Tem transtorno alimentar ativo (anorexia/bulimia/compulsão)?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("transtorno_alimentar","nao")=="nao" else 1)
        uso_corticoide = st.radio("Usa corticoide todos os dias há mais de 3 meses?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("uso_corticoide","nao")=="nao" else 1)
        antipsicoticos = st.radio("Usa antipsicóticos atualmente?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("antipsicoticos","nao")=="nao" else 1)
    with col2:
        alergia_glp1 = st.radio("Tem alergia conhecida a remédios do tipo GLP‑1?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("alergia_glp1","nao")=="nao" else 1)
        alergias_componentes = st.multiselect("É alérgico(a) a algum destes componentes comuns?", options=[
            "Polietilenoglicol (PEG)","Metacresol / Fenol","Fosfatos (fosfato dissódico etc.)","Látex (agulhas/rolhas)","Carboximetilcelulose","Trometamina (TRIS)"
        ], default=st.session_state.answers.get("alergias_componentes", []))
        outros_componentes = st.text_input("Algum outro componente ao qual você é alérgico(a)?")

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
    st.subheader("5) Histórico e objetivo 🎯")
    col1, col2 = st.columns(2)
    with col1:
        usou_antes = st.radio("Já usou medicação para emagrecer?", options=["nao", "sim"], horizontal=True, index=0 if st.session_state.answers.get("usou_antes","nao")=="nao" else 1)
        quais = st.multiselect("Quais?", options=["Semaglutida","Tirzepatida","Liraglutida","Orlistate","Bupropiona/Naltrexona","Outros"], default=st.session_state.answers.get("quais", []))
        efeitos = st.text_area("Teve algum efeito colateral? Conte pra gente.")
    with col2:
        objetivo = st.selectbox("Qual seu objetivo principal?", options=["Perda de peso","Controle de comorbidades","Manutenção"], index=["Perda de peso","Controle de comorbidades","Manutenção"].index(st.session_state.answers.get("objetivo","Perda de peso")) if st.session_state.answers.get("objetivo") else 0)
        gestao_expectativas = st.slider("Quão pronto(a) está para mudanças no dia a dia (0-10)?", 0, 10, value=st.session_state.answers.get("pronto_mudar", 7))

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
        if st.button("Ver meu resultado ✅"):
            # garante idade calculada
            try:
                from datetime import date
                dob = date.fromisoformat(st.session_state.answers.get("data_nascimento"))
                st.session_state.answers["idade"] = (date.today().year - dob.year - ((date.today().month, date.today().day) < (dob.month, dob.day)))
                st.session_state.answers["idade_calculada"] = st.session_state.answers["idade"]
            except Exception:
                pass
            status, reasons = evaluate_rules(st.session_state.answers)
            st.session_state.eligibility = status
            st.session_state.exclusion_reasons = reasons
            next_step()

# ------------------------------
# Step 5 — Resultado + Consentimentos
# ------------------------------
elif st.session_state.step == 5:
    st.subheader("6) Seu resultado ✅")

    status = st.session_state.eligibility
    reasons = st.session_state.exclusion_reasons

    if status == "potencialmente_elegivel":
        st.success("🎉 **Parabéns!** Você pode se **beneficiar do tratamento farmacológico**. Vamos seguir para o agendamento da sua consulta.")
        if "imc" in st.session_state.answers:
            st.markdown(f"<div class='card'>IMC estimado: <span class='badge'><b>{st.session_state.answers['imc']}</b></span></div>", unsafe_allow_html=True)
        st.info("Na consulta on‑line, um médico vai revisar seus dados e, se tudo estiver adequado, definir a melhor estratégia de tratamento para o seu caso.")
        sched = os.environ.get("VIALEVE_SCHED_URL", "")
        if sched:
            st.link_button("Agendar minha consulta agora", sched, use_container_width=True)
        else:
            st.button("Agendar minha consulta (configure VIALEVE_SCHED_URL)", disabled=True, use_container_width=True)
    else:
        st.warning("ℹ️ **Obrigado por responder!** Neste momento, precisamos de uma **avaliação médica** antes de seguir com medicação para emagrecimento.")
        if reasons:
            with st.expander("Entenda o porquê", expanded=False):
                for r in reasons:
                    st.write(f"- {r}")
        st.info("Isso **não significa** que você não pode tratar. Nossa equipe pode orientar um plano seguro e personalizado para você.")

    st.divider()
    st.subheader("Consentimento e autorização")
    with st.expander("Leia o termo completo", expanded=False):
        st.markdown("""
**Termo de Consentimento Informado e Autorização de Teleconsulta (ViaLeve)**

1. **O que é isso?** Este formulário é uma **pré‑triagem** e **não** é consulta médica.
2. **Riscos e benefícios:** todo tratamento pode ter efeitos (náuseas, dor abdominal, cálculos na vesícula, pancreatite etc.). A indicação é **individual** e feita pelo médico.
3. **Alternativas:** mudanças de estilo de vida, plano nutricional, atividade física e, quando indicado, procedimentos cirúrgicos.
4. **Privacidade (LGPD):** autorizo o uso dos meus dados **somente** para este serviço, com segurança e possibilidade de revogar o consentimento.
5. **Teleconsulta:** autorizo a **consulta on‑line** (telemedicina) e sei que, se necessário, ela pode virar consulta presencial.
6. **Veracidade:** declaro que as informações aqui são verdadeiras.
7. **Assinatura eletrônica:** meu aceite eletrônico tem validade jurídica.
        """)

    c1, c2 = st.columns(2)
    with c1:
        aceite_termo = st.checkbox("Li e **aceito** o Termo de Consentimento.", value=st.session_state.answers.get("aceite_termo", False))
        autoriza_teleconsulta = st.checkbox("**Autorizo** a consulta on‑line (telemedicina).", value=st.session_state.answers.get("autoriza_teleconsulta", False))
    with c2:
        lgpd = st.checkbox("Autorizo o uso dos meus dados (LGPD).", value=st.session_state.answers.get("lgpd", False))
        veracidade = st.checkbox("Confirmo que as informações são verdadeiras.", value=st.session_state.answers.get("veracidade", False))

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
            "Baixar minhas respostas (JSON)",
            data=str(st.session_state.answers),
            file_name="vialeve_respostas.json",
            mime="application/json",
            disabled=not st.session_state.consent_ok
        )

st.markdown("---")
st.caption("ViaLeve • Protótipo v0.3 — uso interno • Streamlit (Python)")