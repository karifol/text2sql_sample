# 台風データ Text2SQL サンプル

Claude Sonnet 4.5を使用して、自然言語で台風データを検索できるText2SQLアプリケーションです。

## 機能

- ウェザーニュースの台風データベースから1951年〜2025年の台風データをスクレイピング
- SQLiteデータベースにデータを保存
- Claude Sonnet 4.5を使った自然言語からSQLへの変換
- Streamlitによる使いやすいWebインターフェース
- 検索結果のCSVダウンロード機能

## 必要な環境

- Python 3.12以上
- AWS アカウント（Bedrock経由でClaude Sonnet 4.5を使用）
- AWS認証情報（AWS_ACCESS_KEY_ID、AWS_SECRET_ACCESS_KEY）

## セットアップ

### 1. リポジトリのクローン

```bash
cd text2sql_sample
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. AWS認証情報の設定

AWS認証情報を設定します：

```bash
export AWS_ACCESS_KEY_ID="your-access-key-id"
export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
export AWS_REGION="us-east-1"  # Bedrockが利用可能なリージョン
```

または、AWS CLIで設定：

```bash
aws configure
```

**重要**: AWS BedrockでClaude Sonnet 4.5を使用するには、対象リージョンでBedrockのモデルアクセスを有効にする必要があります。
AWS Bedrockコンソールで「Model access」から「anthropic.claude-sonnet-4-5-v2:0」を有効化してください。

### 4. 台風データのスクレイピング

```bash
python scrape_typhoon_data.py
```

このスクリプトは1951年〜2025年の台風データを収集し、`typhoon.db`というSQLiteデータベースに保存します。
処理には数分かかる場合があります。

## 使用方法

### Streamlitアプリの起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

### 質問例

- 2024年の台風を全て表示
- 2020年から2025年までの台風の数を年ごとに集計
- 台風の英語名に'HAIYAN'が含まれるものを検索
- 1951年以降で最も台風が多かった年トップ5
- 8月に発生した台風の数を数える

## データベーススキーマ

```sql
CREATE TABLE typhoons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER NOT NULL,
    number INTEGER NOT NULL,
    japanese_name TEXT,
    english_name TEXT,
    start_date TEXT,
    end_date TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
)
```

### カラム説明

- `id`: 主キー
- `year`: 台風が発生した年
- `number`: その年の台風番号
- `japanese_name`: 台風の日本語名
- `english_name`: 台風の英語名
- `start_date`: 台風の発生日時（YYYY/MM/DD HH:MM形式）
- `end_date`: 台風の消滅日時（YYYY/MM/DD HH:MM形式）
- `created_at`: レコード作成日時

## ファイル構成

```
text2sql_sample/
├── app.py                    # Streamlitアプリケーション
├── scrape_typhoon_data.py    # スクレイピングスクリプト
├── requirements.txt          # 依存パッケージ
├── README.md                 # このファイル
├── 要件.txt                  # プロジェクト要件
└── typhoon.db               # SQLiteデータベース（生成後）
```

## 技術スタック

- **UI**: Streamlit
- **AI**: AWS Bedrock + Claude Sonnet 4.5
- **Database**: SQLite
- **Web Scraping**: BeautifulSoup4, Requests
- **Language**: Python 3.12

## 注意事項

- スクレイピングは対象サイトの利用規約を遵守してください
- AWS認証情報は安全に管理してください
- BedrockのClaude利用には料金が発生します
- サーバーに負荷をかけないよう、適切な間隔でリクエストしています（1秒間隔）

## ライセンス

MIT License
