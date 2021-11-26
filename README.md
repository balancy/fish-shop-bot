# FISH SHOP BOT

![gif](https://s10.gifyu.com/images/fish_shop_bot_.gif)

App represents telegram bot with limited functionality for customers of "Fish Shop". "Fish shop" is an online shop hosted on [Elasticpath](https://www.elasticpath.com/) e-commerce platform.

Bot allows to user:
- interact with the catalog of products
- interact with his cart (add, remove products)

## Install

At least Python3.8, Git and [Poetry](https://github.com/python-poetry/poetry) should be already installed.

1. Clone the repository
```
git clone https://github.com/balancy/fish-shop-bot.git
```

2. Go inside cloned repo, install dependencies and activate the virtual environment
```
cd fish_shop_bot
poetry install
poetry shell
```

3. Rename `.env.example` to `.env` and define environment variables

- `CLIENT_ID` - your [elasticpath](https://www.elasticpath.com/) client id
- `TG_BOT_TOKEN` - token of your telegram fish shop bot
- `LOGS_BOT_TOKEN` - token of your telegram logs bot
- `TG_USER_CHAT_ID` - id of your telegram user chat
