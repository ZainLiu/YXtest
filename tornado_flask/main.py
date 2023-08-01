import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.wsgi import WSGIContainer
from flask import Flask

# 创建Flask应用程序
app = Flask(__name__)

# 定义Flask路由和处理程序
@app.route('/')
def index():
    return 'Hello, World!'

@app.route('/flask')
def index3():
    return 'Hello, flask!'

# 创建Tornado处理程序
class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, Tornado!")

# 创建Tornado应用程序
def make_app():
    tornado_app = tornado.web.Application([
        (r'/tornado', MainHandler),
        (r'.*', tornado.web.FallbackHandler, dict(fallback=WSGIContainer(app)))
    ])
    return tornado_app

if __name__ == '__main__':
    # 创建Tornado应用程序对象
    tornado_app = make_app()

    # 使用Tornado的HTTP服务器启动应用程序
    http_server = tornado.httpserver.HTTPServer(tornado_app)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.current().start()
