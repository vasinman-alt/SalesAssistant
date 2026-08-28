# Sales Assistant — Архитектура v5.0 (эталон)

> Этот документ — единственный источник истины. Он заменяет все предыдущие версии
> (v1.0–v4.0) и явно разрешает все накопившиеся противоречия между ними. Ничего
> из более ранних документов не действует, если это не подтверждено здесь.

---

## 0. Что этот документ окончательно решает

Несколько вопросов расходились между версиями — фиксирую финальный ответ по каждому:

| Вопрос | Решение |
|---|---|
| `Activity` — сфера деятельности или взаимодействие? | **Сфера деятельности** (как в v1). Взаимодействие — отдельная сущность `Interaction` (как было изначально, до путаницы в v3/v4). |
| Deal — обязательная сущность или отключаемый модуль? | **Отключаемый модуль**, как решили с самого начала. v4 сделал его обязательным — это отменяется. |
| Масштаб ИИ — автономная Sales Intelligence Platform или узкая функция? | **Узкая функция.** ИИ отвечает только за обогащение карточки компании и поиск контактов (сайт/соцсети). Никакого Lead Scoring, ICP, автономного NL-планировщика, Entity Resolution как отдельной сложной подсистемы — это было спроектировано для гораздо большего продукта, чем нужен сейчас. |
| P2P-синхронизация, теги, пользовательские поля | **Остаются в силе**, как решили раньше. В v3/v4 про них забыли — здесь они возвращены и сведены воедино с остальной моделью. |
| Установка без прав администратора | **Остаётся жёстким требованием**, в том числе для ИИ-модуля (см. раздел 9). |
| Физическое удаление компании (было в реальном коде) | **Отменяется.** Только архивация (soft delete). Уже зафиксировано как обязательное требование к БД. |

---

## 1. Цель и принципы

Настольная CRM для Windows для активных B2B-продаж: поиск потенциальных клиентов,
собственная база предприятий, история взаимодействий, задачи, документы, аналитика,
точечное ИИ-обогащение карточек.

Принципы (без изменений с v1):

1. Максимум автоматизации там, где это дёшево и надёжно (детерминированный код);
   ИИ — только там, где детерминированный код объективно не справляется
   (понимание неструктурированного текста, сопоставление соцсетей).
2. Никакого дублирования данных — каждая самостоятельная сущность живёт в своей таблице.
3. История не удаляется — вместо физического удаления везде архивация.
4. Всё связано между собой — переход между связанными объектами в один клик.
5. Минимум действий пользователя.
6. **Любое ИИ-действие — это предложение (diff), а не изменение.** Запись в БД
   происходит только после подтверждения пользователем.

---

## 2. Технологический стек

| Слой | Выбор |
|---|---|
| Язык | Python 3.12+ |
| GUI | PySide6 (QDockWidget, QSS-темы) |
| ORM / миграции | SQLAlchemy 2.x + Alembic |
| БД | SQLite (WAL-режим, foreign keys включены) |
| Поиск предприятий | Checko API (единственный источник сейчас; открытые источники ФНС/ГИР БО — позже, как отдельный провайдер) |
| ИИ-обогащение (опционально) | Локальная модель через Ollama, провайдеро-независимый интерфейс (см. раздел 8) |
| Упаковка | PyInstaller (onedir) + Inno Setup (`PrivilegesRequired=lowest`) |

---

## 3. Установка и хранение данных

Без изменений с v2 — принцип и структура те же:

```
Portable-режим (папка с exe доступна на запись):
  <папка_с_программой>/SalesAssistant.exe
  <папка_с_программой>/data/{sales.db, backups/, cache/, imports/, documents/}

Установленный режим (через инсталлятор, без UAC):
  %LOCALAPPDATA%\Programs\SalesAssistant\
  %LOCALAPPDATA%\SalesAssistant\data\
```

**Важное уточнение:** ИИ-модуль обогащения (Ollama + модель, несколько гигабайт)
устанавливается **отдельно и опционально**, а не в составе основного инсталлятора.
Основная CRM обязана полностью работать без него. Это прямое следствие требования
"установка без прав администратора и минимум трения" — тяжёлая ИИ-зависимость не
должна быть входным барьером для использования CRM.

---

## 4. Общая архитектура приложения

```
┌──────────────────────────────────────────────┐
│ UI (PySide6)                                  │
├──────────────────────────────────────────────┤
│ ViewModel / Controller                        │
├──────────────────────────────────────────────┤
│ Service layer                                 │  CompanyService, ContactService,
│                                                │  InteractionService, TaskService,
│                                                │  DocumentService, SearchService,
│                                                │  EnrichmentService (опц.), SyncService (v0.8+)
├──────────────────────────────────────────────┤
│ Repository layer (SQLAlchemy)                 │
├──────────────────────────────────────────────┤
│ SQLite (sales.db)                             │
└──────────────────────────────────────────────┘
```

Правило прежнее и обязательное: **UI никогда не обращается к репозиториям и не
управляет сессией БД напрямую** — только через сервисы. В нынешнем коде это
правило нарушено (все `ui/*.py` импортируют `SessionLocal` напрямую) — это
технический долг, который нужно закрыть в рамках Этапа 0 (см. раздел 12).

Модуль обогащения (`EnrichmentService`) физически изолирован от остальных
сервисов — ядро CRM не должно падать или менять поведение, если ИИ-модуль не
установлен (тот же принцип, что уже применялся к модулю Deal).

---

## 5. Модель данных — ядро CRM

### 5.1 Идентификаторы и синхронизационные поля

Первичные ключи — **UUID (TEXT)**. У каждой изменяемой сущности — три поля:

```
updated_at   DATETIME NOT NULL
origin_node  UUID NOT NULL   -- id узла (инсталляции), ОДИН И ТОТ ЖЕ для всех
                             -- записей, созданных на этом компьютере
version      INTEGER NOT NULL DEFAULT 1
```

**Важное исправление найденного в коде бага:** `origin_node` должен генерироваться
**один раз** при первом запуске приложения и храниться в `app_settings.json`
(ключ `node_id`), а не заново на каждую запись. Единая точка получения — функция
`get_node_id()` в `config/settings.py`, используемая всеми сервисами без исключения.

### 5.2 Справочники

```sql
Region(id UUID PK, name TEXT, code TEXT)

Activity(                        -- сфера деятельности (НЕ взаимодействие)
  id UUID PK,
  name TEXT,                     -- "Производство пива"
  okved_code TEXT NULL,
  description TEXT NULL,
  industry TEXT NULL
)
```

### 5.3 Company

```sql
Company(
  id UUID PK,
  name TEXT NOT NULL,
  display_name TEXT NULL,
  legal_name TEXT NULL,
  inn TEXT NULL,
  region_id UUID NULL FK -> Region,
  legal_address TEXT NULL,
  actual_address TEXT NULL,
  website TEXT NULL,
  comment TEXT NULL,
  source TEXT NULL,
  status TEXT NOT NULL DEFAULT 'active',   -- active | archived (НЕ удаляется физически)
  custom_fields JSON NULL,
  created_at DATETIME, updated_at DATETIME,
  created_by UUID FK -> User,
  origin_node UUID, version INTEGER DEFAULT 1
)

-- Обязательный частичный уникальный индекс — защита от дублей при повторном
-- импорте/поиске одной и той же организации:
CREATE UNIQUE INDEX ux_company_inn ON companies(inn) WHERE inn IS NOT NULL AND inn != '';

CompanyActivity(company_id UUID FK, activity_id UUID FK, PRIMARY KEY (company_id, activity_id))
```

`CompanyService.delete()` **упраздняется**. Единственный метод для "убрать компанию" —
`CompanyService.archive(session, company_id)`, устанавливающий `status = 'archived'`.
Физическое удаление со всеми связями — если вообще нужно — отдельная redko используемая
административная операция с явным другим текстом предупреждения, не путающаяся с
обычным пользовательским действием.

### 5.4 Contact

```sql
Contact(
  id UUID PK,
  company_id UUID NULL FK -> Company,
  contact_type TEXT NOT NULL,   -- person | phone_shared | email_shared | telegram | whatsapp | department | reception
  full_name TEXT NULL, position TEXT NULL, department TEXT NULL,
  comment TEXT NULL, custom_fields JSON NULL,
  status TEXT NOT NULL DEFAULT 'active',    -- active | archived
  created_at DATETIME, updated_at DATETIME,
  origin_node UUID, version INTEGER DEFAULT 1
)

ContactPhone(id UUID PK, contact_id UUID FK, phone TEXT, label TEXT NULL)
ContactEmail(id UUID PK, contact_id UUID FK, email TEXT, label TEXT NULL)
ContactMessenger(id UUID PK, contact_id UUID FK, type TEXT, value TEXT)  -- включая соцсети, найденные ИИ-модулем
```

### 5.5 Interaction (история) — append-only

Имя окончательно закреплено как `Interaction` (не `Activity`).

```sql
Interaction(
  id UUID PK,
  company_id UUID FK -> Company,
  contact_id UUID NULL FK -> Contact,
  type TEXT,                  -- call | meeting | letter | video | message | note
  event_date DATETIME, entry_date DATETIME,
  subject TEXT, description TEXT, result TEXT NULL, next_action TEXT NULL,
  is_voided BOOLEAN DEFAULT FALSE,
  voided_reason TEXT NULL,
  replaces_id UUID NULL FK -> Interaction,
  created_by UUID FK -> User,
  origin_node UUID
)
```

Первая запись создаётся автоматически при создании карточки компании. Исправления
вносятся не через UPDATE, а через `is_voided = true` + новую запись со ссылкой
`replaces_id`.

### 5.6 Task

```sql
Task(
  id UUID PK,
  company_id UUID NULL FK -> Company,
  contact_id UUID NULL FK -> Contact,
  interaction_id UUID NULL FK -> Interaction,
  title TEXT, description TEXT NULL,
  due_date DATETIME NULL, priority TEXT, status TEXT,
  assignee_id UUID NULL FK -> User,
  reminder_at DATETIME NULL,
  created_at DATETIME, completed_at DATETIME NULL,
  updated_at DATETIME, origin_node UUID, version INTEGER DEFAULT 1
)
```

### 5.7 Document + полиморфные связи

```sql
Document(
  id UUID PK,
  file_path TEXT,             -- ОБЯЗАТЕЛЬНО путь внутри data/documents/<company_id>/,
                               -- не путь к исходному файлу пользователя (см. ниже)
  original_name TEXT, doc_type TEXT,
  status TEXT DEFAULT 'active',
  uploaded_at DATETIME, uploaded_by UUID FK -> User,
  origin_node UUID
)

DocumentLink(
  document_id UUID FK -> Document,
  entity_type TEXT,            -- 'company' | 'contact' | 'interaction' | 'task'
  entity_id UUID,
  PRIMARY KEY (document_id, entity_type, entity_id)
)
```

**Обязательное исправление найденного в коде бага:** `DocumentService.attach_to_entity()`
должен **копировать** файл (`shutil.copy2`) в `DOCUMENTS_DIR / <company_id> / <имя>`
и сохранять путь именно к копии. Сейчас сохраняется путь к оригинальному файлу
пользователя — это ломает и бэкапы (файл вне `data/`), и `remove(delete_file=True)`
рискует удалить единственный оригинал пользователя, а не копию.

### 5.8 Пользователи, роли — закладка под рабочие группы

```sql
User(id UUID PK, username TEXT, display_name TEXT, is_local BOOLEAN DEFAULT TRUE, created_at DATETIME)
Role(id UUID PK, name TEXT)         -- 'owner' | 'manager' | 'viewer'
UserRole(user_id UUID FK, role_id UUID FK, PRIMARY KEY (user_id, role_id))
```

### 5.9 Пользовательские поля

```sql
CustomFieldDefinition(
  id UUID PK, entity_type TEXT,     -- 'company' | 'contact'
  field_key TEXT, field_label TEXT,
  field_type TEXT,                  -- text | number | date | select
  select_options JSON NULL, sort_order INTEGER
)
```
Значения — в JSON-колонке `custom_fields` на `Company`/`Contact`.

### 5.10 Теги

```sql
Tag(id UUID PK, name TEXT, color TEXT NULL)
EntityTag(tag_id UUID FK, entity_type TEXT, entity_id UUID, PRIMARY KEY (tag_id, entity_type, entity_id))
```

### 5.11 Deal — отдельный отключаемый модуль

Подтверждено: **не обязательная сущность ядра**, а модуль по паттерну `ModuleRegistry`,
включаемый в настройках. Собственные таблицы, без жёстких FK-каскадов с ядром.

```sql
Deal(
  id UUID PK,
  company_id UUID FK -> Company,
  title TEXT,
  stage_id UUID FK -> DealStage,   -- настраиваемые стадии, не хардкод
  amount DECIMAL NULL, currency TEXT DEFAULT 'RUB',
  expected_close_date DATE NULL, status TEXT,
  created_at DATETIME, updated_at DATETIME, origin_node UUID
)

DealStage(id UUID PK, name TEXT, sort_order INTEGER, is_won BOOLEAN DEFAULT FALSE, is_lost BOOLEAN DEFAULT FALSE)
```

(Единственное заимствование из v4, которое стоило сохранить — настраиваемые стадии
воронки вместо жёстко зашитого списка. Модуль остаётся опциональным.)

---

## 6. Поиск предприятий

Без изменений с решения предыдущего разговора: **единственный источник сейчас —
Checko API**. Локальный FTS5-индекс на открытых данных ФНС/ГИР БО (`importer.py`,
`indexer.py`, `schema.py` — уже написаны, но не подключены) откладывается на более
поздний этап как альтернативный/резервный провайдер, а не переделывается сейчас.

Технические требования к текущей реализации (по итогам код-ревью):

- Обогащение результатов поиска финансовыми показателями (`get_finances`) — **не
  на GUI-потоке**. Сейчас это последовательные блокирующие HTTP-запросы в обработчике
  клика, замораживающие интерфейс. Выносится в `QThread`/`QRunnable` с прогресс-баром
  и отменой.
- Сортировка результатов по числовым колонкам (оборот) — через `QTableWidgetItem`
  с переопределённым `__lt__`, а не через ручную Python-пересортировку, конфликтующую
  со встроенной сортировкой Qt (уже исправлено в присланном коде).
- Поиск по локальной базе компаний (`CompanyService.search`) должен быть регистронезависимым
  и для кириллицы — для этого нужно зарегистрировать Python-реализацию `LOWER()`/`UPPER()`
  на SQLite-соединении (встроенные функции SQLite ASCII-only и не понимают кириллицу).

---

## 7. Обогащение карточек и поиск контактов — единственная задача ИИ

Это единственная функция, где в системе участвует ИИ. Никакого автономного
планировщика, никакого Lead Scoring/ICP, никакой сложной Entity Resolution как
отдельной подсистемы — при таком узком назначении это не нужно.

### 7.1 Сценарий

```
Пользователь на карточке компании нажимает "Обогатить"
   → детерминированный код находит и скачивает сайт компании
   → детерминированный код извлекает то, что извлекается без ИИ:
     телефоны/email по регулярным выражениям, JSON-LD/schema.org разметку,
     ссылки на соцсети по паттернам URL
   → ИИ используется только там, где детерминированный код не справляется:
     - разобрать неструктурированный текст "О компании"
     - определить, какая из найденных ссылок на соцсети — правда официальная
       страница компании, а не случайная кнопка "поделиться"
     - нормализовать/классифицировать сферу деятельности по свободному тексту
   → результат показывается как diff (было / стало, с источником и датой)
   → пользователь подтверждает — только тогда данные попадают в Contact/Company
```

Тот же принцип "детерминированный код — данные, ИИ — понимание", который был
правильно сформулирован в v3, просто применён к реально нужному масштабу задачи,
а не к целой платформе.

### 7.2 Минимально необходимая модель данных для доверия к источнику

Полноценный Trust Layer из v3/v4 (`RawArtifact → ExtractedClaim → Evidence →
AcceptedField`, Conflict Center, Verification Engine с пятью статусами) избыточен
для функции "обогатить одну карточку по кнопке". Достаточно облегчённой версии:

```sql
EnrichmentEvidence(
  id UUID PK,
  entity_type TEXT,          -- 'company' | 'contact'
  entity_id UUID,
  field_name TEXT,           -- какое поле предложено изменить
  proposed_value TEXT,
  source_type TEXT,          -- 'website' | 'social' | 'checko'
  source_url TEXT NULL,
  confidence REAL NULL,      -- 0.0–1.0, если применимо (для ИИ-выводов)
  extracted_by TEXT,         -- 'deterministic' | 'ai'
  fetched_at DATETIME,
  status TEXT DEFAULT 'pending'   -- pending | accepted | rejected
)
```

Одна таблица вместо десятка — фиксирует источник и позволяет пользователю увидеть
"откуда это взялось", не требуя отдельных экранов Conflict Center/Proposal Center.
Диалог подтверждения обогащения — просто список `EnrichmentEvidence` со статусом
`pending` для конкретной карточки, с кнопками "Принять"/"Отклонить" — это тот же
паттерн diff-подтверждения, что уже реализован в диалоге поиска предприятий
("Добавить выбранные компании"), просто применённый к отдельным полям.

### 7.3 AI Gateway — границы

```
Разрешённые инструменты для ИИ:
  - fetch_page(url)               — получить содержимое страницы (уже скачанной детерминированным кодом)
  - extract_contacts(text)        — извлечь контакты из неструктурированного текста
  - classify_industry(text)       — сопоставить свободный текст со справочником Activity
  - explain_result(data)          — сформулировать понятное объяснение для пользователя

ИИ НЕ имеет:
  - прямого доступа к БД;
  - прямого доступа к интернету (только к уже скачанному контенту);
  - возможности напрямую писать в Company/Contact — только через EnrichmentEvidence;
  - права решать, сколько шагов выполнять — сценарий обогащения детерминирован,
    ИИ вызывается на конкретных, заранее определённых шагах внутри него.
```

Веб-контент считается недоверенным: команды, встреченные в тексте страницы,
игнорируются, извлечённые значения проходят валидацию перед показом пользователю,
изменения применяются только через подтверждение (раздел 7.2).

### 7.4 Локальная модель — практические ограничения

Ollama + локальная модель (например, Qwen — конкретная модель не жёстко зашита,
конфигурируется) — реализация по умолчанию, но:

- **Модуль опционален** (раздел 3) — CRM полностью работает без него; кнопка
  "Обогатить" при отсутствии ИИ-модуля выполняет только детерминированную часть
  сценария (телефоны/email/JSON-LD без разбора неструктурированного текста и без
  сопоставления соцсетей).
- Перед первым использованием — явная проверка: доступна ли Ollama, достаточно ли
  ОЗУ, показать пользователю понятную оценку ("на этом компьютере обогащение будет
  работать медленно/быстро"), а не молча зависать на первом запросе.
- Задача обогащения — не интерактивная (не блокирует ввод пользователя, выполняется
  в фоне с индикатором прогресса), поэтому даже медленный локальный инференс
  (секунды-десятки секунд) не критичен для UX так, как был бы критичен для
  интерактивного `Ctrl+K`-чата — такого чата в этой версии архитектуры нет.

---

## 8. Безопасность и приватность

- Персональные данные контактов (ФИО, телефоны, email) — учитывать 152-ФЗ при
  распространении продукта за пределы личного использования.
- Флаг `do_not_contact` на Contact — на будущее, не в MVP, но поле в схеме
  зарезервировать.
- Локальный LLM runtime — жёстко (не "по возможности") привязан к `127.0.0.1`,
  никогда не слушает на сетевом интерфейсе.
- API-ключи (Checko) хранятся в `app_settings.json`, не попадают в промпты ИИ.

---

## 9. P2P-синхронизация рабочих групп (v0.8+, без изменений с прошлого решения)

Остаётся в силе решение в пользу P2P (не облачный backend), стартуя с синхронизации
через общую папку (Яндекс.Диск/Dropbox), затем прямой LAN P2P. Конфликты — last-write-wins
по `updated_at` для мутируемых сущностей, с журналом `SyncConflictLog` для ручного
разрешения. Append-only сущности (`Interaction`, `Document`) сливаются без конфликтов.

```sql
SyncConflictLog(
  id UUID PK, entity_type TEXT, entity_id UUID,
  losing_version JSON, resolved_at DATETIME NULL, detected_at DATETIME
)
```

---

## 10. Миграции

Alembic с версионированными миграциями с первого коммита, включая изначально
неактивные `User`/`Role`/`Deal`/`SyncConflictLog`/`EnrichmentEvidence`.

---

## 11. Структура проекта

```
sales_assistant/
├── app.py, __main__.py
├── config/               paths.py, settings.py (node_id, app_settings.json)
├── db/
│   ├── models/           region, activity, company, contact, interaction,
│   │                     task, document, tag, custom_field, user, deal,
│   │                     sync_conflict, mixins
│   └── migrations/       (Alembic)
├── repositories/
├── services/              company, contact, interaction, task, document,
│                          user, module_registry
├── modules/
│   └── deals/             (отключаемый модуль, как решено)
├── search/                checko_client, service, importer, indexer, schema (резерв)
├── enrichment/             (отключаемый модуль, по аналогии с deals)
│   ├── service.py          детерминированный сценарий обогащения
│   ├── crawler.py          скачивание сайта, соблюдение robots.txt
│   ├── extractors.py       детерминированное извлечение (regex, JSON-LD)
│   ├── ai_gateway.py       границы вызова ИИ (раздел 7.3)
│   └── models.py           EnrichmentEvidence
├── ui/
│   ├── main_window.py
│   ├── panels/            navigation_panel, company_card, dashboard_panel
│   ├── dialogs/            search_dialog, enrichment_dialog
│   ├── themes/
│   └── utils/              dialogs.py (show_error_message)
├── utils/                  logging_config.py
├── tests/
└── packaging/               pyinstaller.spec, inno_setup.iss
```

---

## 12. Дорожная карта

| Этап | Содержание |
|---|---|
| **0. Фундамент** | структура, миграции с полной схемой (включая неактивные таблицы), логирование, `node_id`, portable/installed установка |
| **1. Стабилизация ядра** | закрыть найденный технический долг: `archive()` вместо `delete()`, копирование документов в managed-хранилище, единый `node_id` вместо `uuid4()` на запись, уникальный индекс на `inn`, юникодный регистронезависимый поиск, вынос сессий из UI в сервисы |
| **2. Companies** | предприятия, контакты, карточки, теги, пользовательские поля в UI |
| **3. CRM** | история (append-only), задачи, документы |
| **4. Search** | Checko UI (обогащение выручкой — вне GUI-потока), импорт/экспорт Excel/CSV |
| **5. Enrichment** | детерминированная часть обогащения (сайт, телефоны/email, JSON-LD) без ИИ |
| **6. Enrichment + AI** | опциональный ИИ-модуль (Ollama), классификация сферы деятельности, разбор неструктурированного текста, сопоставление соцсетей |
| **7. Deals module** | опциональный модуль сделок с настраиваемыми стадиями |
| **8. Workgroups** | P2P-синхронизация, роли, `SyncConflictLog` |

Явно исключено из планов (было в v3/v4, признано избыточным для нужного масштаба):
автономный NL-планировщик с многошаговым tool-calling, Lead Scoring, ICP-профили,
Entity Resolution как отдельная вероятностная подсистема, Conflict Center/Proposal
Center как отдельные полноценные экраны, `Ctrl+K` AI-командная палитра.
