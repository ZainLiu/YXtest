from werkzeug.serving import run_simple


def hello(host, port, app):
    try:
        run_simple(host, port, app)
    finally:
        # reset the first request information if the development server
        # reset normally.  This makes it possible to restart the server
        # without reloader and that stuff from an interactive shell.
        print("启动成功")


def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    print(env)
    return [b"Hello World"]


hello("127.0.0.1", 8080, application)