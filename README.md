# Imitter
imitation + twitter = Imitter  
特定の人物のツイートを真似て会話するTwitterBot  

## Description
Imitterは指定されたアカウントの口調を真似して定時ツイートするbotサービスです  
ユーザはraspberry piなどを使うことで簡単にこのサービスを利用することができます  
またImitterはリプライに対し自動返信する機能を持っています  
リプライを受け取ると、Imitterはリプライを形態素解析し、返信の候補を200個生成します  
その後、Imitterはdoc2vecを使って候補の中からリプライと1番マッチするような返信を選び、リプライ元と会話するような形で返信を行います  
おまけとしてImitterにはおみくじ機能が搭載されています  
「おみくじ」と書かれたリプライを受け取ると、運勢とラッキーアイテムを占い、返信します  

## Demo
target_idとして安倍総理([@AbeShinzo](https://twitter.com/AbeShinzo))を指定した場合  
![Imitter返信1](demo/demo_img_abeshinzo.png)  

target_idとしてダウンタウン松本人志([@matsu_bouzu](https://twitter.com/matsu_bouzu))を指定した場合  
![Imitter返信2](demo/demo_img_matsu_bouzu.png)

target_idを@matsu_bouzuにしておみくじを行なった場合  
![Imitterおみくじ](demo/demo_img_omikuji.png)

## Usage
1. Imitterがツイートするためのtwitterアカウントを作成してください。


2. <https://apps.twitter.com>に1で作ったアカウントでログインして、4つのAPIキーを取得してください。取得方法は<http://phiary.me/twitter-api-key-get-how-to>を参考にしてください。


3. 環境変数を設定してください。設定する環境変数は以下の通りです。  

    - TWITTER_CONSUMER_KEY
    - TWITTER_CONSUMER_SECRET
    - TWITTER_ACCESS_TOKEN
    - TWITTER_ACCESS_SECRET
    <!--リスト終了-->
    環境変数の設定方法がわからない場合はimitter.pyに4つのAPIキーを直接入力してください。

    ```python
    #imitter.py内の以下の部分を編集してください
    consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
    consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
    access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
    access_secret = os.environ.get('TWITTER_ACCESS_SECRET')

    #上の4行を次のように変更してください。
    consumer_key = '取得したconsumer keyをここに入れる'
    consumer_secret = '取得したconsumer　secretをここに入れる'
    access_token = '取得したaccess tokenをここに入れる'
    access_secret = '取得したaccess secretをここに入れる'
    ```

4. 必要なパッケージをインストールしてください。

    ```sh
    pip install tweepy
    sudo apt install libatlas-base-dev
    sudo apt install mecab
    sudo apt install mecab-ipadic
    pip install mecab-python3
    pip install gensim
    ```

5. mecabの新語辞書(mecab-ipadic-neologd)をインストールしてください。  

    ```sh
    git clone --depth 1 https://github.com/neologd/mecab-ipadic-neologd.git
    cd mecab-ipadic-neologd
    ./bin/install-mecab-ipadic-neologd -n
    ```

6. imitter.pyの8行目に真似したいtwitterアカウントのIDを@なしで入力してください。  

    ```python
    #安倍総理のツイートを真似したい時
    target_id = 'AbeShinzo'
    ```

7. python3でimitter.pyを実行してください。

    ```sh
    python3 imitter.py
    ```
