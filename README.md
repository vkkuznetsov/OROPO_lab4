# OROPO_lab4
Использовался Python3.11.9 (но скорее всего подойдет любой из современных 3.7+)
# Установка
1. Клонируем репозиторий
```bash
git clone https://github.com/vkkuznetsov/OROPO_lab4.git
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
# Запросы
1. Всего пользователей
```
MATCH (u:User)
RETURN count(u) AS total_users
```
2. Всего групп
```
MATCH (g:Group)
RETURN count(g) AS total_groups
```
3. Топ-5 пользователей по количеству фолловеров
```
MATCH (u:User)<-[:FOLLOW]-(follower:User)
RETURN u.id AS user_id, u.name AS name, count(follower) AS follower_count
ORDER BY follower_count DESC
LIMIT 5
```
4. Топ-5 самых популярных групп
```
MATCH (g:Group)<-[:SUBSCRIBE]-(subscriber:User)
RETURN g.id AS group_id, g.name AS name, count(subscriber) AS subscriber_count
ORDER BY subscriber_count DESC
LIMIT 5
```
5. Все пользователи, которые фолловеры друг друга
```
MATCH (u1:User)-[:FOLLOW]->(u2:User)
WHERE (u2)-[:FOLLOW]->(u1)
RETURN u1.id AS user1_id, u2.id AS user2_id
```
Использование  
1. Открываем .env файл и вписываем данные
2. Запускаем
