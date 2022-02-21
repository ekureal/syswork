from pysesame3.auth import WebAPIAuth
from pysesame3.lock import CHSesame2
import binascii
import nfc
import os
import time
from time import sleep
import logging
import datetime
import MySQLdb
import sys

# ----------------------------------sesame3情報----------------------------------
# アカウントの API KEY
auth = WebAPIAuth(apikey="aDASdrwlGI1VZSORfifH82xHJxTYoPBXaOfcnl1i")
# Sesame 3 の UUID
your_key_uuid = "41E14BC8-4C5D-327A-922A-3584FDB7A214"
# 前段の手順で取得した秘密鍵の HEX 文字列
your_key_secret = "75d2cce98a5385affde4f81691e87c49"
device = CHSesame2(authenticator=auth, device_uuid=your_key_uuid, secret_key=your_key_secret)

# -----------------------------------ロガー生成-----------------------------------
logger = logging.getLogger('sesamev3')
logger.setLevel(logging.DEBUG)
# -------------------------------出力フォーマット設定-------------------------------
format = '%(asctime)s,%(message)s'
datefmt = '%Y/%m/%d %I:%M:%S'
formatter = logging.Formatter(format, datefmt)
# ---------------------------コンソール出力用 (動作確認用)---------------------------
# Handler基準にsetlevel,addHandlerで追加
# sh = logging.StreamHandler()
# sh.setFormatter(formatter)
# sh.setLevel(logging.DEBUG)
# logger.addHandler(sh)
# -------------------------------ログファイル出力設定-------------------------------
fh = logging.FileHandler('sesameLogin.log')
fh.setFormatter(formatter)
fh.setLevel(logging.DEBUG)
logger.addHandler(fh)


class MyCardReader(object):
    def __init__(self):
        self.__user = 'sample'
        self.__passwd = 'sample'
        self.__host = 'hostname'
        self.__db = 'syswork'
        self.__charset = 'utf8'
        self.idm = None
        self.checklist = []
        self.const

    @property
    def const(self):
        return self.__user, self.__passwd, self.__host, self.__db, self.__charset

# ------------------------------データベース学生情報取得-----------------------------
    def check(self, idm):
        with MySQLdb.connect(user=self.__user, passwd=self.__passwd, host=self.__host, db=self.__db, charset=self.__charset) as conn:
            with conn.cursor() as cur:
                sql = "select idm,学籍番号,学年,氏名 from 学生情報 where idm='{}'".format(idm)
                cur.execute(sql)
                idmList = cur.fetchall()
        for i in range(len(idmList)):
            self.checklist += idmList[i]
        return self.checklist
# -------------------------------学生証タッチ時の処理-------------------------------
    def on_connect(self, tag):

        # IDmのみ取得して表示
        idm = binascii.hexlify(tag.idm)
        self.idm = idm.decode('shift-jis')

        self.check(self.idm)

        # 登録されていた場合の処理
        if self.idm in self.checklist:
            # log登録
            logger.info('学籍番号:{} 学年:{} 氏名:{} が入室しました。'.format(*self.checklist[1:]))
            return
            # 解錠処理。 `My Script` はヒストリに記録される文字列。
            device.toggle(history_tag="My Script")
        # 登録されていない場合の処理
        else:
            logger.error('登録されていない学生です。idm:{}'.format(self.idm))
            return
# ----------------------------------学生証情報取得処理-----------------------------

    def read_id(self):
        clf = nfc.ContactlessFrontend('usb')
        try:
            clf.connect(rdwr={'on-connect': self.on_connect})
        finally:
            clf.close()
            return


if __name__ == '__main__':
    try:
        while True:
            # リスト初期化処理
            cr = MyCardReader()
            # タッチ時処理
            cr.read_id()
            # 連続読み取りがないように
            time.sleep(2)
    except OSError:
        print('nfcリーダーを接続してください')
        sys.exit()
