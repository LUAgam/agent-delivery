# Reporter Platform — Data Sources

Source of truth para campos disponíveis em templates `.tpl`. Sempre consultar este arquivo antes de iniciar qualquer mapeamento de campos.

> **MANDATORY:** Load this file at the start of Gate 1 before any field mapping begins.

---

## Hierarquia de busca recomendada

| Tipo de dado | Fonte primária | Fallback |
|-------------|---------------|----------|
| Dados pessoais / bancários do titular | **CRM** (`crm.holder.*`, `crm.alias.*`) | Midaz metadata |
| Dados contábeis / saldo / movimentações | **midaz_transaction** | — |
| Dados organizacionais / cadastrais | **midaz_onboarding** | — |
| Informações regulatórias específicas | **metadata fields** (ambos) | — |

---

## Data Sources disponíveis

### `midaz_onboarding`
Dados cadastrais do Midaz (organizations e accounts).

| Campo | Tipo | Exemplo | Descrição |
|-------|------|---------|-----------|
| `midaz_onboarding.organization.0.legal_document` | string | `"12345678000190"` | CNPJ completo (14 dígitos) |
| `midaz_onboarding.organization.0.legal_name` | string | `"Empresa S.A."` | Razão social |
| `midaz_onboarding.organization.0.trade_name` | string | `"Empresa"` | Nome fantasia |
| `midaz_onboarding.organization.0.status` | string | `"active"` | Status da organização |
| `midaz_onboarding.organization.0.metadata.*` | any | — | Campos customizados (ex: `metadata.giin`, `metadata.categoria_declarante`) |
| `midaz_onboarding.account.id` | uuid | `"acc_01abc..."` | ID da conta |
| `midaz_onboarding.account.name` | string | `"Conta Corrente"` | Nome da conta |
| `midaz_onboarding.account.alias` | string | `"CC-001"` | Alias da conta |
| `midaz_onboarding.account.type` | string | `"asset"` | Tipo: asset, liability, equity, income, expense |
| `midaz_onboarding.account.status` | string | `"active"` | Status: active, inactive |
| `midaz_onboarding.account.metadata.*` | any | — | Campos customizados da conta |

**Filtros comuns:**
- CNPJ base (8 dígitos): `{{ midaz_onboarding.organization.0.legal_document | slice:':8' }}`
- CNPJ formatado: `{{ midaz_onboarding.organization.0.legal_document }}`

---

### `midaz_transaction`
Dados transacionais do Midaz (saldos, operações, rotas).

| Campo | Tipo | Exemplo | Descrição |
|-------|------|---------|-----------|
| `midaz_transaction.operation_route.code` | string | `"161-90"` | Código COSIF da operação |
| `midaz_transaction.operation_route.description` | string | `"Depósitos à Vista"` | Descrição da operação |
| `midaz_transaction.balance.available` | decimal | `150000.00` | Saldo disponível |
| `midaz_transaction.balance.on_hold` | decimal | `5000.00` | Saldo bloqueado |
| `midaz_transaction.balance.scale` | int | `2` | Escala do valor (2 = centavos) |
| `midaz_transaction.operation.id` | uuid | `"op_01abc..."` | ID da operação |
| `midaz_transaction.operation.amount` | decimal | `1000.00` | Valor da operação |
| `midaz_transaction.operation.type` | string | `"credit"` | Tipo: debit, credit |
| `midaz_transaction.operation.created_at` | datetime | `"2025-12-01T10:00:00Z"` | Data/hora da operação |
| `midaz_transaction.operation.metadata.*` | any | — | Campos customizados da operação |

**Filtros comuns:**
- Valor monetário BACEN: `{{ midaz_transaction.balance.available | floatformat:2 }}`
- Data BACEN: `{{ midaz_transaction.operation.created_at | date:"Ymd" }}`

---

### `midaz_onboarding_metadata` / `midaz_transaction_metadata`
Campos de metadata customizados. Usados para informações regulatórias específicas não presentes no schema padrão do Midaz. Definidos por cada cliente/instituição.

**Acesso:** via `*.metadata.{campo}` nas entidades correspondentes.

**Campos comuns por regulação:**

| Regulação | Campo | Acesso |
|-----------|-------|--------|
| FATCA/CRS | GIIN | `midaz_onboarding.organization.0.metadata.giin` |
| FATCA/CRS | Categoria declarante | `midaz_onboarding.organization.0.metadata.categoria_declarante` |
| FATCA/CRS | País de residência | `midaz_onboarding.organization.0.metadata.pais_residencia` |
| CADOC | Código instituição | `midaz_onboarding.organization.0.metadata.codigo_instituicao` |
| CADOC | Tipo de pessoa | `midaz_onboarding.organization.0.metadata.tipo_pessoa` |

> **Note:** Metadata fields are customer-defined. Always confirm availability with the client before mapping. Mark as `source: metadata` and `confidence: MEDIUM` when used.

---

### `crm`
Dados do CRM — sistema de gestão de clientes. Fonte primária para dados cadastrais de pessoas físicas e jurídicas.

| Campo | Tipo | Exemplo | Descrição |
|-------|------|---------|-----------|
| `crm.holder.document` | string | `"12345678901"` | CPF ou CNPJ do titular |
| `crm.holder.name` | string | `"João Silva"` | Nome completo do titular |
| `crm.holder.type` | string | `"natural_person"` | Tipo: natural_person, legal_person |
| `crm.holder.addresses.primary.line1` | string | `"Av. Paulista, 1000"` | Endereço linha 1 |
| `crm.holder.addresses.primary.line2` | string | `"Sala 200"` | Endereço linha 2 |
| `crm.holder.addresses.primary.city` | string | `"São Paulo"` | Cidade |
| `crm.holder.addresses.primary.state` | string | `"SP"` | Estado (UF) |
| `crm.holder.addresses.primary.postal_code` | string | `"01310100"` | CEP (8 dígitos) |
| `crm.holder.addresses.primary.country` | string | `"BRA"` | País (código ISO-3) |
| `crm.holder.contact.email` | string | `"joao@email.com"` | Email |
| `crm.holder.contact.phone` | string | `"+5511999999999"` | Telefone (E.164) |
| `crm.holder.natural_person.date_of_birth` | date | `"1985-03-15"` | Data de nascimento (pessoa física) |
| `crm.holder.natural_person.nationality` | string | `"BRA"` | Nacionalidade (ISO-3) |
| `crm.holder.legal_person.founded_at` | date | `"2010-06-01"` | Data de constituição (pessoa jurídica) |
| `crm.alias.banking_details.branch` | string | `"0001"` | Agência bancária |
| `crm.alias.banking_details.account_number` | string | `"123456-7"` | Número da conta |
| `crm.alias.banking_details.account_type` | string | `"checking"` | Tipo: checking, savings |
| `crm.alias.metadata.*` | any | — | Campos customizados do alias |

---

## Variáveis globais injetadas pelo Reporter

O Reporter injeta automaticamente no contexto de cada template, sem necessidade de mapeamento:

| Variável | Tipo | Exemplo | Descrição |
|----------|------|---------|-----------|
| `report_date` | datetime | `"2025-12-31T23:59:59Z"` | Data/hora de geração do relatório |
| `reference_period` | string | `"2025-12"` | Período de referência |
| `institution_cnpj` | string | `"12345678000190"` | CNPJ da instituição gerando o relatório |

---

## Convenção de nomenclatura (OBRIGATÓRIO)

Todos os campos em templates `.tpl` DEVEM usar **snake_case**. Nunca camelCase.

| API retorna | Usar no template | ✓/✗ |
|-------------|-----------------|-----|
| `legalDocument` | `legal_document` | ✅ |
| `taxId` | `tax_id` | ✅ |
| `openingDate` | `opening_date` | ✅ |
| `legalDocument` | `legalDocument` | ❌ NUNCA |

---

## Data sources dinâmicos (clientes enterprise)

Clientes da Lerian podem registrar data sources adicionais no Reporter além dos documentados aqui. Quando o agente encontrar referências a campos não listados neste arquivo:

1. Tratar como campo customizado
2. Marcar confiança como MEDIUM ou LOW
3. Solicitar confirmação do usuário antes de finalizar o mapeamento
4. Documentar como `source: custom` no dicionário gerado

---

*Última atualização: 2026-03-08 | Maintainer: ring:finops-team*
