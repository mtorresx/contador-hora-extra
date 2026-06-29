# Contador de Hora Extra

Um app simples e prático para registrar hora extra e atestados direto no Google Sheets.

## Por que criei isso?

Estava procurando uma solução rápida para conehcido controlar suas horas extras sem precisar ficar anotando em papel ou digitando tudo manualmente numa planilha. A ideia era algo bem intuitivo: abrir pelo celular, preencher início e fim, e pronto. Dados vão direto pro Sheets.

Virou também um projeto de estudo de integração com Google Sheets, Streamlit e deploy em produção.

## O que faz

- Registra hora extra com cálculo automático
- Registra atestado (expediente todo ou parcial)
- Impede duplicidade no mesmo dia
- Armazena tudo no Google Sheets
- Protegido por senha
- Mobile-first, responsivo no celular

## Como funciona

Digitação rápida: só preencher horário (4 números) e valor. O app calcula automaticamente quantas horas foram trabalhadas e quanto vai receber.

Todos os registros vão pro Google Sheets em tempo real. Fácil auditar, fácil organizar.

## Stack

- **Python** - Backend simples e rápido
- **Streamlit** - Interface web sem complicação
- **Google Sheets + gspread** - Banco de dados (yes, de verdade)
- **Google Service Account** - Autenticação segura
- **Streamlit Community Cloud** - Hospedagem gratuita

## Configuração local

1. Clone o repo:
```bash
git clone https://github.com/mtorresx/contador-hora-extra.git
cd contador-hora-extra
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o arquivo `.streamlit/secrets.toml` com suas credenciais do Google

4. Execute:
```bash
streamlit run app.py
```

## Configurar Google Sheets

1. Crie um projeto no Google Cloud Console
2. Ative Google Sheets API e Google Drive API
3. Crie uma Service Account
4. Gere uma chave JSON
5. Compartilhe uma planilha "Horas Extras" com o e-mail da Service Account
6. Coloque as credenciais no `secrets.toml`

## Deploy

Hospedado no Streamlit Community Cloud.

## Funcionalidades V1

- ✅ Registro de hora extra
- ✅ Registro de atestado
- ✅ Cálculo automático
- ✅ Proteção contra duplicidade
- ✅ Integração com Google Sheets
- ✅ Interface mobile

## Melhorias futuras

- Edição de registros pelo app
- Resumo mensal
- Exportação em PDF
- Suporte a múltiplos usuários

---

Trabalho em progresso. Feito com ☕ e curiosidade.