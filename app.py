import streamlit as st
import sqlite3
import pandas as pd
import boto3
import json
import os

# Page configuration
st.set_page_config(
    page_title="台風データ Text2SQL",
    page_icon="🌪️",
    layout="wide"
)

st.title("🌪️ 台風データ Text2SQL")
st.markdown("自然言語で台風データを検索できます")

# Database connection
@st.cache_resource
def get_database_schema():
    """Get database schema information"""
    conn = sqlite3.connect('typhoon.db')
    cursor = conn.cursor()

    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='typhoons'")
    schema = cursor.fetchone()

    cursor.execute("SELECT COUNT(*) FROM typhoons")
    count = cursor.fetchone()[0]

    conn.close()

    return schema[0] if schema else None, count

def execute_sql_query(query):
    """Execute SQL query and return results as DataFrame"""
    try:
        conn = sqlite3.connect('typhoon.db')
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df, None
    except Exception as e:
        return None, str(e)

def generate_sql_from_text(user_question, schema):
    """Use Claude Sonnet 4.5 via AWS Bedrock to convert text to SQL"""

    # Check AWS credentials
    aws_region = os.environ.get("AWS_REGION", "us-east-1")

    try:
        # Initialize Bedrock Runtime client
        bedrock_runtime = boto3.client(
            service_name='bedrock-runtime',
            region_name=aws_region
        )
    except Exception as e:
        return None, f"AWS認証エラー: {str(e)}\nAWS認証情報を設定してください"

    prompt = f"""データベーススキーマ:
{schema}

テーブル説明:
- typhoons: 台風の情報を格納するテーブル
  - id: 主キー
  - year: 台風が発生した年
  - number: その年の台風番号
  - japanese_name: 台風の日本語名
  - english_name: 台風の英語名
  - start_date: 台風の発生日時 (YYYY/MM/DD HH:MM形式)
  - end_date: 台風の消滅日時 (YYYY/MM/DD HH:MM形式)

ユーザーの質問: {user_question}

上記の質問に答えるためのSQLクエリを生成してください。
SQLクエリのみを出力し、説明や```sqlなどのマークダウンは含めないでください。
SELECT文のみを生成してください。"""

    # Prepare request body for Bedrock
    request_body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    try:
        # Invoke Claude Sonnet 4.5 via Bedrock
        response = bedrock_runtime.invoke_model(
            modelId="global.anthropic.claude-sonnet-4-20250514-v1:0",
            body=json.dumps(request_body)
        )

        # Parse response
        response_body = json.loads(response['body'].read())
        sql_query = response_body['content'][0]['text'].strip()

        # Remove markdown code blocks if present
        if sql_query.startswith("```"):
            lines = sql_query.split("\n")
            sql_query = "\n".join(lines[1:-1]) if len(lines) > 2 else sql_query
            sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

        return sql_query, None

    except Exception as e:
        return None, str(e)

# Main app
schema, record_count = get_database_schema()

if schema:
    st.sidebar.success(f"✅ データベース接続成功")
    st.sidebar.info(f"📊 総台風数: {record_count:,}件")

    with st.sidebar.expander("データベーススキーマ"):
        st.code(schema, language="sql")

    # Sample questions
    st.sidebar.markdown("### 質問例")
    sample_questions = [
        "2024年の台風を全て表示",
        "2020年から2025年までの台風の数を年ごとに集計",
        "台風の英語名に'HAIYAN'が含まれるものを検索",
        "1951年以降で最も台風が多かった年トップ5",
        "8月に発生した台風の数を数える"
    ]

    for q in sample_questions:
        if st.sidebar.button(q, key=f"sample_{q}"):
            st.session_state['user_question'] = q

    # User input
    user_question = st.text_input(
        "質問を入力してください:",
        value=st.session_state.get('user_question', ''),
        placeholder="例: 2024年の台風を全て表示"
    )

    if st.button("🔍 検索", type="primary"):
        if user_question:
            with st.spinner("SQLクエリを生成中..."):
                sql_query, error = generate_sql_from_text(user_question, schema)

            if error:
                st.error(f"❌ エラー: {error}")
            elif sql_query:
                st.subheader("生成されたSQLクエリ")
                st.code(sql_query, language="sql")

                with st.spinner("クエリを実行中..."):
                    df, exec_error = execute_sql_query(sql_query)

                if exec_error:
                    st.error(f"❌ クエリ実行エラー: {exec_error}")
                elif df is not None:
                    st.subheader("検索結果")

                    if len(df) > 0:
                        st.success(f"✅ {len(df)}件のレコードが見つかりました")
                        st.dataframe(df, use_container_width=True)

                        # Download button
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 CSVダウンロード",
                            data=csv,
                            file_name="typhoon_query_results.csv",
                            mime="text/csv"
                        )
                    else:
                        st.warning("該当するデータが見つかりませんでした")
        else:
            st.warning("質問を入力してください")

else:
    st.error("❌ データベースが見つかりません。先に `python scrape_typhoon_data.py` を実行してください。")

# Footer
st.markdown("---")
st.markdown("Powered by AWS Bedrock (Claude Sonnet 4.5) and Streamlit")
