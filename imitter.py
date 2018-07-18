import os, re, gc, sys, time, MeCab, random, tweepy, datetime
from tweepy.error import TweepError
from gensim import models

debug_mode = False

#形態素解析をする対象となるアカウント
target_id = ''

#形態素解析した結果を書き出すファイル名
folder = 'tweet/' + target_id + '/'
today = datetime.datetime.now().strftime('%Y%m%d')
filename = 'MeCab-' + target_id + '-' + today + '.csv'
path = folder + filename

#macabで使用するシステム辞書のパス
sysdic = '/usr/local/lib/mecab/dic/mecab-ipadic-neologd'

#mecabで使用するユーザー辞書のパス
userdic = 'userdic/user.dic'

#Doc2Vecで学習させたモデルファイルのパス
model_file = 'model/twitter.model'

#特定ツイートの除外(URL付きツイート、引用RT, swarn)
exclusion_list = ['https', 'http', 'RT', '(@', 'w/', '#', '|']

#おみくじ
fortune_list = ['大吉', '中吉', '小吉', '吉', '末吉', '凶']

#Twitterアクセストークン
consumer_key = os.environ.get('TWITTER_CONSUMER_KEY')
consumer_secret = os.environ.get('TWITTER_CONSUMER_SECRET')
access_token = os.environ.get('TWITTER_ACCESS_TOKEN')
access_secret = os.environ.get('TWITTER_ACCESS_SECRET')

# TwitterAPIの取得
auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_secret)
api = tweepy.API(auth, timeout = 120)

class TweetGetter:
	def __init__(self):
		self.form_class_chain = {'':{'':[]}}
		self.get_tweet(path)
		
	def get_form_class_chain(self):
		return self.form_class_chain
	
	def get_tweet(self, output_file):
		mecab = MeCab.Tagger('-d ' + sysdic + ' -u ' + userdic)
		mecab.parse('')
		output_csv_file = open(output_file, 'w', newline = '', encoding = 'utf-8')
		#ツイートの取得
		tweet_data = []
		training_data = []
		limits = 50 if debug_mode else 2000
		TL = tweepy.Cursor(api.user_timeline, screen_name = target_id, exclude_replies = True).items(limits)
		for tweet in TL:
			tweet = tweet.text.replace('\n','')
			print(tweet)
			if re.compile('(https|http|RT|@|w/)').search(tweet) == None:
				tweet_data.append([tweet])
				#形態素解析
				parsed_tweet = mecab.parse(tweet).split('\n')
				#マルコフ連鎖の構築
				self.add_chain(parsed_tweet)
				#形態素解析した結果を保存
				output_csv_file.write(mecab.parse(tweet))
		print('Done.')
		output_csv_file.close()
		
	def make_element(self, string):
		element = string.split('\t')[0]
		return str(element)
		
	def add_chain(self, form_class_list):
		for i in range(len(form_class_list)-3):
			key1 = self.make_element(form_class_list[i])		
			key2 = self.make_element(form_class_list[i+1])
			if i == len(form_class_list) - 4:
				value = 'EOS'
			else:
				value = self.make_element(form_class_list[i+2])
				
			if key1 in self.form_class_chain:
				if key2 in self.form_class_chain[key1]:
					self.form_class_chain[key1][key2].append(value)
				else:
					self.form_class_chain[key1][key2] = [value]
			else:
				self.form_class_chain[key1] = {}
				self.form_class_chain[key1][key2] = [value]

class Listener(tweepy.StreamListener):
	def __init__(self, TweetGetter):
		#親クラスのコンストラクタを呼び出す
		tweepy.StreamListener.__init__(self)
		#自分のユーザーID
		self.my_id = api.me().screen_name
		#最終ツイート日時
		self.last_tweeted_time = datetime.datetime.now()
		#モデルの読み込み
		self.model = models.doc2vec.Doc2Vec.load(model_file)
		#マルコフ連鎖
		self.form_class_chain = TweetGetter.form_class_chain
		#各種品詞が入ったリスト
		self.noun_list = []
		self.name_list = []
		self.adjuct_list = []
		#ツイートを整形して各種品詞リストに追加
		self.composition(path)

	def composition(self, input_file):
		exclusion = False

		for line in open(input_file, 'r'):
			data = line.split('	')

			if data[0] in exclusion_list:
				exclusion = True
			if exclusion:
				if len(data) == 1:
					exclusion = False
				else:
					continue

			if len(data) != 1:
				key = data[-1].split(',')
				del key[6:9]
				key = str(key)

				#各種リストに要素を追加する
				if re.compile('(?=.*名詞)(?!.*(接尾|数))').search(key) != None:
					self.noun_list.append(data[0])
				if re.compile('(?=.*(人物|人名))(?!.*接尾)').search(key) != None:
					self.name_list.append(data[0])
				if re.compile('形容詞.*基本形').search(key) != None:
					self.adjuct_list.append(data[0])

	def make_lucky_item(self):
		noun = random.choice(self.noun_list)
		name = random.choice(self.name_list)
		adjuct = random.choice(self.adjuct_list)
		tweet = random.choice([name + 'の' + noun, adjuct + noun, noun])
		return tweet
				
	def make_tweet(self, return_as_list):
		while True:
			words = []
			words.append(random.choice(list(self.form_class_chain.keys())))
			while True:
				key1 = words[-1]
				if key1 in self.form_class_chain:
					key2, value = random.choice(list(self.form_class_chain[key1].items()))
				else:
					break
				if len(value) > 0:
					value = random.choice(value)
				words.append(key2)
				if value == 'EOS':
					break
				if len(value) == 0:
					break
				words.append(value)
			if 0 < len(''.join(words)) < 50:
				if return_as_list:
					return words
				else:
					return ''.join(words)

	'''
	def on_event(self, event):
		#自動フォロー返し
		if event.event == 'follow':
			if api.me().id != source_user['id']:
				print('\nFollowed by ' + source_user['id'] + '.')
				source_user = event.source
				event._api.create_friendship(source_user['id'])
				print('Created friendship: ' + source_user['id'])
	'''

	def on_status(self, status):
		#ローカライズ
		status.created_at += datetime.timedelta(hours = 9)
		reply_id = status.in_reply_to_screen_name
		
		#返信
		if str(reply_id) == self.my_id:
			#おみくじ
			if 'おみくじ' in status.text:
				print('\nGet an Omikuji request.')
				reply_id = status.id
				fortune = '\n運勢: ' + random.choice(fortune_list)
				tweet = '@' + str(status.user.screen_name) + ' ' + fortune
				tweet = tweet + '\nラッキーアイテム: ' + self.make_lucky_item()
				api.update_status(status = tweet, in_reply_to_status_id = reply_id)
				print('Update status: ' + tweet)
			#おはなし
			else:
				print('\nGet a reply.')
				#リプライを形態素解析
				mecab = MeCab.Tagger('-d ' + sysdic+ ' -u ' + userdic)
				mecab.parse('')
				parsed_reply = mecab.parse(status.text.replace('\n','').replace(reply_id, '')).split('\n')
				reply_words = [word.split('\t')[0] for word in parsed_reply]
				#返信の候補を複数作成
				candidates_for_reply = [self.make_tweet(return_as_list = True) for _ in range(200)]
				#返信と最大の類似度を取る候補を選択
				max_similarity = 0
				max_similarity_index = 0
				for i in range(len(candidates_for_reply)):
					similarity = self.model.docvecs.similarity_unseen_docs(self.model, reply_words, candidates_for_reply[i])
					if similarity > max_similarity:
						max_similarity = similarity
						max_similarity_index = i
				print('Select: '+ str(max_similarity_index) + ', similarity: ' + str(max_similarity))
				#返信
				reply_id = status.id
				text = ''.join(candidates_for_reply[max_similarity_index])
				tweet = '@' + str(status.user.screen_name) + ' ' + text
				api.update_status(status = tweet, in_reply_to_status_id = reply_id)
				print('Update status: ' + tweet)

		#定期ツイート
		if status.created_at > self.last_tweeted_time + datetime.timedelta(minutes = 20):
			#最終ツイート時刻を更新
			self.last_tweeted_time = status.created_at
			print('\nRegularly tweet.')
			tweet = self.make_tweet(return_as_list = False)
			api.update_status(status = tweet)
			print('Update status: ' + tweet)
			return True

	def on_error(self, status_code):
		print('\nGot an error with status code: ' + str(status_code))
		return True

	def on_timeout(self):
		print('\nTimeout...')
		return True

def main():
	#target_idが設定されているかの確認
	if len(target_id) == 0:
		print('target_id is not set.')
		sys.exit()
	#フォルダの作成
	if target_id not in os.listdir('tweet'):
		os.mkdir('tweet/' + target_id)
	#ツイートの取得
	getter = TweetGetter()
	listener = Listener(getter)
	stream = tweepy.Stream(auth, listener)
	
	while True:
		try:
			stream.userstream()
		except TweepError:
			print('\nAn error occurred. It resumes after 60 seconds.')
			time.sleep(60)
			print('Restart user stream.')
		finally:
			time.sleep(60)

if __name__ == '__main__':
	main()
