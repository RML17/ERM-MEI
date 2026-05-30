# Sistema de Gestão Empresarial Integrado

Sistema web completo desenvolvido em **Flask (Python)** para gestão de pequenas e médias empresas. Oferece módulos integrados de finanças, estoque, recursos humanos, logística, fiscal e conversão de moedas.

---

## Funcionalidades

| Módulo | Descrição |
|---|---|
| **Notas Fiscais** | Emissão, importação de XML, cálculo automático de impostos |
| **Estoque** | Controle de produtos, movimentações FIFO, alertas de estoque mínimo |
| **Pagamentos** | Contas a pagar/receber, múltiplos métodos, controle de vencimentos |
| **Recursos Humanos** | Funcionários, folha de pagamento, ponto, férias e licenças |
| **Logística** | Transportadoras, envios, rotas, veículos e motoristas |
| **Fiscal** | Cálculo de ICMS, IPI, PIS, COFINS, ISS por estado |
| **Câmbio** | Cotações em tempo real com suporte a 15+ moedas |
| **Relatórios** | Dashboards financeiros, exportação para Excel/Word |
| **Auditoria** | Log completo de todas as operações do sistema |

---

## Tecnologias

- **Backend:** Python 3 + Flask + SQLAlchemy
- **Banco de dados:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **Frontend:** Bootstrap 5, jQuery, Chart.js, DataTables
- **Autenticação:** Flask-Login com controle de roles
- **Formulários:** WTForms com proteção CSRF

---

## Pré-requisitos

- Python 3.10+
- pip

---

## Instalação

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd sistema-gestao

# Instale as dependências
pip install -r requirements.txt

# Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas configurações
```

---

## Variáveis de Ambiente

| Variável | Descrição | Exemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexão com o banco | `sqlite:///gestao.db` |
| `SESSION_SECRET` | Chave secreta para sessões | `sua-chave-secreta` |

---

## Executando o projeto

```bash
python main.py
```

Acesse em: [http://localhost:5000](http://localhost:5000)

**Credenciais padrão:**
- Usuário: `admin`
- Senha: `admin123`

> Recomendamos alterar a senha no primeiro acesso em **Meu Perfil**.

---

## Estrutura do Projeto

```
├── app.py              # Configuração principal do Flask
├── main.py             # Ponto de entrada
├── models.py           # Modelos do banco de dados
├── forms.py            # Formulários WTForms
├── config.py           # Configurações por ambiente
├── routes/             # Blueprints de cada módulo
│   ├── auth.py         # Autenticação e perfil
│   ├── dashboard.py    # Painel principal
│   ├── invoices.py     # Notas fiscais
│   ├── inventory.py    # Estoque
│   ├── payments.py     # Pagamentos
│   ├── hr.py           # Recursos humanos
│   ├── logistics.py    # Logística
│   ├── taxes.py        # Serviços fiscais
│   ├── currency.py     # Conversão de moedas
│   └── reports.py      # Relatórios
└── templates/          # Templates Jinja2
```

---

## Perfis de Usuário

| Role | Acesso |
|---|---|
| **Administrador** | Acesso total ao sistema |
| **Gerente** | Gestão operacional e relatórios |
| **Contador** | Módulos financeiros e fiscais |
| **Estoquista** | Controle de inventário |
| **Vendas** | Emissão de notas e pagamentos |

---

## Deploy em Produção

1. Configure `DATABASE_URL` para um banco PostgreSQL
2. Defina `SESSION_SECRET` com uma chave forte e aleatória
3. Execute com Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

---

## Licença

Este projeto é de uso interno. Todos os direitos reservados.
