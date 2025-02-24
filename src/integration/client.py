from purse.http.clients.pure import SimpleHttpClient


class SimpleClient(SimpleHttpClient):
    def do_test_exception(self):
        return self.get("/index")
