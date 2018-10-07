def run(function_invoker, port):

    from flask import Flask, request

    app = Flask("app")

    @app.route("/", methods=['POST'])
    def invoke():
        arg = request.data.decode("utf-8")

        return next(function_invoker.invoke([arg]))

    app.run(port=port)