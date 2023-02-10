class Hello:
    def __init__(self):
        self.init_data()

    def init_data(self):
        Hello.app = [1, 2, 3]

h = Hello()
print(h.app, id(h.app))
print(Hello.app, id(Hello.app))