import os

from werkzeug import run_simple


class Node(object):
    def __init__(self, pattern="", part="", children=None, is_wild=False):
        self.pattern = pattern
        self.part = part
        self.children = children if children else []
        self.is_wild = is_wild

    def match_child(self, part):
        """第一个匹配成功的节点，用于插入"""
        for child in self.children:
            if child.part == part or child.is_wild:
                return child
        return None

    def match_children(self, part):
        nodes = []
        for child in self.children:
            if child.part == part or child.is_wild:
                nodes.append(child)
        return nodes

    def insert(self, pattern, parts, height):
        if len(parts) == height:
            self.pattern = pattern
            return
        part = parts[height]
        child = self.match_child(part)
        if not child:
            child = Node(part=part, is_wild=(part[0] == ":") or (part == "*"))
            self.children.append(child)
        child.insert(pattern, parts, height + 1)

    def search(self, parts, height):
        if len(parts) == height or self.part.startswith("*"):
            if self.pattern == "":
                return None
            return self
        part = parts[height]
        children = self.match_children(part)
        for child in children:
            result = child.search(parts, height + 1)
            if result:
                return result
        return None


class Route(object):
    roots = dict()
    handlers = dict()

    def parse_pattern(self, pattern):
        parts = []
        vs = pattern.split("/")
        for item in vs:
            if item != "":
                parts.append(item)
                if item[0] == "*":
                    break
        return parts

    def add_route(self, method, pattern, handler):
        parts = self.parse_pattern(pattern)
        key = method + "-" + pattern
        node = self.roots.get(method, None)
        if not node:
            self.roots[method] = Node()
        self.roots[method].insert(pattern, parts, 0)
        self.handlers[key] = handler

    def get_route(self, method, path):
        search_parts = self.parse_pattern(path)
        params = dict()
        root = self.roots.get(method, None)
        if not root:
            return None, None
        node = root.search(search_parts, 0)
        if node:
            parts = self.parse_pattern(node.pattern)
            for index, part in enumerate(parts):
                if part[0] == ":":
                    params[part[1:]] = search_parts[index]
                if part[0] == "*" and len(parts) > 1:
                    params[part[1:]] = "/".join(search_parts[index:])
                    break
            return node, params
        return None, None


def sayhello(params):
    print(os.getpid())
    print(f'hello:{params.get("name")}'.encode('utf-8'))
    return f'hello:{params.get("name")}'.encode('utf-8')


class RouterGroup(object):
    def __init__(self, prefix="", parent=None, engine=None):
        self.prefix = prefix
        self.middlewares = []
        self.parent = parent
        self.engine = engine

    def group(self, prefix):
        engine = self.engine if self.engine else self
        new_group = RouterGroup(self.prefix + prefix, self, engine)
        engine.groups.append(new_group)
        return new_group

    def add_route(self, method, comp, handler):
        pattern = self.prefix + comp
        print(f"Route {method} - {pattern}")
        if self.engine:
            self.engine.route.add_route(method, pattern, handler)
        else:
            self.route.add_route(method, pattern, handler)

    def get(self, pattern, handler):
        self.add_route("GET", pattern, handler)

    def post(self, pattern, handler):
        self.add_route("POST", pattern, handler)


class Engine(RouterGroup):
    route = Route()
    groups = []

    def __call__(self, env, start_response):

        path = env.get("PATH_INFO")
        method = env.get("REQUEST_METHOD")

        node, params = self.route.get_route(method, path)
        if node:
            handler = self.route.handlers.get(f"{method}-{node.pattern}")
            resp = handler(params)
        else:
            resp = "没有匹配到相关路由".encode('utf-8')
        start_response('200 OK', [('Content-Type', 'text/html;charset=utf-8')])
        print(start_response, type(start_response))
        return [resp]

    def run_http(self):
        try:
            run_simple("127.0.0.1", 8080, self)
        finally:
            # reset the first request information if the development server
            # reset normally.  This makes it possible to restart the server
            # without reloader and that stuff from an interactive shell.
            print("启动成功".encode('utf-8'))


if __name__ == '__main__':
    py_gee = Engine()
    py_gee.get("/hello/:name/haha", sayhello)
    v2 = py_gee.group("/v1")
    v2.get("/hello/:name/haha", sayhello)
    py_gee.run_http()
