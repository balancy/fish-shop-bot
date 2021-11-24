from environs import Env


env = Env()
env.read_env()


CLIENT_ID = env.str('CLIENT_ID')
