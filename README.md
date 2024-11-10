# OROPO_lab4
# Установка
1. Клонируем репозиторий
```bash
git clone https://github.com/vkkuznetsov/OROPO_lab3.git
```
2. Переходим в папку с проектом
```bash
cd OROPO_lab3
```
3. Создаем виртуальное оркжуение
```bash
python -m venv venv
```
4. Активируем его

LINUX
```bash
source venv/bin/activate
```
WINDOWS (cmd)
```bash
.\venv\Scripts\activate
```
Если powershell
```bash
Set-ExecutionPolicy RemoteSigned
.\venv\Scripts\activate
```
5. Устанавливаем зависимости
```bash
pip install -r requirements.txt
```
6. Запускаем приложение
```bash
python main.py
```
Использование  
1. Вводим токен от vk api
2. Вводим айди пользователя (по умолчанию уже стоит)
3. Файлы сохраняются в корень проекта followers.json, friends.json, groups.json 
еще плюсом выводятся пути до файлов
4. Открываем файлы любым удобным способом