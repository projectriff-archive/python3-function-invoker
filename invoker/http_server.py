from bottle import Bottle, request


def run(function_invoker, port):
    app = Bottle()

    @app.post('/')
    def invoke():
        arg = parse_function_arguments()

        result = function_invoker.invoke([arg])

        return next(result)

    app.run(host="0.0.0.0", port=port)


def parse_function_arguments():
    if request.json is not None:
        return request.json
    else:
        return request.body.read().decode()
