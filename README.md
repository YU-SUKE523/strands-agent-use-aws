# Strands Agents on AWS Lambda

このプロジェクトは、Strands SDK を利用したエージェントアプリケーションを AWS Lambda 上で実行するためのサンプルです。
AWS SAM (Serverless Application Model) を使用して、Lambda関数と必要なIAMロールをデプロイします。

## 前提条件

デプロイには以下のツールとリソースが必要です。CloudShellには以下のツールがプリインストールされています。

### 必要なツール
*   AWS CLI
*   AWS SAM CLI
*   Docker
*   Git

### 必要なAWSリソース
*   **S3バケット** - Lambdaレイヤーのアップロード用
  - レイヤーのZIPファイルを保存するためのS3バケットが必要です
  - バケット名は手順内の `<YOUR_S3_BUCKET>` 部分で指定します

## デプロイ手順

### 1. リポジトリのクローン

まず、このリポジトリをクローンします。

```bash
git clone <repository_url>
cd strands-agents-use-aws
```

### 2. Lambdaレイヤーの作成

`strands` SDK を含む Lambda レイヤーを作成します。

1.  **Dockerイメージのビルド**
    Dockerfile を使用して、レイヤーの中身を作成するためのDockerイメージをビルドします。

    ```bash
    docker build -t strands-agent .
    ```

2.  **レイヤーのZIPファイル作成**
    ビルドしたイメージを実行し、`strands-layer.zip` という名前のZIPファイルを作成します。

    ```bash
    docker run -v "$(pwd)":/work strands-agent
    ```
    実行後、カレントディレクトリに `strands-layer.zip` が作成されていることを確認してください。

### 3. レイヤーのアップロードと公開

作成したZIPファイルを使ってLambdaレイヤーを公開します。

1.  **S3バケットへのアップロード**
    `strands-layer.zip` をS3バケットにアップロードします。`<YOUR_S3_BUCKET>` はご自身のS3バケット名に置き換えてください。

    ```bash
    aws s3 cp strands-layer.zip s3://<YOUR_S3_BUCKET>/strands-layer.zip
    ```

2.  **Lambdaレイヤーの公開**
    S3にアップロードしたZIPファイルからLambdaレイヤーを作成します。

    ```bash
    aws lambda publish-layer-version \
        --layer-name strands-layer \
        --description "Layer for Strands SDK" \
        --content S3Bucket=<YOUR_S3_BUCKET>,S3Key=strands-layer.zip \
        --compatible-runtimes python3.11 python3.12
    ```
    コマンドが成功すると、`LayerVersionArn` が出力されます。このARNを次のステップで使用します。

### 4. SAMテンプレートの更新

`template.yaml` ファイルを編集し、作成したLambdaレイヤーを関数にアタッチします。

1.  `template.yaml` を開き、`StrandsAgentsUseAwsFunction` リソースの `Properties` に `Layers` セクションを追加します。
2.  `Layers` に、前のステップで取得した `LayerVersionArn` を追加します。

    ```yaml
    Resources:
      StrandsAgentsUseAwsFunction:
        Type: AWS::Serverless::Function
        Properties:
          # ... 既存のプロパティ ...
          Layers:
            - <LayerVersionArn をここに貼り付け>
    ```

### 5. SAMアプリケーションのデプロイ

SAMを使用してアプリケーションをビルドし、デプロイします。

0.  **Python 3.12のインストール（CloudShellの場合）**
    CloudShellではPython 3.12がデフォルトでインストールされていないため、手動でインストールします。

    ```bash
    # Python 3.12をインストール
    sudo dnf install python3.12 python3.12-devel python3.12-pip -y
    
    # インストール確認
    python3.12 --version
    ```

1.  **Lambda関数ビルド用のrequirements.txtを準備**
    レイヤーとの重複を避けるため、requirements.txtを一時的にリネームします。

    ```bash
    # レイヤー用のrequirements.txtをバックアップ
    mv requirements.txt layer-requirements.txt
    
    # Lambda関数には最小限の依存関係のみ（boto3は Lambda環境に含まれているため不要）
    echo "# No additional dependencies needed - using layer" > requirements.txt
    ```

2.  **SAMビルド**
    インストールしたPython 3.12を指定してビルドします。

    ```bash
    # Python 3.12を使用してビルド
    PYTHON_PATH=$(which python3.12) sam build
    
    # ビルド後のサイズを確認
    du -sh .aws-sam/build/StrandsAgentsUseAwsFunction/
    ```

3.  **SAMデプロイ**
    対話形式でデプロイを進めます。スタック名などを指定してください。

    ```bash
    sam deploy --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM --guided
    ```

4.  **デプロイ後の後片付け**
    デプロイ完了後、requirements.txtを元に戻します。

    ```bash
    # 元のrequirements.txtに戻す
    mv layer-requirements.txt requirements.txt
    ```

以上でデプロイは完了です。
