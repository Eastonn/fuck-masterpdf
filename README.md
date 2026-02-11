# Удаление водяного знака Master PDF Editor

Скрипт удаляет диагональный водяной знак **«Created in Master PDF Editor»** из PDF-файлов.

## Установка

### 1. Установить uv

macOS / Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows (PowerShell):

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. Скачать проект

```bash
git clone <url-этого-репозитория>
cd remove-pdf-watermark
```

### 3. Запустить

```bash
uv run python remove_watermark.py мой_файл.pdf
```

Всё. `uv` сам скачает Python и зависимости при первом запуске.

## Примеры

```bash
# Один файл → создаст мой_файл_clean.pdf
uv run python remove_watermark.py мой_файл.pdf

# Указать имя выходного файла
uv run python remove_watermark.py мой_файл.pdf -o чистый.pdf

# Несколько файлов
uv run python remove_watermark.py file1.pdf file2.pdf file3.pdf

# Все PDF в папке
uv run python remove_watermark.py *.pdf

# Перезаписать оригинал (сохранит .bak-копию)
uv run python remove_watermark.py мой_файл.pdf --inplace
```

## Как это работает

PDF-файл, сохранённый в бесплатной версии Master PDF Editor, содержит водяной знак в виде Form XObject — отдельного объекта с красным текстом при 5% непрозрачности, наложенного поверх каждой страницы с поворотом.

Скрипт:

1. Находит эти XObject'ы по характерным признакам (красный цвет `1 0 0 scn`, шрифт `/Fm1`)
2. Удаляет ссылки на них из потока команд отрисовки каждой страницы
3. Удаляет сами объекты из ресурсов PDF
4. Сохраняет чистый файл — остальное содержимое не затрагивается
