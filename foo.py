from fabric.api import run, env, put
from fabric.network import disconnect_all
import io
import os.environ

def main(user, host, password_env_var):
    env.host_string = '{user}@{host}'.format(user=user, host=host)
    env.password = os.environ[password_env_var]

    f = io.StringIO('''
    import this
    '''.strip())
    put(f, '~/foobar.py')
    run('python foobar.py')
    disconnect_all()

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(user)
    parser.add_argument(host)
    parser.add_argument(password_env_var)
    args = parser.parse_args()

    main(**vars(args))
