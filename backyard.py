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


# menu.pyの1,2の処理
class statusClass():

    def __init__(self, query):
        # 初期設定
        self._num = 'num'
        self.query = query
        self.df = None

        self._user = 'user'
        self._passwd = 'passwd'
        self._host = 'host'
        self._db = 'db'
        self._charset = 'charset'

    # pandasのデータフレームに読み込み
    def status(self):
        with MySQLdb.connect(user=self._user, passwd=self._passwd, host=self._host, db=self._db, charset=self._charset) as conn:
            self.df = pd.read_sql(self.query, conn)
        return self.df

    # statusで読み込んだものを加工,表示する処理
    def printdf(self, *args):
        print(tabulate(self.df, headers=[self._num, *args], tablefmt='fancy_grid'))


# menu.pyの3,4,5の共通処理をまとめたクラス
class nfcSQLClass():

    def __init__(self):
        self.idm = None
        self.idmCheckList = []
        self.editList = []
        self.dict = {}

        self.user = None
        self.passwd = None
        self.host = None
        self.db = None
        self.charset = None

    # 接続するデータベースの設定
    def configSQL(self, user, passwd, host, db, charset):
        self.user = user
        self.passwd = passwd
        self.host = host
        self.db = db
        self.charset = charset
        return self.user, self.passwd, self.host, self.db, self.charset

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

    # nfcの本命の処理
    def nfcRead(self, tag):
        # nfcタグがtype3タグの時に読み取り,idmだけを読み取る
        if isinstance(tag, nfc.tag.tt3.Type3Tag):
            try:
                # idmの加工
                block_idm = binascii.hexlify(tag.idm)
                # idmのデコード処理
                self.idm = block_idm.decode('shift-jis')

                print('読み込みが完了しました。学生証を離してください')
                return self.idm
            except Exception as e:
                print("error: %s" % e)
                return

    # 開発者用,中身を見て取り出したい部分のデコードを考える際に利用していただければ
    def nfcReadDunp(self, tag):
        if isinstance(tag, nfc.tag.tt3.Type3Tag):
            try:
                print(('\n  '.join(tag.dump())))
                print('読み込みが完了しました。')
                return
            except Exception as e:
                print("error: %s" % e)
                return

    # テーブルの指定をして,nfcReadで読み取ったidmをself.idmCheckListに格納する
    def idmSQL(self, table):
        # SQL接続処理
        with MySQLdb.connect(user=self.user, passwd=self.passwd, host=self.host, db=self.db, charset=self.charset) as conn:
            with conn.cursor() as cur:
                # nfcリーダから取得したidmと同じデータをsqlから取得
                sql = "select idm from {} where idm='{}'".format(table, self.idm)
                cur.execute(sql)
                # データ取得
                idmList = cur.fetchall()
        # 取得したデータをリストにして加工
        for i in range(len(idmList)):
            self.idmCheckList += idmList[i]
        return self.idmCheckList

    # idmが重複登録されているかの確認用(基本的にはidmSQLとセットで使用)
    def idmCheckerT(self, errormsg):
        if self.idm in self.idmCheckList:
            raise ValueError('Error:'+errormsg)
        else:
            pass

    # 上の処理の逆ver.登録されていなければエラーを出力
    def idmCheckerF(self, errormsg):
        if self.idm in self.idmCheckList:
            pass
        else:
            raise ValueError('Error:' + errormsg)

    # データの更新処理,テーブルと列,値の指定
    def updateSQL(self, table, columns, *values):
        with MySQLdb.connect(user=self.user, passwd=self.passwd, host=self.host, db=self.db, charset=self.charset) as conn:
            with conn.cursor() as cur:
                sql = 'UPDATE {} SET {} = {}'.format(table, columns, *values)
                cur.execute(sql)
                # 更新,追加処理の際はcommit()を忘れないように
                conn.commit()
        return

    # データの追加処理,更新処理とほぼ同様
    def insertSQL(self, table, columns, *values):
        with MySQLdb.connect(user=self.user, passwd=self.passwd, host=self.host, db=self.db, charset=self.charset) as conn:
            with conn.cursor() as cur:
                sql = "INSERT INTO {}({}) VALUES{}".format(table, columns, values)
                cur.execute(sql)
                conn.commit()
        return

    # 読み取ったidmの取得(別の処理に応用される等幅広く利用どうぞ)
    def getidm(self):
        return self.idm

    # idm以外の情報(学籍番号,名前など)をeditListに格納するようにしているので,そちらのデータ活用用
    def geteditList(self):
        return self.editList

    # Listのデータを辞書に加工する処理,登録処理の表示が楽なので採用してます
    def editdict(self, valueList, *key):
        keyList = []
        keyList += key
        for i in range(len(valueList)):
            self.dict[keyList[i]] = valueList[i]
        return self.dict

    # デコレーター(本当はinsertSQL,updateSQLに使った方がいいんだろうけど汎用性高めるためにあえてしてないです)
    # 形は複雑ですが内容自体はyもしくはYで登録
    # nもしくはN,未入力で登録しませんよ、ってやつです。挙動は実際に動かして確かめる。デコレーターについて調べる等してもらえると
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


# 学生情報登録のみに必要な処理
class resisterStudentClass(nfcSQLClass):

    def __init__(self):
        super().__init__()
        self.nfcList = []
        self.dateYear = datetime.datetime.now().year+1
        # --ここの部分は取り出したいデータの格納されている部分に対して,値を変更してください---
        self.service_code = 0x300B
        self.rangeNum = 4
        # ----------------------------------------------------------------------

    # 学生情報も読み取るためnfcRead(86行目からのもの)を若干変更している。
    def nfcRead(self, tag):
        if isinstance(tag, nfc.tag.tt3.Type3Tag):
            try:
                # 取り出す箇所のサービス番号,属性の取得
                service_list = nfc.tag.tt3.ServiceCode(self.service_code >> 6, self.service_code & 0x3f)
                # ***ここの部分は取り出したいデータの格納されている部分に対して,値を変更してください***
                # カードに格納されているデータの指定
                for i in range(self.rangeNum):
                    self.nfcList.append(nfc.tag.tt3.BlockCode(i, service=0))
                # 指定したデータの取り出し。block_rawに格納
                block_raw = tag.read_without_encryption([service_list], [*self.nfcList])
                # 格納したデータの加工,カードによって異なる場合があるため、ダンプデータを確認していただけると
                self.editnfcList(block_raw)
                # ************************************************************************
                block_idm = binascii.hexlify(tag.idm)
                self.idm = block_idm.decode('shift-jis')

                print('読み込みが完了しました。学生証を離してください')
                return
            except Exception as e:
                print("error: %s" % e)
        else:
            print("error: tag isn't Type3Tag")

    # 格納したデータの加工処理(227行目のもの)、学籍番号,学年,氏名を取り出している。
    # editListに格納
    def editnfcList(self, list):
        school_num = list[0:7].decode('shift-jis')
        year = list[56:60].decode('shift-jis')
        school_y = self.dateYear-int(year)
        name = list[26:36].decode('shift-jis')
        self.editList += [school_num, school_y, name]
        return self.editList


# menu.pyの備品登録に必要な処理
class resisterItemClass(nfcSQLClass):
    def __init__(self):
        super().__init__()

    # 備品名を決定するための処理
    # 入力失敗が5回目になるとエラーを出力し、メニューに戻るようにしている
    # 入力に成功するとeditListに格納
    def editListInput(self):
        inputitem = input('備品名:')
        for i in range(5):
            if i == 3:
                print('次未入力の場合、メニューに戻ります')
                inputitem = input('備品名:')
            elif i == 4:
                raise ValueError('未入力のため、メニューに戻ります')
                return
            elif inputitem == '':
                print('Error:未入力です。')
                inputitem = input('備品名:')
            elif inputitem != '':
                self.editList.append(inputitem)
                return self.editList


# menu.pyの学年変更に必要な処理
class changeSchoolYearClass(nfcSQLClass):
    def __init__(self):
        super().__init__()
        # 院生,教授用のナンバーを設定している。
        self.schoolYearList = ['3', '4', '11', '12', '13', '14', '9999']

    # カードから読み取ったidmを元にデータベースからその人の学年を取得、editListに格納
    def schoolYearSQL(self):
        with MySQLdb.connect(user=self.user, passwd=self.passwd, host=self.host, db=self.db, charset=self.charset) as conn:
            with conn.cursor() as cur:
                sql = "select 学年 from 学生情報 where idm='{}'".format(self.idm)
                cur.execute(sql)
                idmList = cur.fetchall()
        for i in range(len(idmList)):
            self.editList += idmList[i]
        return
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


# 開発、拡張機能を作る際に
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
