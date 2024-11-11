import json

import requests
from copy import deepcopy
from neo4j import GraphDatabase

USER_ID_sec = "287263552"


def get_followers(user_id, params, level):
    """Получить фолловеров на указанном уровне"""
    params = deepcopy(params)
    params["user_id"] = user_id
    url = "https://api.vk.com/method/users.getFollowers"
    params['fields'] = "sex,screen_name,city"

    response = requests.get(url, params=params)
    data = response.json()

    followers = data.get("response", {}).get("items", [])

    if level < 2:
        for follower in followers:
            new_user_id = follower['id']
            follower['followers'] = get_followers(new_user_id, params, level + 1)
            follower['groups'] = get_subscriptions(new_user_id, params)

    return followers


def get_subscriptions(user_id, params):
    """Получить подписки пользователя"""
    params = deepcopy(params)
    params["user_id"] = user_id
    url = "https://api.vk.com/method/users.getSubscriptions"
    params['extended'] = 1

    response = requests.get(url, params=params)
    data = response.json()

    return data.get("response", {}).get("items", [])


def save_to_neo4j(followers_data, level=1, max_level=2):
    """Сохраняет данные о пользователях, их фолловерах и группах в Neo4j, включая несколько уровней вложенности"""
    uri = "bolt://localhost:7687"  # Адрес вашего Neo4j сервера
    username = "neo4j"  # Имя пользователя
    password = "postgres"  # Ваш пароль
    driver = GraphDatabase.driver(uri, auth=(username, password))

    def create_user(tx, user_id, screen_name, full_name, sex, city):
        """Создает пользователя в базе данных Neo4j"""
        query = (
            "MERGE (u:User {id: $user_id}) "
            "ON CREATE SET u.screen_name = $screen_name, "
            "u.name = $full_name, u.sex = $sex, u.city = $city"
        )
        tx.run(query, user_id=user_id, screen_name=screen_name, full_name=full_name, sex=sex, city=city)

    def create_group(tx, group_id, group_name, screen_name):
        """Создает группу в базе данных Neo4j"""
        query = (
            "MERGE (g:Group {id: $group_id}) "
            "ON CREATE SET g.name = $group_name, g.screen_name = $screen_name"
        )
        tx.run(query, group_id=group_id, group_name=group_name, screen_name=screen_name)

    def create_follow_relation(tx, follower_id, followed_id):
        """Создает связь Follow между пользователями"""
        query = (
            "MATCH (f:User {id: $follower_id}), (t:User {id: $followed_id}) "
            "MERGE (f)-[:FOLLOW]->(t)"
        )
        tx.run(query, follower_id=follower_id, followed_id=followed_id)

    def create_subscribe_relation(tx, subscriber_id, subscribed_id):
        """Создает связь Subscribe между пользователем и группой"""
        query = (
            "MATCH (s:User {id: $subscriber_id}), (g:Group {id: $subscribed_id}) "
            "MERGE (s)-[:SUBSCRIBE]->(g)"
        )
        tx.run(query, subscriber_id=subscriber_id, subscribed_id=subscribed_id)

    with driver.session() as session:
        def process_user(user_data, current_level):
            user_id = user_data['id']
            screen_name = user_data.get('screen_name', '')
            full_name = f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}"
            sex = user_data.get('sex', '')
            city = user_data.get('city', {}).get('title', '') if user_data.get('city') else ''

            session.execute_write(create_user, user_id, screen_name, full_name, sex, city)

            for follower in user_data.get('followers', []):
                follower_id = follower['id']
                follower_screen_name = follower.get('screen_name', '')
                follower_full_name = f"{follower.get('first_name', '')} {follower.get('last_name', '')}"
                follower_sex = follower.get('sex', '')
                follower_city = follower.get('city', {}).get('title', '') if follower.get('city') else ''

                session.execute_write(create_user, follower_id, follower_screen_name, follower_full_name, follower_sex,
                                      follower_city)

                session.execute_write(create_follow_relation, follower_id, user_id)

                if current_level < max_level:
                    process_user(follower, current_level + 1)

            for group in user_data.get('groups', []):
                group_id = group['id']
                group_name = group.get('name', '')
                group_screen_name = group.get('screen_name', '')

                session.execute_write(create_group, group_id, group_name, group_screen_name)

                session.execute_write(create_subscribe_relation, user_id, group_id)

        for user in followers_data:
            process_user(user, 1)

    driver.close()


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return filename


if __name__ == "__main__":
    TOKEN = TOKEN_sec
    USER_ID = USER_ID_sec

    print("Starting requests...")

    params = {
        "v": "5.199",
        "access_token": TOKEN,
    }

    followers_data = get_followers(USER_ID, params, level=0)

    save_to_json(followers_data, 'new_data.json')
    save_to_neo4j(followers_data)

    print("Finished.")
