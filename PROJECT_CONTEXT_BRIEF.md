# 🤖 YIELDBOT AI: PROJECT CONTEXT & CURRENT STATUS BRIEF

## 📋 1. Project Overview
**Название:** YieldBot AI  
**Цель:** Полностью автономный DeFi-агент для поиска и исполнения доходных операций на Solana. Работает без участия человека после начальной настройки.  
**Текущая фаза:** Phase 2 → Phase 3 (переход от локальной интеграции к production-деплою на VPS)  
**Приоритет:** Безопасность (Devnet first), стабильность цикла, наблюдаемость, автоматическое восстановление.

## 🏗️ 2. Architecture & Tech Stack
- **Язык:** Python 3.12
- **Оркестрация:** `LangGraph` (StateGraph, conditional edges, state reducers)
- **Внешние API:** Jupiter Aggregator v6 (`quote`, `swap` endpoints)
- **Blockchain:** Solana Devnet (`solana-py`, `solders` для подписи транзакций)
- **Конфигурация:** `pydantic` + `pydantic-settings` (вложенная структура: `settings.analyzer.ema_period`, `settings.executor.max_retries` и т.д.)
- **Безопасность:** `utils/security.py` → `SecureKeyManager` (загрузка ключа из `.env`, очистка из памяти)
- **Логирование:** `logging` + JSON-форматирование, session tracking
- **Тестирование:** `test_integration.py` (mock pipeline: Analyzer → Executor → Monitor)

### 📁 Ключевая структура файлов:
```
agents/state.py          # BotState TypedDict, reducers
agents/planner.py        # PlannerAgent, perceive/create_plan, LangGraph compilation
agents/analyzer.py       # EMA расчет, detection opportunity, risk scoring
agents/executor.py       # Подпись tx, retry/backoff, симуляция для MVP
agents/monitor.py        # Health tracking, self-healing, cooldowns, P&L reports
services/jupiter_service.py # HTTP клиент к Jupiter API v6
utils/config.py          # Pydantic nested settings
utils/security.py        # SecureKeyManager
main.py                  # YieldBot class, async loop, signal handling, graph invocation
```

## ✅ 3. Completed Phases & Achievements
1. **Phase 1 (Core Architecture):** Создан LangGraph-цикл `Perceive → Analyze → Plan → Execute → Monitor`. Реализована схема состояния, конфигурация, базовые тесты.
2. **Phase 2 (Real Network Integration):** 
   - Интегрирован Jupiter API v6 (`get_quote`, `get_swap_transaction`)
   - Реализована логика подписи и отправки транзакций на Devnet
   - Исправлены импорты и конфигурация в `main.py` (переход на вложенные `settings.*`)
   - Добавлен graceful fallback на mock-данные при недоступности сети
   - ✅ `test_integration.py` успешно проходит (Analyzer, Executor, Monitor работают)
   - ✅ Граф компилируется и запускается без ошибок

## ⚠️ 4. Current Status & Known Constraints
- **Репозиторий:** `https://github.com/Abirva1g/yieldbot-ai`
- **Среда выполнения:** VPS `vm.nano` (2 vCPU / 2GB RAM / 60GB SSD, Ubuntu 22.04)
- **Проблема сети:** В sandbox/VPS заблокирован DNS или outbound-трафик. Вызовы к `quote-api.jup.ag` падают с `[Errno -5] No address associated with hostname`.
- **Решение:** `PlannerAgent.perceive()` ловит исключение и подставляет mock-данные (`price=143.50`), позволяя циклу работать стабильно.
- **Конфигурация:** `.env` на сервере еще не заполнен реальными Devnet-ключами.
- **Задержка итераций:** Захардкожена на `10 сек` в `main.py` для MVP.

## 🎯 5. Immediate Next Steps (Phase 3: Deployment & Observability)
1. 🐳 **Контейнеризация:** `Dockerfile` (python:3.12-slim) + `docker-compose.yml`
2. 📱 **Telegram Observability:** `utils/telegram_logger.py` (оповещения о старте/остановке, critical alerts, команды `/pause`, `/resume`, `/status`)
3. 🛡️ **Kill Switch:** Файловый/Redis-флаг паузы, проверяемый на каждой итерации
4. ⚙️ **Systemd + VPS:** Шаблон `yieldbot.service` для автозапуска и перезапуска при падении
5. 🌐 **Network Fix / Fallback:** Проверка DNS на VPS, настройка `.env` с Devnet RPC и тестовым ключом
6. 📊 **Live Devnet Run:** Запуск цикла с реальными котировками (если сеть доступна) или стабильным mock-режимом

## 📜 6. Operational Rules & Constraints (Strict)
- 🔒 **Devnet Only:** Никогда не использовать mainnet-ключи или RPC в `.env` до Phase 4.
- 🧩 **Config Structure:** Всегда использовать вложенные настройки: `settings.analyzer.ema_period`, `settings.executor.max_retries`, `settings.solana.rpc_url`.
- 🔄 **LangGraph State:** Все ноды должны принимать и возвращать `BotState`. Использовать `state.get()` с дефолтами.
- 🌐 **Network Resilience:** Любые HTTP/RPC вызовы обернуты в `try/except`. При падении сети → mock fallback + логирование ошибки. Цикл не должен падать.
- 🛑 **Security:** Приватный ключ никогда не логируется. Используется только `SecureKeyManager`. Очищается после подписи.
- 📝 **VPS Instructions:** Пользователь новичок. Все команды для сервера должны быть copy-paste ready, с пояснением ожидаемого вывода и проверкой успеха.
- 📦 **Code Delivery:** Большие файлы передавай через `cat > path/to/file << 'EOF' ... EOF`. Не вываливай всё одним блоком.

## 💬 7. How to Proceed
Я буду управлять деплоем пошагово. Твоя задача:
1. Подтвердить понимание текущего статуса
2. Подготовить следующий технический блок (например, `Dockerfile` + `docker-compose.yml` + `.env` template)
3. Дождаться моего подтверждения перед генерацией кода для следующей части
4. Придерживаться правил безопасности и структуры

**Готов к работе. Жду подтверждения контекста и первый блок для Phase 3.** 🚀
