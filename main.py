import asyncio
import aiohttp
from copy import deepcopy
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_config():
    load_dotenv()
    config = {
        "TOKEN": os.getenv("TOKEN"),
        "USER_ID": os.getenv("USER_ID"),
        "URI": os.getenv("DB_URI"),
        "USERNAME": os.getenv("DB_USERNAME"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
    }
    return config


async def get_followers(user_id, params, level, session, max_level=2):
    url = "https://api.vk.com/method/users.getFollowers"
    params = deepcopy(params)
    params["user_id"] = user_id
    params['fields'] = "sex,screen_name,city"

    try:
        async with session.get(url, params=params) as response:
            data = await response.json()
            followers = data.get("response", {}).get("items", [])
            logger.info(f"Получены фолловеры для user_id={user_id} на уровне {level}")
    except Exception as e:
        logger.error(f"Ошибка при получении фолловеров для user_id={user_id}: {e}")
        return []

    if level <= max_level:
        tasks = []
        for follower in followers:
            new_user_id = follower['id']
            tasks.append(get_followers(new_user_id, params, level + 1, session, max_level))
            follower['groups'] = await get_subscriptions(new_user_id, params, session)

        followers_data = await asyncio.gather(*tasks)
        for follower, data in zip(followers, followers_data):
            follower['followers'] = data

    return followers


async def get_subscriptions(user_id, params, session):
    url = "https://api.vk.com/method/users.getSubscriptions"
    params = deepcopy(params)
    params["user_id"] = user_id
    params['extended'] = 1

    try:
        async with session.get(url, params=params) as response:
            data = await response.json()
            logger.info(f"Получены подписки для user_id={user_id}")
            return data.get("response", {}).get("items", [])
    except Exception as e:
        logger.error(f"Ошибка при получении подписок для user_id={user_id}: {e}")
        return []


def save_to_neo4j(followers_data, config, max_level=3):
    """Сохраняет данные о пользователях, их фолловерах и группах в Neo4j, включая несколько уровней вложенности"""
    uri = config["URI"]
    username = config["USERNAME"]
    password = config["PASSWORD"]
    driver = GraphDatabase.driver(uri, auth=(username, password))

    def create_user(tx, user_id, screen_name, full_name, sex, city):
        query = (
            "MERGE (u:User {id: $user_id}) "
            "ON CREATE SET u.screen_name = $screen_name, "
            "u.name = $full_name, u.sex = $sex, u.city = $city"
        )
        tx.run(query, user_id=user_id, screen_name=screen_name, full_name=full_name, sex=sex, city=city)

    def create_group(tx, group_id, group_name, screen_name):
        query = (
            "MERGE (g:Group {id: $group_id}) "
            "ON CREATE SET g.name = $group_name, g.screen_name = $screen_name"
        )
        tx.run(query, group_id=group_id, group_name=group_name, screen_name=screen_name)

    def create_follow_relation(tx, follower_id, followed_id):
        query = (
            "MATCH (f:User {id: $follower_id}), (t:User {id: $followed_id}) "
            "MERGE (f)-[:FOLLOW]->(t)"
        )
        tx.run(query, follower_id=follower_id, followed_id=followed_id)

    def create_subscribe_relation(tx, subscriber_id, subscribed_id):
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
            logger.debug(f"Пользователь {user_id} добавлен в Neo4j")

            for follower in user_data.get('followers', []):
                follower_id = follower['id']
                follower_screen_name = follower.get('screen_name', '')
                follower_full_name = f"{follower.get('first_name', '')} {follower.get('last_name', '')}"
                follower_sex = follower.get('sex', '')
                follower_city = follower.get('city', {}).get('title', '') if follower.get('city') else ''

                session.execute_write(create_user, follower_id, follower_screen_name, follower_full_name, follower_sex,
                                      follower_city)
                session.execute_write(create_follow_relation, follower_id, user_id)
                logger.debug(f"Отношение FOLLOW между {follower_id} и {user_id} создано")

                if current_level <= max_level:
                    process_user(follower, current_level + 1)

            for group in user_data.get('groups', []):
                group_id = group['id']
                group_name = group.get('name', '')
                group_screen_name = group.get('screen_name', '')

                session.execute_write(create_group, group_id, group_name, group_screen_name)
                session.execute_write(create_subscribe_relation, user_id, group_id)
                logger.debug(f"Отношение SUBSCRIBE между {user_id} и группой {group_id} создано")

        for user in followers_data:
            process_user(user, 1)

    driver.close()
    logger.info("Сохранение данных в Neo4j завершено")


async def main():
    config = load_config()
    logger.info("Запуск программы")

    params = {
        "v": "5.199",
        "access_token": config["TOKEN"],
    }

    async with aiohttp.ClientSession() as session:
        followers_data = await get_followers(config["USER_ID"], params, level=0, session=session, max_level=1)

    save_to_neo4j(followers_data, config, max_level=1)
    logger.info("Программа завершена")


if __name__ == "__main__":
    asyncio.run(main())
