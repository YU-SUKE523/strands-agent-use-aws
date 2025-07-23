import json
import logging
import boto3
import os
from strands import Agent
from strands.models import BedrockModel
from strands_tools import use_aws, http_request, current_time
from typing import Dict, Any

# ログ設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

model_id = os.environ["MODEL_ID"]
region = os.environ["BEDROCK_REGION"]

# Bedrockモデルの初期化
session = boto3.Session(region_name=region)
bedrock_model = BedrockModel(
    model_id=model_id,
    boto_session=session
)

# AWSリソース専門エージェントのシステムプロンプト
AWS_SYSTEM_PROMPT = """
あなたは経験豊富なAWSクラウドアーキテクトです。
以下のガイドラインに従ってAWSリソースに関する質問に答えてください：

1. use_awsツールを使用してAWSリソースの情報を取得し、正確な情報を提供する
2. セキュリティ、コスト効率、ベストプラクティスの観点からアドバイスする
3. 回答は分かりやすく、具体的で実用的な内容にする
4. 必要に応じて複数のAWSサービスを調査して包括的な回答を提供する
5. エラーが発生した場合は、可能な解決策も提案する
"""

def lambda_handler(event: Dict[str, Any], context) -> Dict[str, Any]:
    """
    AWSリソースに関する質問に答えるLambda関数
    
    Args:
        event: 入力イベント（'prompt'キーでユーザーの質問を受け取る）
        context: Lambda実行コンテキスト
    
    Returns:
        Dict[str, Any]: レスポンス（statusCode, body含む）
    """
    try:
        # 入力イベントからプロンプトを取得
        user_prompt = event.get('prompt')
        if not user_prompt:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'application/json; charset=utf-8'},
                'body': json.dumps({
                    'error': 'promptパラメータが必要です。',
                    'example': '{"prompt": "S3バケット一覧を取得してください"}'
                }, ensure_ascii=False)
            }
        
        # AWSリソース専門エージェントを作成
        aws_agent = Agent(
            tools=[use_aws, http_request, current_time],
            model=bedrock_model,
            system_prompt=AWS_SYSTEM_PROMPT    
        )
        
        logger.info(f"Processing user prompt: {user_prompt}")
        
        # エージェントを実行
        response = aws_agent(user_prompt)
        
        logger.info(f"Agent response generated successfully")
        
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json; charset=utf-8'},
            'body': json.dumps({
                'prompt': user_prompt,
                'response': str(response),
                'request_id': context.aws_request_id if context else None
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json; charset=utf-8'},
            'body': json.dumps({
                'error': f'処理中にエラーが発生しました: {str(e)}',
                'request_id': context.aws_request_id if context else None
            }, ensure_ascii=False)
        }