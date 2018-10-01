def run(func, port):

    from flask import Flask, request

    app = Flask("app")

    @app.route("/", methods=['POST', 'GET'])
    def hello():
        arg = request.data.decode("utf-8")
        return func(arg)

    app.run(port=port)