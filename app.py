import os
import streamlit as st
from typing import Dict, Any, List
from datetime import date

st.set_page_config(page_title="ViaLeve - Pré-elegibilidade", page_icon="💊", layout="centered")

LOGO_SVG = """
<svg width="720" height="180" viewBox="0 0 720 180" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="g1" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0EA5A4" />
      <stop offset="100%" stop-color="#94E7E3" />
    </linearGradient>
  </defs>
  <g transform="translate(10,20)">
    <circle cx="70" cy="70" r="62" fill="url(#g1)"/>
    <path d="M45 70 C60 45, 80 40, 100 55 C95 60, 85 68, 75 78 C68 84, 60 90, 55 94 C58 84, 58 78, 60 70 Z" fill="#ffffff" opacity="0.95"/>
    <path d="M55 90 L70 105 L105 70" fill="none" stroke="#ffffff" stroke-width="10" stroke-linecap="round" stroke-linejoin="round" opacity="0.95"/>
  </g>
  <g transform="translate(160,40)">
    <text x="0" y="55" font-size="64" font-family="Inter, Arial, Helvetica, sans-serif" font-weight="700" fill="#0F172A">Via</text>
    <text x="155" y="55" font-size="64" font-family="Inter, Arial, Helvetica, sans-serif" font-weight="600" fill="#0EA5A4">Leve</text>
    <text x="0" y="105" font-size="20" font-family="Inter, Arial, Helvetica, sans-serif" fill="#475569">sua jornada mais leve começa aqui</text>
  </g>
</svg>
"""

st.markdown(
    """
    <style>
      :root { --brand: #0EA5A4; --brandSoft: #94E7E3; --ink: #0F172A; }
      .logo-wrap { display:flex; align-items:center; gap:14px; margin: 0 0 12px 0; }
      .logo-wrap svg { max-width: 100%; height: auto; }
      .crumbs { display:flex; gap:8px; flex-wrap:wrap; margin: 6px 0 16px 0;}
      .crumb { padding:6px 10px; border-radius:999px; border:1px solid #e2e8f0; background:#fff; color:#0f172a; font-size:0.85rem;}
      .crumb.active { background: var(--brandSoft); border-color: #c7f3ef; }
      .float-wa { position: fixed; right: 18px; bottom: 18px; z-index: 9999; }
      .float-wa a { display:inline-block; padding:12px 16px; border-radius:999px; background:#25D366; color:#fff; text-decoration:none; font-weight:600; box-shadow:0 6px 20px rgba(0,0,0,.15); }
    </style>
    """,
    unsafe_allow_html=True,
)

def init_state():
    defaults = {"step":0, "answers":{}, "eligibility":None, "exclusion_reasons":[], "consent_ok":False}
    for k,v in defaults.items():
        if k not in st.session_state: st.session_state[k]=v

def go_to(step:int):
    st.session_state.step = max(0, min(5, step))
    st.experimental_rerun()

def next_step(): go_to(st.session_state.step+1)
def prev_step(): go_to(st.session_state.step-1)

def reset_flow():
    for k in list(st.session_state.keys()): del st.session_state[k]
    init_state(); st.experimental_rerun()

def calc_idade(d):
    if not d: return None
    today = date.today()
    return today.year - d.year - ((today.month, today.day) < (d.month, d.day))

EXCIPIENTES_COMUNS = [
    "Polietilenoglicol (PEG)","Metacresol / Fenol","Fosfatos (fosfato dissódico etc.)",
    "Látex (agulhas/rolhas)","Carboximetilcelulose","Trometamina (TRIS)",
]

def evaluate_rules(a:Dict[str,Any]):
    exclusion=[]; g=lambda k,d=None:a.get(k,d)
    if g("data_nascimento"):
        try:
            dob = g("data_nascimento"); 
            from datetime import date as _d
            if isinstance(dob, str): dob = _d.fromisoformat(dob)
            idade = calc_idade(dob)
            if idade is not None: a["idade"]=idade; a["idade_calculada"]=idade
        except: pass
    if g("idade") is not None and g("idade")<18: exclusion.append("Menor de 18 anos.")
    if g("gravidez")=="sim": exclusion.append("Gestação em curso.")
    if g("amamentando")=="sim": exclusion.append("Amamentação em curso.")
    if g("tratamento_cancer")=="sim": exclusion.append("Tratamento oncológico ativo.")
    if g("pancreatite_previa")=="sim": exclusion.append("História de pancreatite prévia.")
    if g("historico_mtc_men2")=="sim": exclusion.append("História pessoal/familiar de carcinoma medular de tireoide (MTC) ou MEN2.")
    if g("alergia_glp1")=="sim": exclusion.append("Hipersensibilidade conhecida a análogos de GLP-1.")
    if g("alergias_componentes"):
        if g("alergias_componentes")!=["Não tenho alergia a esses componentes"]:
            exclusion.append("Alergia relatada a excipientes comuns de formulações injetáveis (ver detalhes).")
    if g("gi_grave")=="sim": exclusion.append("Doença gastrointestinal grave ativa.")
    if g("gastroparesia")=="sim": exclusion.append("Gastroparesia diagnosticada.")
    if g("colecistite_12m")=="sim": exclusion.append("Colecistite/colelitíase sintomática nos últimos 12 meses.")
    if g("insuf_renal") in ["moderada","grave"]: exclusion.append("Insuficiência renal moderada/grave (necessita avaliação).")
    if g("insuf_hepatica") in ["moderada","grave"]: exclusion.append("Insuficiência hepática moderada/grave (necessita avaliação).")
    if g("transtorno_alimentar")=="sim": exclusion.append("Transtorno alimentar ativo.")
    if g("uso_corticoide")=="sim": exclusion.append("Uso crônico de corticoide (requer avaliação).")
    if g("antipsicoticos")=="sim": exclusion.append("Uso de antipsicóticos (requer avaliação).")
    imc=None; peso=g("peso"); altura=g("altura")
    if peso and altura:
        try: imc=float(peso)/(float(altura)**2)
        except: pass
    if imc is not None and imc<27 and g("tem_comorbidades")=="nao":
        exclusion.append("IMC < 27 sem comorbidades relevantes.")
    return ("excluido" if exclusion else "potencialmente_elegivel"), exclusion

STEP_NAMES=["Sobre você","Sua saúde","Condições importantes","Medicações & alergias","Histórico & objetivo","Revisar & confirmar"]
def crumbs():
    st.markdown("<div class='crumbs'>" + "".join([f"<span class='crumb {'active' if i==st.session_state.step else ''}'>{i+1}. {n}</span>" for i,n in enumerate(STEP_NAMES)]) + "</div>", unsafe_allow_html=True)

def safe_multi(options, current):
    NONE="Não tenho alergia a esses componentes"
    s=list(current or [])
    if NONE in s and len(s)>1: s=[x for x in s if x!=NONE]
    return [x for x in s if x in options]

# App
init_state()
st.markdown(f"<div class='logo-wrap'>{LOGO_SVG}</div>", unsafe_allow_html=True)
if st.session_state.step==0 and not st.session_state.answers.get("_abertura_lida"):
    st.info("Olá! Vamos fazer algumas perguntas rápidas para entender seu perfil e indicar a melhor forma de cuidar da sua saúde. É rápido e seguro — seus dados ficam protegidos.")
    st.session_state.answers["_abertura_lida"]=True

crumbs()

from datetime import date as _date

if st.session_state.step==0:
    st.subheader("Sobre você")
    with st.form("step0"):
        col1, col2 = st.columns(2)
        with col1:
            nome = st.text_input("Nome completo *", value=st.session_state.answers.get("nome",""))
            email = st.text_input("E-mail *", value=st.session_state.answers.get("email",""))
        with col2:
            today=_date.today()
            default_iso = st.session_state.answers.get("data_nascimento")
            if isinstance(default_iso,str) and default_iso:
                try:
                    d=_date.fromisoformat(default_iso); d_d,d_m,d_a=d.day,d.month,d.year
                except: d_d,d_m,d_a=1,1,1990
            else: d_d,d_m,d_a=1,1,1990
            c1,c2,c3=st.columns([1,1,2])
            dia=c1.selectbox("Dia", list(range(1,32)), index=d_d-1)
            mes=c2.selectbox("Mês", list(range(1,13)), index=d_m-1)
            anos=list(range(1900, today.year+1))
            idx=anos.index(d_a) if d_a in anos else len(anos)//2
            ano=c3.selectbox("Ano", anos, index=idx)
            identidade=st.selectbox("Como você se identifica? (opcional)", ["Feminino","Masculino","Prefiro não informar"], index=(["Feminino","Masculino","Prefiro não informar"].index(st.session_state.answers.get("identidade","Feminino")) if st.session_state.answers.get("identidade") else 0))

        erro=None
        try:
            dob=_date(ano,mes,dia)
            if dob>_date.today(): erro="Data de nascimento no futuro não é válida."
        except: erro="Data inválida. Verifique dia/mês/ano."
        st.session_state.answers.update({"nome":nome,"email":email,"identidade":identidade,"data_nascimento":str(dob) if not erro else ""})
        if st.form_submit_button("Continuar ▶️", use_container_width=True):
            if not nome.strip(): st.error("Por favor, preencha o nome completo.")
            elif not email.strip(): st.error("Por favor, preencha o e-mail.")
            elif erro: st.error(erro)
            else: next_step()

elif st.session_state.step==1:
    st.subheader("Sua saúde")
    with st.form("step1"):
        col1,col2=st.columns(2)
        with col1:
            peso=st.number_input("Peso (kg) *", min_value=30, max_value=400, step=1, value=int(st.session_state.answers.get("peso",90)), format="%d")
            tem=st.selectbox("Você tem alguma dessas condições de saúde? (ex.: diabetes tipo 2, pressão alta, apneia do sono, colesterol alto)", ["Sim","Não"], index=0 if st.session_state.answers.get("tem_comorbidades","Sim")=="Sim" else 1)
        with col2:
            altura=st.number_input("Altura (m) *", min_value=1.30, max_value=2.20, step=0.01, value=float(st.session_state.answers.get("altura",1.70)))
            comorbidades=st.text_area("Se sim, quais?", value=st.session_state.answers.get("comorbidades",""))
        st.session_state.answers.update({"peso":peso,"altura":altura,"tem_comorbidades":"sim" if tem=="Sim" else "nao","comorbidades":comorbidades})
        if st.form_submit_button("Continuar ▶️", use_container_width=True): next_step()

elif st.session_state.step==2:
    st.subheader("Condições importantes")
    with st.form("step2"):
        col1,col2=st.columns(2)
        with col1:
            gravidez=st.selectbox("Está grávida?", ["Não","Sim"], index=0 if st.session_state.answers.get("gravidez","nao")=="nao" else 1)
            amamentando=st.selectbox("Está amamentando?", ["Não","Sim"], index=0 if st.session_state.answers.get("amamentando","nao")=="nao" else 1)
            tratamento=st.selectbox("Está em tratamento contra câncer neste momento?", ["Não","Sim"], index=0 if st.session_state.answers.get("tratamento_cancer","nao")=="nao" else 1)
            gi=st.selectbox("Tem alguma doença grave no estômago ou intestino em atividade?", ["Não","Sim"], index=0 if st.session_state.answers.get("gi_grave","nao")=="nao" else 1)
            gastro=st.selectbox("Já recebeu diagnóstico de gastroparesia (esvaziamento gástrico lento)?", ["Não","Sim"], index=0 if st.session_state.answers.get("gastroparesia","nao")=="nao" else 1)
        with col2:
            pancrea=st.selectbox("Já teve pancreatite?", ["Não","Sim"], index=0 if st.session_state.answers.get("pancreatite_previa","nao")=="nao" else 1)
            mtc=st.selectbox("Algum caso seu ou na família de câncer de tireoide ou síndrome genética rara (MTC ou MEN2)?", ["Não","Sim"], index=0 if st.session_state.answers.get("historico_mtc_men2","nao")=="nao" else 1)
            cole=st.selectbox("Teve crise de vesícula ou colecistite nos últimos 12 meses?", ["Não","Sim"], index=0 if st.session_state.answers.get("colecistite_12m","nao")=="nao" else 1)
            outras=st.text_area("Outras condições relevantes?")
        st.session_state.answers.update({
            "gravidez":"sim" if gravidez=="Sim" else "nao",
            "amamentando":"sim" if amamentando=="Sim" else "nao",
            "tratamento_cancer":"sim" if tratamento=="Sim" else "nao",
            "gi_grave":"sim" if gi=="Sim" else "nao",
            "gastroparesia":"sim" if gastro=="Sim" else "nao",
            "pancreatite_previa":"sim" if pancrea=="Sim" else "nao",
            "historico_mtc_men2":"sim" if mtc=="Sim" else "nao",
            "colecistite_12m":"sim" if cole=="Sim" else "nao",
            "outras_contra":outras,
        })
        if st.form_submit_button("Continuar ▶️", use_container_width=True): next_step()

elif st.session_state.step==3:
    st.subheader("Medicações & alergias")
    with st.form("step3"):
        col1,col2=st.columns(2)
        with col1:
            rins=st.selectbox("Saúde dos rins", ["Normal","Leve alteração","Alteração moderada","Alteração grave","Não sei informar"], index=["Normal","Leve alteração","Alteração moderada","Alteração grave","Não sei informar"].index(st.session_state.answers.get("insuf_renal","Normal")) if st.session_state.answers.get("insuf_renal") else 0)
            figado=st.selectbox("Saúde do fígado", ["Normal","Leve alteração","Alteração moderada","Alteração grave","Não sei informar"], index=["Normal","Leve alteração","Alteração moderada","Alteração grave","Não sei informar"].index(st.session_state.answers.get("insuf_hepatica","Normal")) if st.session_state.answers.get("insuf_hepatica") else 0)
            ta=st.selectbox("Tem transtorno alimentar ativo? (anorexia, bulimia, compulsão alimentar)", ["Não","Sim"], index=0 if st.session_state.answers.get("transtorno_alimentar","nao")=="nao" else 1)
            cort=st.selectbox("Usa corticoide todos os dias há mais de 3 meses?", ["Não","Sim"], index=0 if st.session_state.answers.get("uso_corticoide","nao")=="nao" else 1)
            anti=st.selectbox("Usa medicamentos antipsicóticos atualmente?", ["Não","Sim"], index=0 if st.session_state.answers.get("antipsicoticos","nao")=="nao" else 1)
        with col2:
            options = EXCIPIENTES_COMUNS + ["Não tenho alergia a esses componentes"]
            alergias=st.multiselect("Alergia a algum destes componentes? (pode marcar mais de um)", options=options, default=st.session_state.answers.get("alergias_componentes", []))
            # mutual exclusion
            NONE="Não tenho alergia a esses componentes"
            if NONE in alergias and len(alergias)>1: alergias=[NONE]
            outros=st.text_input("Alguma outra alergia importante?", value=st.session_state.answers.get("outros_componentes",""))
            glp1=st.selectbox("Alergia conhecida a medicamentos do tipo GLP-1?", ["Não","Sim"], index=0 if st.session_state.answers.get("alergia_glp1","nao")=="nao" else 1)
        def norm(x):
            m={"Normal":"normal","Leve alteração":"leve","Alteração moderada":"moderada","Alteração grave":"grave","Não sei informar":"desconhecido"}; return m.get(x,"normal")
        st.session_state.answers.update({
            "insuf_renal":norm(rins),"insuf_hepatica":norm(figado),
            "transtorno_alimentar":"sim" if ta=="Sim" else "nao",
            "uso_corticoide":"sim" if cort=="Sim" else "nao",
            "antipsicoticos":"sim" if anti=="Sim" else "nao",
            "alergias_componentes":alergias,"outros_componentes":outros,
            "alergia_glp1":"sim" if glp1=="Sim" else "nao",
        })
        if st.form_submit_button("Continuar ▶️", use_container_width=True): next_step()

elif st.session_state.step==4:
    st.subheader("Histórico & objetivo")
    with st.form("step4"):
        col1,col2=st.columns(2)
        with col1:
            usou=st.selectbox("Já usou medicação para emagrecer?", ["Não","Sim"], index=0 if st.session_state.answers.get("usou_antes","nao")=="nao" else 1)
            quais=st.multiselect("Quais? (pode deixar em branco se não lembrar)", options=["Semaglutida","Tirzepatida","Liraglutida","Orlistate","Bupropiona/Naltrexona","Outros"], default=st.session_state.answers.get("quais", []))
            efeitos=st.text_area("Teve algum efeito colateral? (opcional)", value=st.session_state.answers.get("efeitos",""))
        with col2:
            obj=st.selectbox("Qual seu objetivo principal?", ["Perda de peso","Controle de comorbidades","Manutenção do peso"], index=["Perda de peso","Controle de comorbidades","Manutenção do peso"].index(st.session_state.answers.get("objetivo","Perda de peso")) if st.session_state.answers.get("objetivo") else 0)
            pronto=st.slider("Numa escala de 0 a 10, o quanto você está pronto(a) para transformar seus hábitos e conquistar seus objetivos?", 0, 10, value=st.session_state.answers.get("pronto_mudar", 7))
        st.session_state.answers.update({"usou_antes":"sim" if usou=="Sim" else "nao","quais":quais,"efeitos":efeitos,"objetivo":obj,"pronto_mudar":pronto})
        if st.form_submit_button("Revisar & confirmar ✅", use_container_width=True): next_step()

elif st.session_state.step==5:
    st.subheader("Revisar & confirmar")
    a=st.session_state.answers
    with st.expander("Clique para revisar suas respostas", expanded=True):
        st.write("**Sobre você**")
        st.write(f"- Nome: {a.get('nome','')}")
        st.write(f"- E-mail: {a.get('email','')}")
        st.write(f"- Data de nascimento: {a.get('data_nascimento','')}")
        st.write(f"- Identidade: {a.get('identidade','')}")
        st.write("**Sua saúde**")
        st.write(f"- Peso (kg): {a.get('peso','')}")
        st.write(f"- Altura (m): {a.get('altura','')}")
        st.write(f"- Comorbidades relevantes: {'Sim' if a.get('tem_comorbidades')=='sim' else 'Não'}")
        if a.get('comorbidades'): st.write(f"  - Quais: {a.get('comorbidades')}")
        st.write("**Condições importantes**")
        def y(v): return 'Sim' if v=='sim' else 'Não'
        st.write(f"- Grávida: {y(a.get('gravidez','nao'))}")
        st.write(f"- Amamentando: {y(a.get('amamentando','nao'))}")
        st.write(f"- Tratamento oncológico: {y(a.get('tratamento_cancer','nao'))}")
        st.write(f"- Doença GI grave ativa: {y(a.get('gi_grave','nao'))}")
        st.write(f"- Gastroparesia: {y(a.get('gastroparesia','nao'))}")
        st.write(f"- Pancreatite prévia: {y(a.get('pancreatite_previa','nao'))}")
        st.write(f"- MTC/MEN2 (pessoal/família): {y(a.get('historico_mtc_men2','nao'))}")
        st.write(f"- Colecistite/cólica vesicular 12m: {y(a.get('colecistite_12m','nao'))}")
        if a.get("outras_contra"): st.write(f"  - Outras: {a.get('outras_contra')}")
        st.write("**Medicações & alergias**")
        st.write(f"- Rins: {a.get('insuf_renal','')}")
        st.write(f"- Fígado: {a.get('insuf_hepatica','')}")
        st.write(f"- Transtorno alimentar ativo: {y(a.get('transtorno_alimentar','nao'))}")
        st.write(f"- Corticoide crônico: {y(a.get('uso_corticoide','nao'))}")
        st.write(f"- Antipsicóticos: {y(a.get('antipsicoticos','nao'))}")
        st.write(f"- Alergia GLP-1: {y(a.get('alergia_glp1','nao'))}")
        st.write(f"- Alergia a componentes: {', '.join(a.get('alergias_componentes', [])) or '—'}")
        if a.get("outros_componentes"): st.write(f"  - Outras alergias: {a.get('outros_componentes')}")
        st.write("**Histórico & objetivo**")
        st.write(f"- Uso prévio de medicação: {y(a.get('usou_antes','nao'))}")
        st.write(f"- Quais: {', '.join(a.get('quais', [])) or '—'}")
        if a.get("efeitos"): st.write(f"- Efeitos colaterais: {a.get('efeitos')}")
        st.write(f"- Objetivo: {a.get('objetivo','')}")
        st.write(f"- Pronto(a) para mudanças (0–10): {a.get('pronto_mudar', '')}")
    with st.form("final"):
        col1,col2,col3=st.columns(3)
        with col1: b_voltar=st.form_submit_button("⬅️ Voltar", use_container_width=True)
        with col2: b_reiniciar=st.form_submit_button("Reiniciar 🔄", use_container_width=True)
        with col3: b_confirmar=st.form_submit_button("Confirmar e ver resultado 🚀", use_container_width=True)
        if b_voltar: prev_step()
        if b_reiniciar: reset_flow()
        if b_confirmar:
            status, reasons = evaluate_rules(st.session_state.answers)
            st.session_state.eligibility,status; st.session_state.exclusion_reasons=reasons
            if status=="potencialmente_elegivel":
                st.success("🎉 Parabéns! Você pode se **beneficiar do tratamento farmacológico**. Vamos seguir para o agendamento da sua consulta ainda hoje.")
            else:
                st.warning("Obrigado por responder! Antes de definir a medicação, vamos conversar para criar um plano **seguro e personalizado** para você.")
                if reasons:
                    with st.expander("Entenda o porquê", expanded=False):
                        for r in reasons: st.write(f"- {r}")
            st.divider(); st.subheader("Consentimentos")
            with st.expander("Leia o termo completo", expanded=False):
                st.markdown("""
**Termo de Consentimento Informado e Autorização de Teleconsulta (ViaLeve)**

1. **O que é isso?** Este formulário é uma **pré-triagem** e **não** é consulta médica.
2. **Riscos e benefícios:** todo tratamento pode ter efeitos (náuseas, dor abdominal, cálculos na vesícula, pancreatite etc.). A indicação é **individual** e feita pelo médico.
3. **Alternativas:** mudanças de estilo de vida, plano nutricional, atividade física e, quando indicado, procedimentos cirúrgicos.
4. **Privacidade (LGPD):** autorizo o uso dos meus dados **somente** para este serviço, com segurança e possibilidade de revogar o consentimento.
5. **Teleconsulta:** autorizo a **consulta on-line** (telemedicina) e sei que, se necessário, ela pode virar consulta presencial.
6. **Veracidade:** declaro que as informações são verdadeiras.
7. **Assinatura eletrônica:** meu aceite eletrônico tem validade jurídica.
                """)
            with st.form("consent"):
                c1,c2=st.columns(2)
                with c1:
                    aceite=st.checkbox("Li e aceito o Termo de Consentimento.", value=st.session_state.answers.get("aceite_termo", False))
                    tele=st.checkbox("Autorizo a consulta on-line (telemedicina).", value=st.session_state.answers.get("autoriza_teleconsulta", False))
                with c2:
                    lgpd=st.checkbox("Autorizo o uso dos meus dados (LGPD).", value=st.session_state.answers.get("lgpd", False))
                    ver=st.checkbox("Confirmo que as informações são verdadeiras.", value=st.session_state.answers.get("veracidade", False))
                st.session_state.answers.update({"aceite_termo":aceite,"autoriza_teleconsulta":tele,"lgpd":lgpd,"veracidade":ver})
                st.session_state.consent_ok = all([aceite,tele,lgpd,ver])
                colx1,colx2=st.columns(2)
                with colx1:
                    sched=os.environ.get("VIALEVE_SCHED_URL","")
                    if sched: st.link_button("Agendar minha consulta agora", sched, use_container_width=True, type="primary")
                    else: st.button("Agendar minha consulta (configure VIALEVE_SCHED_URL)", disabled=True, use_container_width=True)
                with colx2:
                    st.download_button("Baixar minhas respostas (JSON)", data=str(st.session_state.answers), file_name="vialeve_respostas.json", mime="application/json", disabled=not st.session_state.consent_ok, use_container_width=True)

wa=os.environ.get("VIALEVE_WHATSAPP_URL","")
if wa:
    st.markdown(f"<div class='float-wa'><a href='{wa}' target='_blank'>Dúvidas? Fale no WhatsApp</a></div>", unsafe_allow_html=True)

st.markdown("---"); st.caption("ViaLeve • Protótipo v0.9 — PT-BR • Streamlit (Python)")