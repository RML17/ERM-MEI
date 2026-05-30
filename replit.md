# Sistema de Gestão Empresarial Integrado

## Overview

Este é um sistema completo de gestão empresarial desenvolvido em Flask, projetado para pequenas e médias empresas que precisam de uma solução integrada para gerenciamento financeiro, estoque, recursos humanos, logística e operações comerciais. O sistema oferece funcionalidades abrangentes incluindo emissão de notas fiscais, controle de estoque, gestão de pagamentos, recursos humanos, logística e conversão de moedas.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python) com arquitetura modular baseada em Blueprints
- **ORM**: SQLAlchemy com DeclarativeBase para mapeamento objeto-relacional
- **Autenticação**: Flask-Login para gerenciamento de sessões e controle de acesso
- **Formulários**: WTForms para validação e renderização de formulários
- **Estrutura**: Separação clara entre modelos, serviços, rotas e templates

### Frontend Architecture
- **Template Engine**: Jinja2 para renderização server-side
- **CSS Framework**: Bootstrap 5 com tema escuro personalizado
- **JavaScript**: jQuery, DataTables para tabelas interativas, Chart.js para gráficos
- **Design Pattern**: Responsive design com suporte a dispositivos móveis

### Data Storage Solutions
- **Banco Principal**: SQLite para desenvolvimento, PostgreSQL para produção
- **Migrations**: SQLAlchemy migrations para controle de versão do esquema
- **Connection Pool**: Pool de conexões configurado com recycle e ping automático

### Authentication and Authorization
- **Sistema de Usuários**: Baseado em roles (Admin, Manager, Accountant, Inventory, Sales)
- **Password Security**: Werkzeug para hash seguro de senhas
- **Session Management**: Flask-Login com controle de sessões persistentes
- **Audit Trail**: Sistema completo de logs de auditoria para todas as operações

## Key Components

### 1. Invoice Management (Gestão de Notas Fiscais)
- **Funcionalidades**: Criação, edição, visualização e cancelamento de notas fiscais
- **Tipos Suportados**: Notas de entrada (compras) e saída (vendas)
- **Importação XML**: Processamento automático de arquivos XML da SEFAZ
- **Cálculo de Impostos**: Sistema automatizado para ICMS, IPI, PIS, COFINS, ISS
- **Status Workflow**: Rascunho → Pendente → Emitida → Aprovada/Cancelada

### 2. Inventory Management (Controle de Estoque)
- **Produtos**: Cadastro completo com SKU, preços, estoque mínimo
- **Movimentações**: Controle FIFO para entradas e saídas
- **Integração**: Automática com notas fiscais para atualização de estoque
- **Relatórios**: Posição de estoque, movimentações e produtos em falta

### 3. Payment Management (Gestão de Pagamentos)
- **Múltiplos Métodos**: Boleto, PIX, transferência, cartão, dinheiro, cheque
- **Status Tracking**: Pendente, pago, parcial, em atraso, cancelado
- **Vencimentos**: Controle automático de datas de vencimento
- **Integração**: Vinculação automática com notas fiscais

### 4. Human Resources (Recursos Humanos)
- **Funcionários**: Cadastro completo com dados pessoais e profissionais
- **Departamentos**: Organização hierárquica da empresa
- **Folha de Pagamento**: Cálculo automático de INSS, IRRF, FGTS
- **Ponto**: Sistema de controle de frequência
- **Férias e Licenças**: Gestão de solicitações e aprovações

### 5. Logistics (Logística)
- **Transportadoras**: Cadastro e gestão de parceiros logísticos
- **Envios**: Criação e rastreamento de remessas
- **Rotas**: Definição de percursos e custos
- **Veículos e Motoristas**: Controle da frota própria

### 6. Currency Conversion (Conversão de Moedas)
- **Cotações em Tempo Real**: Integração com APIs de câmbio
- **15+ Moedas**: Suporte a principais moedas mundiais
- **Histórico**: Armazenamento de cotações para relatórios

### 7. Tax Services (Serviços Fiscais)
- **Cálculos Automatizados**: Todos os impostos brasileiros por estado
- **ICMS Interestadual**: Diferenciação por região de origem/destino
- **Simulações**: Ferramenta para calcular impostos antes da emissão
- **Compliance**: Alinhado com a legislação tributária brasileira

## Data Flow

### Invoice Processing Flow
1. **Criação**: Usuário cria nota fiscal manual ou importa XML
2. **Validação**: Sistema valida dados e calcula impostos automaticamente
3. **Aprovação**: Workflow de aprovação baseado em roles
4. **Estoque**: Atualização automática do inventário
5. **Financeiro**: Geração automática de contas a pagar/receber

### Inventory Flow
1. **Movimentação**: Registro de entradas/saídas com método FIFO
2. **Validação**: Verificação de estoque disponível para saídas
3. **Custos**: Cálculo automático de custo médio ponderado
4. **Alertas**: Notificações para produtos com estoque baixo

### Payment Flow
1. **Geração**: Criação automática a partir de notas fiscais
2. **Vencimento**: Sistema de alertas para datas próximas
3. **Recebimento**: Registro de pagamentos com conciliação
4. **Relatórios**: Dashboards financeiros em tempo real

## External Dependencies

### Core Dependencies
- **Flask**: Framework web principal
- **SQLAlchemy**: ORM para banco de dados
- **WTForms**: Validação e renderização de formulários
- **Flask-Login**: Autenticação e sessões
- **Werkzeug**: Utilitários de segurança

### Data Processing
- **lxml**: Processamento de arquivos XML
- **openpyxl**: Geração de relatórios Excel
- **python-docx**: Relatórios em Word
- **pandas**: Análise de dados

### Frontend Libraries
- **Bootstrap 5**: Framework CSS
- **Font Awesome**: Ícones
- **DataTables**: Tabelas interativas
- **Chart.js**: Gráficos e dashboards

### External APIs
- **Exchange Rate APIs**: Para cotações de moedas
- **SEFAZ Web Services**: Para validação fiscal (futuro)

## Deployment Strategy

### Development Environment
- **Database**: SQLite para simplicidade
- **Debug Mode**: Ativado para desenvolvimento
- **Hot Reload**: Automático para mudanças de código

### Production Environment
- **Database**: PostgreSQL com SSL
- **WSGI Server**: Gunicorn recomendado
- **Reverse Proxy**: Nginx para arquivos estáticos
- **SSL/TLS**: Certificados obrigatórios
- **Environment Variables**: Para configurações sensíveis

### Database Migration
- **URI Handling**: Conversão automática postgres:// para postgresql://
- **Connection Pool**: Configurado para alta disponibilidade
- **Backup Strategy**: Backups automáticos recomendados

### Security Considerations
- **Session Management**: Chaves secretas em environment variables
- **Password Hashing**: Werkzeug com salt
- **CSRF Protection**: WTForms CSRF tokens
- **SQL Injection**: Proteção via SQLAlchemy ORM

## Changelog
- June 29, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.