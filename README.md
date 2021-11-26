# FISH SHOP BOT

![gif](https://s10.gifyu.com/images/fish_shop_bot_.gif)

App represents telegram bot with limited functionality for customers of "Fish Shop". "Fish shop" is an online shop hosted on [Elasticpath](https://www.elasticpath.com/) e-commerce platform.

Bot allows to user:
- interact with the catalog of products
- interact with his cart (add, remove products)

Link to telegram bot: [Bot](https://t.me/devman_fish_shop_bot)

## Install

At least Python 3.8 and Git should be already installed.

1. Clone the repository
```
git clone https://github.com/balancy/fish-shop-bot.git
```

2. Go inside cloned repository, create and activate virtal environment:
```console
python -m venv env
source env/bin/activate (env\scripts\activate for Windows)
```

3. Install dependecies:
```console
pip install -r requirements.txt
```

4. Rename `.env.example` to `.env` and define environment variables

- `CLIENT_ID` - your [elasticpath](https://www.elasticpath.com/) client id
- `TG_BOT_TOKEN` - token of your telegram fish shop bot
- `LOGS_BOT_TOKEN` - token of your telegram logs bot
- `TG_USER_CHAT_ID` - id of your telegram user chat

## Launch bot

```console
python bot.py
```