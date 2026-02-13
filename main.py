import os
import json
import requests

# 机场的地址
url = os.environ.get("URL")

# 配置：一行账号一行密码（成对）
config = os.environ.get("CONFIG", "")

# 旧：Server酱（兼容保留，不再作为主要推送）
SCKEY = os.environ.get("SCKEY", "")

# 新：Telegram
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

login_url = f"{url}/auth/login"
check_url = f"{url}/user/checkin"


def push_telegram(text: str) -> None:
    """
    Telegram Bot API 推送
    """
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        return

    api = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": text,
        "disable_web_page_preview": True,
    }
    # 可选：想用 Markdown 就放开下面两行
    # payload["parse_mode"] = "Markdown"
    # payload["text"] = text.replace("_", "\\_")

    r = requests.post(api, json=payload, timeout=20)
    r.raise_for_status()


def push_serverchan_compat(text: str) -> None:
    """
    兼容旧的 Server酱推送（可选保留）
    """
    if not SCKEY:
        return
    push_url = f"https://sctapi.ftqq.com/{SCKEY}.send?title=机场签到&desp={text}"
    requests.post(url=push_url, timeout=20)


def sign(order: int, user: str, pwd: str) -> None:
    session = requests.session()
    header = {
        "origin": url,
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/109.0.0.0 Safari/537.36"
        ),
    }
    data = {"email": user, "passwd": pwd}

    try:
        print(f"===账号{order}进行登录...===")
        print(f"账号：{user}")

        res = session.post(url=login_url, headers=header, data=data, timeout=30).text
        response = json.loads(res)
        print(response.get("msg", res))

        # 进行签到
        res2 = session.post(url=check_url, headers=header, timeout=30).text
        result = json.loads(res2)
        msg = result.get("msg", res2)
        print(msg)

        content = f"账号：{user}\n签到结果：{msg}"

        # 推送：优先 Telegram；兼容保留 Server酱
        if TG_BOT_TOKEN and TG_CHAT_ID:
            push_telegram(content)
            print("Telegram 推送成功")
        elif SCKEY:
            push_serverchan_compat(content)
            print("Server酱 推送成功(兼容)")
    except Exception as ex:
        content = f"账号：{user}\n签到失败：{ex}"
        print(content)

        # 失败也推送
        try:
            if TG_BOT_TOKEN and TG_CHAT_ID:
                push_telegram(content)
                print("Telegram 推送成功")
            elif SCKEY:
                push_serverchan_compat(content)
                print("Server酱 推送成功(兼容)")
        except Exception as ex2:
            print(f"推送也失败：{ex2}")

    print(f"===账号{order}签到结束===\n")


if __name__ == "__main__":
    configs = config.splitlines()
    if len(configs) % 2 != 0 or len(configs) == 0:
        print("配置文件格式错误")
        raise SystemExit(1)

    user_quantity = len(configs) // 2
    for i in range(user_quantity):
        user = configs[i * 2].strip()
        pwd = configs[i * 2 + 1].strip()
        sign(i, user, pwd)
