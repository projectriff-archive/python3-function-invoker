from bottle import Bottle, request


def run(function_invoker, port):
    app = Bottle()

    @app.post('/')
    def invoke():
        arg = request.body.read().decode()

        result = function_invoker.invoke([arg])

        return next(result)

    app.run(host="0.0.0.0", port=port)
