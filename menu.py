# private 関数
from backyard import statusClass
from backyard import resisterItemClass
from backyard import resisterStudentClass
from backyard import changeSchoolYearClass
from backyard import developClass

# public 関数
import sys


def menu():
    while True:
        # メニュー画面表示
        print('--------------------------------------------------------')
        print('備品管理システムへようこそ！操作を選んでください\n(番号をキーで入力し、Enterを押してください)')
        print('--------------------------------------------------------')
        print('1:在室状態確認')
        print('2:備品情報確認')
        print('3:学生情報登録')
        print('4:備品登録')
        print('5:学年変更')
        print('0:ログアウト')
        print('--------------------------------------------------------')
        # メニューの処理。キー入力に従って処理が行われる
        keyPress = input()
        # ログアウト(プログラムの終了処理)
        if keyPress == '0':
            print('プログラムは終了されました')
            sys.exit()

        # 1,2はデータベースから情報を取得し、表示する処理
        elif keyPress == '1':
            stay = statusClass("select 学番,学年,名前,最終更新 from 学生情報")
            stay.status()
            # 取り出したデータに対して列を設定して表形式で出力する
            stay.printdf('学籍番号', '学年', '氏名', '最終更新')
        elif keyPress == '2':
            tool = statusClass("select 備品名,備品状態 from 備品情報")
            tool.status()
            tool.printdf('備品名', '備品状態')

        # 3:学生情報登録処理
        elif keyPress == '3':
            student = resisterStudentClass()
            # アクセスするuser,password,host,DB,charsetの設定をする
            student.configSQL('user', 'passwd', 'host', 'db', 'utf8')
            try:
                # ---------------------nfc接続,データ取得処理----------------------
                student.nfcConnect()
                # --------------------------------------------------------------

                # -------------------idmの照合処理(テーブルを指定)------------------
                student.idmSQL('学生情報')
                # データの重複登録が行われないよう、データベース内に同じidmがあった場合にエラー出力
                student.idmCheckerT('既に登録されている学生情報です、メニューに戻ります')
                # --------------------------------------------------------------

                # -------------idm,取得した学生情報の呼び出し,加工処理----------------
                idm = student.getidm()
                editList = student.geteditList()
                # 学生情報の加工処理
                student.editdict(editList, '学籍番号', '学年', '氏名')
                # --------------------------------------------------------------

                # --------------------学生情報の登録処理---------------------------
                res = student.resDecoretor(student.insertSQL)
                res('学生情報', 'idm,学番,学年,名前', idm, *editList)
                # --------------------------------------------------------------
            # OS,ValueErrorはnfcリーダーが接続されていない,無効な入力の際に利用
            except OSError:
                print('OSError：nfcリーダーが接続されていません。メニューに戻ります')
            except ValueError as v:
                print(v)
            # 想定されていないエラーの処理(保険)
            except Exception as e:
                print('Errorが発生しました:%s' % (e))
                student.errorLog()

        # 4:備品登録処理,備品名の入力処理以外は3と同様
        elif keyPress == '4':
            tool = resisterItemClass()
            tool.configSQL('user', 'passwd', 'host', 'db', 'utf8')

            try:
                tool.nfcConnect()

                tool.idmSQL('備品情報')
                tool.idmCheckerT('既に登録されている備品IDです、メニューに戻ります')

                # ---------------備品名の入力処理,任意の備品名の入力------------------
                print('備品名を決定してください')
                tool.editListInput()
                # --------------------------------------------------------------

                idm = tool.getidm()
                editList = tool.geteditList()
                tool.editdict(editList, '備品名')

                res = tool.resDecoretor(tool.insertSQL)
                res('備品情報', 'idm,備品名', idm, *editList)

            except OSError:
                print('OSError：nfcリーダーが接続されていません。メニューに戻ります')
            except ValueError as v:
                print(v)
            except Exception as e:
                print('Errorが発生しました:%s' % (e))
                tool.errorLog()

        # 5:学年変更処理,学年変更部分以外はほぼ3と同様
        elif keyPress == '5':
            hen = changeSchoolYearClass()
            hen.configSQL('user', 'passwd', 'host', 'db', 'utf8')
            try:
                hen.nfcConnect()

                hen.idmSQL('学生情報')
                # 登録されていないデータに対してエラーの出力
                hen.idmCheckerF('登録されていない学生情報です、メニューに戻ります')

                # ---------------学年取得処理(上:変更前,下:変更後)-------------------
                hen.schoolYearSQL()
                hen.inputYear()
                # --------------------------------------------------------------

                idm = hen.getidm()
                editList = hen.geteditList()
                hen.editdict(editList, '変更前の学年', '変更後の学年')

                res = hen.resDecoretor(hen.updateSQL)
                res('学生情報', '学年', editList[1])

            except OSError:
                print('OSError：nfcリーダーが接続されていません。メニューに戻ります')
            except ValueError as v:
                print(v)
            except Exception as e:
                print('Errorが発生しました:%s' % (e))
                hen.errorLog()

        # develop:プログラム改善用
        elif keyPress == 'develop':
            dev = developClass()
            # 前述した処理とは若干異なり、カードの中身をダンプして表示する(中身全部)
            dev.nfcConnect()
        # 設定していない例外処理用
        else:
            print('処理が存在しません')


if __name__ == "__main__":
    menu()
