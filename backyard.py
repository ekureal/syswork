import MySQLdb
import pandas as pd
import nfc
import binascii
import datetime
import time
import traceback
import logging
from tabulate import tabulate

# -----------------------------------ロガー生成-----------------------------------
logger = logging.getLogger('backyard')
logger.setLevel(logging.DEBUG)
# -------------------------------出力フォーマット設定-------------------------------
format = '%(asctime)s,%(message)s'
datefmt = '%Y/%m/%d %I:%M:%S'
formatter = logging.Formatter(format, datefmt)
# -------------------------------ログファイル出力設定-------------------------------
fh = logging.FileHandler('backyard_error.log')
fh.setFormatter(formatter)
logger.addHandler(fh)


# menu.pyの共通処理をまとめたクラス
class nfcSQLClass():

    def __init__(self):
        self.idm = None

        self._user = 'user'
        self._passwd = 'passwd'
        self._host = 'localhost'
        self._db = 'db'
        self._charset = 'utf8'

    # nfcの処理
    def nfcConnect(self):

        print('nfcタグ(学生証、備品タグ)をnfcリーダーにかざしてください。\n 待機中...')

        with nfc.ContactlessFrontend('usb') as clf:

            # 5秒間カードが置かれなかった場合処理が終了する(tag == None)
            after5s = lambda: time.time() - started > 5
            started = time.time()

            # タグが読み込まれた場合はself.nfcReadが実行される
            tag = clf.connect(rdwr={'on-connect': self.nfcRead}, terminate=after5s)
            if tag is None:
                raise ValueError('ICカードが置かれていません。メニューに戻ります')
                return

    def nfcRead(self, tag):
        # nfcタグがtype3タグの時に読み取り,idmだけを読み取る
        if isinstance(tag, nfc.tag.tt3.Type3Tag):
            try:
                # idmの加工
                block_idm = binascii.hexlify(tag.identifier)
                # idmのデコード処理
                self.idm = block_idm.decode('shift-jis')

                print('読み込みが完了しました。学生証を離してください')
                return self.idm
            except Exception as e:
                print("error: %s" % e)
                return

    # 読み取ったidmの取得
    def getidm(self):
        return self.idm

    def geteditList(self):
        return self.editList

    # idmが重複登録されているかの確認用
    def isResister(self, idm, SQLidm, errormsg):
        if idm == SQLidm:
            raise ValueError('Error:'+errormsg)
        else:
            pass

    # idmが重複登録されていないかの確認用
    def isNotResister(self, idm, SQLidm, errormsg):
        if idm != SQLidm:
            raise ValueError('Error:'+errormsg)
        else:
            pass

    def SQLRead(self, sql, List = []):
        # SQL接続処理
        with MySQLdb.connect(user=self._user, passwd=self._passwd, host=self._host, db=self._db, charset=self._charset) as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
                # データ取得
                a = cur.fetchall()
                for i in range(len(a)):
                    List.append(a[i])
        return List

    def SQLCommit(self, sql):
        with MySQLdb.connect(user=self._user, passwd=self._passwd, host=self._host, db=self._db, charset=self._charset) as conn:
            with conn.cursor() as cur:
                # print(sql)
                cur.execute(sql)
                # 更新,追加処理の際はcommit()を忘れないように
                conn.commit()
        return

    # Listのデータを辞書に加工する処理,登録処理の表示が楽なので採用してます
    def editdict(self, valueList, *key):
        keyList = []
        keyList += key
        for i in range(len(valueList)):
            self.dict[keyList[i]] = valueList[i]
        return self.dict

    # 入力失敗が5回目になるとエラーを出力し、メニューに戻るようにしている
    # 入力に成功するとeditListに格納
    def editListInput(self, name):
        inputitem = input(name)
        for i in range(3):
            if i == 1:
                print('次未入力の場合、メニューに戻ります')
                inputitem = input(name)
            elif i == 2:
                raise ValueError('未入力のため、メニューに戻ります')
                return
            elif inputitem == '':
                print('Error:未入力です。')
                inputitem = input(name)
            elif inputitem != '':
                self.editList.append(inputitem)
                return self.editList

    # デコレーター
    # 形は複雑ですが内容自体はyもしくはYで登録
    # nもしくはN,未入力で登録しない。挙動は実際に動かして確かめる。
    def resDecoretor(self, func):
        print('--------------------------------------------------------')
        print(str(self.dict)[1:-1])
        print('--------------------------------------------------------')
        print('以上の内容で登録します。よろしいですか？(y|n) \n(入力がない場合、メニューに戻ります)')
        keyPress = input()

        def wrapper(*args):
            if keyPress == 'Y' or keyPress == 'y':
                func(*args)
                print('正常に登録されました。メニューに戻ります')
                return
            elif keyPress == 'N' or keyPress == 'n':
                print('登録せずメニューに戻ります')
                return
            elif keyPress != 'Y' or keyPress != 'y':
                print('入力がない、無効のため登録せずメニューに戻ります')
                return
        return wrapper

    # 想定していないエラーが出た際の詳細をbackyard_error.logに出力してます。
    # コンソール上には簡単なエラー文しか表示されず、該当箇所が分かりづらいと思うので...
    def errorLog(self):
        logger.error(traceback.format_exc())
        return

# menu.pyの1,2の処理
class statusClass(nfcSQLClass):

    def __init__(self):
        super().__init__()
        self._num = 'num'
        self.df = None

    # pandasのデータフレームに読み込み
    def SQLstatus(self, sql):
        with MySQLdb.connect(user=self._user, passwd=self._passwd, host=self._host, db=self._db, charset=self._charset) as conn:
            self.df = pd.read_sql(sql, conn)
        return self.df

    # statusで読み込んだものを加工,表示する処理
    def printdf(self, *columns):
        return tabulate(self.df, headers=[self._num, *columns], tablefmt='fancy_grid')


# 学生情報登録のみに必要な処理
class resisterStudentClass(nfcSQLClass):

    def __init__(self, service_code, rangeNum):
        super().__init__()
        self.nfcList = []
        self.editList = []
        self.dict = {}
        self.dateYear = datetime.datetime.now().year+1

        self.service_code = service_code
        self.rangeNum = rangeNum
    # 学生情報読み取り
    def nfcRead(self, tag):
        if isinstance(tag, nfc.tag.tt3.Type3Tag):
            try:
                # 取り出す箇所のサービス番号,属性の取得
                service_list = nfc.tag.tt3.ServiceCode(self.service_code >> 6, self.service_code & 0x3f)

                # 指定したデータの取り出し。block_rawに格納
                for i in range(self.rangeNum):
                    self.nfcList.append(nfc.tag.tt3.BlockCode(i, service=0))
                block_raw = tag.read_without_encryption([service_list], [*self.nfcList])
                # 格納したデータの加工,カードによって異なる場合があるため、ダンプデータを確認していただけると
                self.editList  = self.editnfcList(block_raw)

                block_idm = binascii.hexlify(tag.idm)
                self.idm = block_idm.decode('shift-jis')

                print('読み込みが完了しました。学生証を離してください')
                return
            except Exception as e:
                print("error: %s" % e)
        else:
            print("error: tag isn't Type3Tag")

    # 格納したデータの加工処理、学籍番号,学年,を取り出している。editListに格納
    def editnfcList(self, rawList, editList = []):
        school_num = rawList[:7].decode('shift-jis')
        year = rawList[:2].decode('shift-jis')
        school_y = self.dateYear-int(year) - 2000
        # name = list[26:36].decode('shift-jis')
        editList += [school_num, school_y]
        return editList


# menu.pyの備品登録に必要な処理
class resisterItemClass(nfcSQLClass):
    def __init__(self):
        super().__init__()
        self.editList = []
        self.dict = {}

    def nfcRead(self, tag):
        # nfcタグがtype2タグの時に読み取り,idmだけを読み取る
        if isinstance(tag, nfc.tag.tt2.Type2Tag):
            try:
                # idmの加工
                block_idm = binascii.hexlify(tag.identifier)
                # idmのデコード処理
                self.idm = block_idm.decode('shift-jis')

                print('読み込みが完了しました。備品を離してください')
                return self.idm
            except Exception as e:
                print("error: %s" % e)
                return

# menu.pyの学年変更に必要な処理
class changeSchoolYearClass(nfcSQLClass):
    def __init__(self):
        super().__init__()
        self.editList = []
        self.dict = {}
        # 院生,教授用のナンバーを設定。
        self.schoolYearList = ['3', '4', '11', '12', '13', '14', '9999']

    # 変更したい学年を入力する処理。editListに格納
    # 無効な入力でエラーを出力し、メニューに戻る。
    def inputYear(self):
        print('変更したい学年を入力して、Enterキーを押してください')
        keyPress = input('変更後の学年：')
        if keyPress in self.schoolYearList:
            self.editList.append(keyPress)
            return
        elif keyPress not in self.schoolYearList:
            raise ValueError('無効な入力値です、メニューに戻ります')
            return


# 開発、拡張機能を作る際に使ってみてください
class developClass(nfcSQLClass):
    def __init__(self):
        super().__init__()

    def nfcConnect(self):
        print('nfcタグ(学生証、備品タグ)をnfcリーダーにかざしてください。\n 待機中...')
        with nfc.ContactlessFrontend('usb') as clf:
            after5s = lambda: time.time() - started > 5
            started = time.time()
            tag = clf.connect(rdwr={'on-connect': self.nfcReadDunp}, terminate=after5s)

            if tag is None:
                raise ValueError('ICカードが置かれていません。メニューに戻ります')
                return

    # 開発者用,中身を見て取り出したい部分のデコードを考える際に利用していただければ、タグは好きにいじって
    def nfcReadDunp(self, tag):
        if isinstance(tag, nfc.tag.tt3.Type3Tag):
            try:
                print(('\n  '.join(tag.dump())))
                print('読み込みが完了しました。')
                return
            except Exception as e:
                print("error: %s" % e)
                return
