# ViaLeve — Protótipo de Pré-elegibilidade (v0.1)

Protótipo rápido em **Streamlit** para triagem inicial de pacientes candidatos a tratamento farmacológico para emagrecimento (GLP‑1 e afins).

## Como rodar

1. Crie e ative um virtualenv (opcional).
2. Instale dependências:
   ```bash
   pip install -r requirements.txt
   ```
3. Rode o app:
   ```bash
   streamlit run app.py
   ```

## Notas de Produto

- Fluxo em 5 passos: Identificação → Medidas/Comorbidades → Contraindicações → Histórico/Objetivos → Resultado.
- **Regras de exclusão** no arquivo `app.py` dentro de `evaluate_rules(...)`:
  - Menor de 18 anos;
  - Gestação ou amamentação;
  - Tratamento oncológico ativo;
  - Pancreatite prévia;
  - História pessoal/familiar de **MTC** (carcinoma medular de tireoide) ou **MEN2**;
  - Alergia/hipersensibilidade a GLP‑1;
  - Doença gastrointestinal grave ativa;
  - IMC < 27 **sem** comorbidades relevantes.

> Este conjunto é **ilustrativo** e deve ser validado e ampliado pelo time clínico e jurídico.

## Próximos passos sugeridos

- Persistência segura (PostgreSQL) e autenticação (e‑mail/SMS).
- Painel admin para revisão médica e emissão de receita.
- Logs de consentimento e trilhas de auditoria.
- Internacionalização e acessibilidade (WCAG).
- Portar UI para web/mobile com **React Native** ou **Flutter**, mantendo a API em Python (FastAPI).