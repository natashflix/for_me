#!/bin/bash
# Скрипт для загрузки проекта на GitHub

set -e

echo "🚀 Настройка проекта для GitHub"
echo ""

# Проверка безопасности
echo "🔒 Проверка безопасности..."
if [ -f .env ]; then
    if git check-ignore .env 2>/dev/null; then
        echo "✅ .env будет игнорироваться Git"
    else
        echo "⚠️  ВНИМАНИЕ: .env не в .gitignore!"
        read -p "Продолжить? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
else
    echo "ℹ️  .env не существует (это нормально)"
fi

# Инициализация Git
if [ ! -d .git ]; then
    echo ""
    echo "📦 Инициализация Git репозитория..."
    git init
    echo "✅ Git инициализирован"
else
    echo "✅ Git уже инициализирован"
fi

# Добавление файлов
echo ""
echo "➕ Добавление файлов..."
git add .
echo "✅ Файлы добавлены"

# Проверка статуса
echo ""
echo "📋 Статус (первые 20 файлов):"
git status --short | head -20

# Проверка, что .env не добавлен
if git status --short | grep -q "^A.*\.env$"; then
    echo ""
    echo "❌ ОШИБКА: .env попал в коммит!"
    echo "Удаляю .env из индекса..."
    git reset HEAD .env
    echo "✅ .env удален из индекса"
fi

echo ""
echo "✅ Готово к коммиту!"
echo ""
echo "📝 Следующие шаги:"
echo "1. Создайте репозиторий на GitHub.com"
echo "2. Выполните:"
echo "   git commit -m 'Initial commit: FOR ME product compatibility system'"
echo "   git remote add origin https://github.com/YOUR_USERNAME/for-me.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
