FROM python:3.6-slim as build_proto
RUN  apt-get update \
  && apt-get install -y wget \
  && rm -rf /var/lib/apt/lists/*

ADD  grpcio-tools.txt /
RUN  ["pip","install","-r","grpcio-tools.txt"]

RUN ["wget", "https://raw.githubusercontent.com/projectriff/function-proto/master/function.proto", "-P", "proto"]

# Generate the protobufs
RUN ["mkdir", "./grpc_modules"]
RUN ["python", "-m", "grpc_tools.protoc","-I./proto","--python_out=./grpc_modules", "--grpc_python_out=./grpc_modules","./proto/function.proto"]

FROM python:3.6-slim
COPY invoker/* /
COPY --from=build_proto ./grpc_modules .
RUN  ["pip","install","-r","requirements.txt"]
ENTRYPOINT ["python","./function_invoker.py"]


