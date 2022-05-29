# private 関数
from backyard import statusClass
from backyard import resisterItemClass
from backyard import resisterStudentClass
from backyard import changeSchoolYearClass
from backyard import developClass
from backyard import lendingClass
from backyard import nfcSQLClass

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
        print('5:備品登録(nfcなし)')
        print('6:学年変更')
        print('7:貸出')
        print('8:返却')
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
            stay = statusClass()
            stay.SQLstatus("select 学籍番号,学年,氏名,最終更新 from 学生情報")
            # 取り出したデータに対して列を設定して表形式で出力する
            print(stay.printdf('学籍番号', '学年', '氏名', '最終更新'))
        elif keyPress == '2':
            tool = statusClass()
            tool.SQLstatus("select 資産番号,備品名,備品状態,最終更新 from 備品情報")
            print(tool.printdf('資産番号','備品名', '備品状態','最終更新'))

        # 3:学生情報登録処理
        elif keyPress == '3':
            student = resisterStudentClass(0x300B, 4)
            try:
                # ---------------------nfc接続,データ取得処理----------------------
                student.nfcConnect()
                idm = student.getidm()
                # --------------------------------------------------------------

                # -------------------idmの照合処理(テーブルを指定)------------------
                SQLidm = student.SQLRead("select idm from 学生情報 where idm = '{}'".format(idm))
                # データの重複登録が行われないよう、データベース内に同じidmがあった場合にエラー出力,19に治す
                student.isResister(idm, str(SQLidm)[3:19], '既に登録されている学生情報です、メニューに戻ります')
                # --------------------------------------------------------------

                # -------------idm,取得した学生情報の呼び出し,加工処理----------------
                editList = student.geteditList()
                student.editListInput('氏名：')
                # 学生情報の加工処理
                student.editdict(editList, '学籍番号', '学年', '氏名')
                # --------------------------------------------------------------

                # --------------------学生情報の登録処理---------------------------
                res = student.resDecoretor(student.SQLCommit)
                res("INSERT INTO 学生情報(idm, 学籍番号, 学年, 氏名) VALUES('{}',{})".format(idm,str(editList)[1:-1]))
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

            try:
                tool.nfcConnect()
                idm = tool.getidm()

                SQLidm = tool.SQLRead("select idm from 備品情報 where idm = '{}'".format(idm))
                tool.isResister(idm, str(SQLidm)[3:19], '既に登録されている備品情報です、メニューに戻ります')

                # ---------------備品名の入力処理,任意の備品名の入力------------------
                print('資産番号を決定してください')
                tool.editListInput('資産番号:')
                print('備品名を決定してください')
                tool.editListInput('備品名：')
                # --------------------------------------------------------------

                editList = tool.geteditList()
                tool.editdict(editList,'資産番号','備品名')

                res = tool.resDecoretor(tool.SQLCommit)
                res("INSERT INTO 備品情報(idm,資産番号,備品名) VALUES('{}',{})".format(idm,str(editList)[1:-1]))

            except OSError:
                print('OSError：nfcリーダーが接続されていません。メニューに戻ります')
            except ValueError as v:
                print(v)
            except Exception as e:
                print('Errorが発生しました:%s' % (e))
                tool.errorLog()

        # 5:備品登録処理,備品名の入力処理以外は3と同様
        elif keyPress == '5':
            tool = resisterItemClass()

            try:

                # ---------------備品名の入力処理,任意の備品名の入力------------------
                print('資産番号を決定してください')
                tool.editListInput('資産番号:')
                editList = tool.geteditList()
                inputAsset = str(editList)[1:-1]

                assetNum = tool.SQLRead("select 資産番号 from 備品情報 where idm = '{}'".format(inputAsset))
                tool.isResister(inputAsset, assetNum, '既に登録されている備品情報です、メニューに戻ります')

                print('備品名を決定してください')
                tool.editListInput('備品名：')
                # --------------------------------------------------------------

                editList = tool.geteditList()
                tool.editdict(editList,'資産番号','備品名')

                res = tool.resDecoretor(tool.SQLCommit)
                res("INSERT INTO 備品情報(idm,資産番号,備品名) VALUES('Not exist',{})".format(str(editList)[1:-1]))

            except OSError:
                print('OSError：nfcリーダーが接続されていません。メニューに戻ります')
            except ValueError as v:
                print(v)
            except Exception as e:
                print('Errorが発生しました:%s' % (e))
                tool.errorLog()
        # 6:学年変更処理,学年変更部分以外はほぼ3と同様
        elif keyPress == '6':
            change = changeSchoolYearClass()
            try:
                change.nfcConnect()
                idm = change.getidm()

                SQLidm = change.SQLRead("select idm from 学生情報 where idm = '{}'".format(idm))
                change.isNotResister(idm, str(SQLidm)[3:19], '登録されていない学生です')

                # ---------------学年取得処理(上:変更前,下:変更後)-------------------
                SQLYear = change.SQLRead("select 学年 from 学生情報 where idm='{}'".format(idm))
                editList = change.geteditList()
                editList.append(str(SQLYear[1])[1:2])
                change.inputYear()
                # --------------------------------------------------------------
                change.editdict(editList, '変更前の学年', '変更後の学年')


                res = change.resDecoretor(change.SQLCommit)
                res("UPDATE 学生情報 SET 学年 = {} where idm = '{}'".format(int(editList[1]),idm))

            except OSError:
                print('OSError：nfcリーダーが接続されていません。メニューに戻ります')
            except ValueError as v:
                print(v)
            except Exception as e:
                print('Errorが発生しました:%s' % (e))
                change.errorLog()
        elif keyPress == '7':
            Lending = lendingClass()
            try:
                Lending.nfcConnect()
                idm = Lending.getidm()

                SQLidm = Lending.SQLRead("select idm from 備品情報 where idm = '{}'".format(idm))
                Lending.isNotResister(idm, str(SQLidm)[3:19], '登録されていない学生です')
                shineee = Lending.SQLRead("select 氏名 from 学生情報 where idm = '{}'".format(idm))

                # ---------------つかれた！-------------------
                Lending.nfcConnectItem()
                idmItem = Lending.getidm()
                BihinName = Lending.SQLRead("select 備品名 from 備品情報 where idm = '{}'".format(idmItem))
                # --------------------------------------------------------------

                lender = Lending.resDecoretor(Lending.SQLCommit)
                lender("UPDATE 備品情報 SET 備品状態 = '貸出' where idm = '{}'".format(idm))
                lender("INSERT INTO 貸出表(備品名,氏名) VALUES('{}','{}')".format(BihinName,shineee))
        elif keyPress == '8':
            Lending = lendingClass()
            try:
                Lending.nfcConnect()
                idm = Lending.getidm()

                SQLidm = Lending.SQLRead("select idm from 備品情報 where idm = '{}'".format(idm))
                Lending.isNotResister(idm, str(SQLidm)[3:19], '登録されていない学生です')
                shineee = Lending.SQLRead("select 氏名 from 学生情報 where idm = '{}'".format(idm))

                # ---------------つかれた！-------------------
                
                # --------------------------------------------------------------

                lender = Lending.resDecoretor(Lending.SQLCommit)
                lender("UPDATE 備品情報 SET 備品状態 = '在庫' where idm = '{}'".format(idm))
                lender("DELETE FROM 学生情報 WHERE 氏名 = '{}".format(shineee))


            except OSError:
                print('OSError：nfcリーダーが接続されていません。メニューに戻ります')
            except ValueError as v:
                print(v)
            except Exception as e:
                print('Errorが発生しました:%s' % (e))
                Lending.errorLog()
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
