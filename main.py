from copy import deepcopy
import requests
import json
import os

USER_ID_sec = "287263552"


def get_friends(params):
    params = deepcopy(params)
    url = f"https://api.vk.com/method/friends.get"
    params["fields"] = "contacts"
    response = requests.get(url, params=params)
    data = response.json()

    for friend in data["response"]["items"]:
        keys_to_remove = [key for key in friend if key not in {"id", "first_name", "last_name"}]
        for key in keys_to_remove:
            del friend[key]

    return data


def get_groups(params):
    params = deepcopy(params)
    url = f"https://api.vk.com/method/groups.get"
    params['extended'] = 1
    response = requests.get(url, params=params)
    data = response.json()

    for group in data["response"]["items"]:
        keys_to_remove = [key for key in group if key not in {"id", "name", "screen_name"}]
        for key in keys_to_remove:
            del group[key]

    return data


def get_followers(params):
    params = deepcopy(params)
    url = f"https://api.vk.com/method/users.getFollowers"
    params['fields'] = "screen_name"
    response = requests.get(url, params=params)
    data = response.json()

    for follower in data["response"]["items"]:
        keys_to_remove = [key for key in follower if key not in {"id", "first_name", "last_name"}]
        for key in keys_to_remove:
            del follower[key]

    return data


def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return filename


if __name__ == "__main__":

    TOKEN = input("Enter TOKEN (enter to use mine) = ")

    USER_ID = input(f"Enter USER_ID (enter to use {USER_ID_sec}) = ")

    if not USER_ID:
        USER_ID = USER_ID_sec

    print("Starting requests...")
    params = {
        "user_id": USER_ID,
        "v": "5.199",
        "access_token": TOKEN,
    }

    friends_file = save_to_json(get_friends(params), 'friends.json')
    groups_file = save_to_json(get_groups(params), 'groups.json')
    followers_file = save_to_json(get_followers(params), 'followers.json')

    files = [friends_file, groups_file, followers_file]

    print("Finished. Your files:")
    for file in files:
        full_path = os.path.abspath(file)
        print(f"File: {file}")
        print(f"Full Path: {full_path}")

