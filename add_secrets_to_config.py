import os
import json


def add_tokens(file_path, app_token, user_token):
    with open(file_path, "r") as file:
        json_data = json.load(file)

    secret_app_token = os.environ.get(app_token)
    secret_user_token = os.environ.get(user_token)
    if secret_app_token is None or secret_user_token is None:
        raise Exception(f"Environment variable '{secret_app_token}' and '{secret_user_token}' not set.")

    json_data["notifications"]["pushover"]["token"] = secret_app_token
    json_data["notifications"]["pushover"]["user"] = secret_user_token
    with open(file_path, "w") as file:
        json.dump(json_data, file)


if __name__ == "__main__":
    add_tokens("config.json", "APPTOKEN", "USERTOKEN")
