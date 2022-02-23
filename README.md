# syswork
学生・備品情報管理

解錠システム(sesamev3)

# DEMO
学生情報・備品情報の管理や登録を行うシステムです。
ご興味ございましたら以下のリンクから簡単な動作状況をご確認くださいませ(以下、参考画像とリンク)。

 https://youtu.be/nM1gErLJULg

<img width="403" alt="メニュー" src="https://user-images.githubusercontent.com/53808519/154916164-ddaf0fe3-c14f-43db-904e-0d3eb9ba0ce2.png">
<img width="469" alt="スクリーンショット 2022-02-21 17 26 15" src="https://user-images.githubusercontent.com/53808519/154916277-69820337-d016-4faa-9bd5-ccea153ca78d.png">
 
解錠システムは登録した学生情報を参照して解錠するかどうかを決めるシステムです。
解錠にはsesame3を利用しています(以下、参考画像)。

<img width="817" alt="スクリーンショット 2022-02-22 13 36 39" src="https://user-images.githubusercontent.com/53808519/155063946-32ae3ab1-6867-4b15-8c6e-b13ad9ba438f.png">

<img width="817" alt="スクリーンショット 2022-02-22 13 36 58" src="https://user-images.githubusercontent.com/53808519/155063969-2ab458f9-0fca-4531-aa64-b8be915f06a5.png">

 
# Features
 <img width="779" alt="スクリーンショット 2022-02-21 17 52 09" src="https://user-images.githubusercontent.com/53808519/154920453-b3ff187f-d680-4e6b-88fc-45d5c5509bea.png">

 学生情報・備品情報を一元管理し、参照しやすいものにしました。
 
# Requirement
 menu.py,backyard.py
 
* Python 3.9.2
* libusb 1.0.24
* nfcpy 1.0.3
* pandas 1.3.4
* PyMySQL 1.0.2
* tabulate 0.8.9
* DateTime 4.3

sesamev3.py
* pysesame3 0.5.1


 
 
# Installation
 
libusb は右のURLからダウンロードしてください https://github.com/libusb/libusb.

nfcpy,pandas,tabulate,DateTime,PyMySQL,pysesame3 は pip3コマンドでインストールしてください(以下、例)。
 
```bash
pip3 install nfcpy
pip3 install pandas
pip3 install tabulate 
pip3 install datetime
pip3 install mysqlclient
pip3 install pysesame3
```
 
# Usage
 
sysworkをダウンロードして、menu.pyを目的のSQLサーバーに接続できるようにしてから実行してください(以下、実行例)。

```bash
python3 menu.py
```
 
# Note
 
 Linux,Windows環境では動作確認をしておりません。
 
# Author
 
* 飯高 正規
# Licence

GNU General Public License v3.0
 
