# FISH SHOP BOT

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

- `CLIENT_ID`   - your [elasticpath](https://www.elasticpath.com/) client id
