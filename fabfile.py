from fabric.api import local, run, env, task

@task
def do_a_thing():
    local("ls ~/")
    run("ls ~/")
