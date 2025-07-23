FROM public.ecr.aws/lambda/python:3.12
 
WORKDIR /work
 
# システム更新と必要なパッケージのインストール
RUN dnf update && dnf install -y zip

# 必要なパッケージをインストール
COPY requirements.txt .
RUN pip install -r requirements.txt -t /python/

 
# boto3など、不要なパッケージを削除
RUN rm -rf /python/boto3* \
           /python/botocore* \
           /python/s3transfer* \
           /python/docutils* \
           /python/jmespath* \
           /python/chardet* \
           /python/six* \
           /python/python_dateutil*
 
ENTRYPOINT [""]
CMD zip -r strands-layer.zip /python/
