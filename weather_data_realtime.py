import urllib.request
import os

import datetime
import pytz
import pygrib
import pandas as pd
import numpy as np

print("---リアルタイム制御用気象予報データ抽出プログラム開始---\n")

# 現在の日時取得########################################################
# タイムゾーンを指定
tz = pytz.timezone('Asia/Tokyo')

#現地の日付と時刻を取得
now = datetime.datetime.now(tz)
today = now.date()
current_time = now.hour
current_time = int(current_time)

#毎時30分を超えた場合、current_timeをn.5時になるよう設定
current_minute = now.minute
current_minute = int(current_minute)
if current_minute >= 30:
    current_time += 0.5

time_diff = datetime.timedelta(hours=9) #時差


#時間を現在時刻に関係なく指定する場合
#current_time = 17.5   #テスト用・数値は時間(0.5刻み)を入力

########################################################################


#ダウンロードするファイル名の指定######################################################################################
# この部分でJST->UTCへの変換
#午前中：現在時刻(JST)と取得するデータ公開時刻(UTC)の日付が異なるとき(データ利用時間を考慮して0000-1130(JST))
if current_time >= 0 and current_time <12:  
    data_year = (today - datetime.timedelta(days=1)).strftime("%Y")
    data_date = (today - datetime.timedelta(days=1)).strftime("%m%d")
    data_date1 = (today - datetime.timedelta(days=1)).strftime("%Y/%m/%d")

    #0000-0230(JST)
    if current_time < 3:    #JST
        data_time = 120000    #UTC
    #0300-0530(JST)
    elif current_time < 6:    #JST
        data_time = "150000"    #UTC
    #0600-0830(JST)
    elif current_time < 9:    #JST
        data_time = "180000"    #UTC
    #0900-1130(JST)
    elif current_time < 12:    #JST
        data_time = "210000"    #UTC

#現在時刻(JST)と取得するデータ公開時刻(UTC)が同じ日付になるとき
else:
    data_year = today.strftime("%Y")
    data_date = today.strftime("%m%d")
    data_date1 = today.strftime("%Y/%m/%d")

    #1200-1430(JST)
    if current_time < 15:    #JST
        data_time = "000000"    #UTC
    #1500-1730(JST)
    elif current_time < 18:    #JST
        data_time = "030000"    #UTC
    #1800-2030(JST)
    elif current_time < 21:    #JST
        data_time = "060000"    #UTC
    #2100-2330(JST)
    elif current_time < 24:    #JST
        data_time = "090000"    #UTC
    

#時間を現在時刻に関係なく指定する場合
#data_year = 2023
#data_date = "0626"    #(当日の日付を4桁で指定)
#data_date1 = "2023/06/26"    #YYYY/MM/DD



# Grid Point指定#########################
#欲しい場所の場所指定
lat =36.06489716079195
lon = 140.1349848817127

#最寄りのGrid Point探索の範囲指定
#緯度 0.05度刻み
lat1 = lat - 0.025
lat2 = lat + 0.025
#経度 0.0625度刻み
lon1 = lon - 0.03125
lon2 = lon + 0.03125



# 表示部分################################################################
print("緯度 : " + str(lat))
print("経度 : " + str(lon) + "\n")

print("今日の日付:" + str(today.strftime("%Y/%m/%d")))
print("現在時刻:" + str(now.strftime("%H:%M") + "\n"))
print(str(data_date1) + " " + data_time + "(UTC)公開の直近の予測データを取得\n")



#---------------------------------------------------------------------------------------------------------
#GPVデータパラメータ定義
#prmsl = gpv_file.select(parameterName='Pressure reduced to MSL')            #[0] 海面更正気圧[Pa]
#sp    = gpv_file.select(parameterName='Pressure')                           #[1] 気圧[Pa]
#uwind = gpv_file.select(parameterName='u-component of wind')                #[2] 風速(東西)[m/s]
#vwind = gpv_file.select(parameterName='v-component of wind')                #[3] 風速(南北)[m/s]
#temp  = gpv_file.select(parameterName='Temperature')                        #[4] 気温[K]
#rh    = gpv_file.select(parameterName='Relative humidity')                  #[5] 相対湿度[%]
#lcc   = gpv_file.select(parameterName='Low cloud cover')                    #[6] 下層雲量[%]
#mcc   = gpv_file.select(parameterName='Medium cloud cover')                 #[7] 中層雲量[%]
#hcc   = gpv_file.select(parameterName='High cloud cover')                   #[8] 上層雲量[%]
#tcc   = gpv_file.select(parameterName='Total cloud cover')                  #[9] 全雲量[%]
#tp    = gpv_file.select(parameterName='Total precipitation')                #[10] 降水量[kg/m^2]
#dswrf = gpv_file.select(parameterName='Downward short-wave radiation flux') #[11] 下向き短波放射フラックス[W/m^2]
#---------------------------------------------------------------------------------------------------------

#出力データの型枠生成
df = pd.DataFrame(columns=["year","month","day","hour","Pressure","temperature","u-component of wind","v-component of wind","Relative humidity", "Total cloud cover", "Total precipitation"])

#関数：データ取得
def data_acquisition(data_year, data_date, data_time, data_range):

    # GRIB2ファイルを読み込む#########################################

    #ファイル名の文字列指定
    #このプログラムのフォルダ名
    dataname_base = "Battery-Control-By-Reinforcement-Learning/"

    #GPVファイル名
    dataname_base1 = "Z__C_RJTD_"
    dataname_base2 = "_MSM_GPV_Rjp_Lsurf_FH"
    dataname_base3 = "_grib2.bin"

    #GPVファイル名(ダウンロード用)
    file_name = dataname_base1 + str(data_year) + str(data_date) + data_time + dataname_base2 + data_range + dataname_base3

    #ファイルパス(フォルダ指定用)
    file_path = dataname_base + file_name


    ## 京大RISHからファイルをダウンロード
    print(data_range +"時間後予測  ファイルダウンロード開始...")
    url_surf = "http://database.rish.kyoto-u.ac.jp/arch/jmadata/data/gpv/original/" + str(data_date1) + "/" + file_name
    urllib.request.urlretrieve(url_surf, file_path)
    print(data_range +"時間後予測  ファイルダウンロード完了")


    #ファイルオープン
    gpv_file = pygrib.open(file_path)
    print(data_range +"時間後予測  データ取得開始...")
    

    # データ抽出#########################################################3
    #パラメータ指定
    p_messages  = gpv_file.select(parameterName='Pressure')
    t_messages = gpv_file.select(parameterName='Temperature')
    uw_messages = gpv_file.select(parameterName='u-component of wind')
    vw_messages = gpv_file.select(parameterName='v-component of wind')
    rh_messages  = gpv_file.select(parameterName='Relative humidity')
    tcc_messages  = gpv_file.select(parameterName='Total cloud cover')
    tp_messages  = gpv_file.select(parameterName='Total precipitation')
    dswrf_messages  = gpv_file.select(parameterName='Downward short-wave radiation flux')

    #時系列取り出し・データ分解
    df_validdata_ = pd.DataFrame({"validDate": [msg.validDate + time_diff for msg in t_messages]})
    df_validdata = pd.DataFrame(columns=["year","month","day","hour"])
    df_validdata['year'] = df_validdata_['validDate'].dt.year
    df_validdata['month'] = df_validdata_['validDate'].dt.month
    df_validdata['day'] = df_validdata_['validDate'].dt.day
    df_validdata['hour'] = df_validdata_['validDate'].dt.hour

    #各データフレームへデータ格納
    #気圧([hPa]へ変換)
    df1 = pd.DataFrame({
        "Pressure":[
            msg.data(lat1, lat2, lon1, lon2)[0][0][0] * 0.01 for msg in p_messages
        ]
   })
    #気温(摂氏変換)
    df2 = pd.DataFrame({
        "temperature": [
            msg.data(lat1, lat2, lon1, lon2)[0][0][0] - 273.15 for msg in t_messages
        ]
    })
    #u風速(東西方向)
    df3 = pd.DataFrame({
        "u-component of wind":[
            msg.data(lat1, lat2, lon1, lon2)[0][0][0] for msg in uw_messages
        ]
    })
    #v風速(南北方向)
    df4 = pd.DataFrame({
        "v-component of wind":[
            msg.data(lat1, lat2, lon1, lon2)[0][0][0] for msg in vw_messages
        ]
    })
    #湿度
    df5 = pd.DataFrame({
        "Relative humidity":[
            msg.data(lat1, lat2, lon1, lon2)[0][0][0] for msg in rh_messages
        ]
    })
    #雲量
    df6 = pd.DataFrame({
        "Total cloud cover":[
            msg.data(lat1, lat2, lon1, lon2)[0][0][0] for msg in tcc_messages
        ]
    })
    #降水量
    df7 = pd.DataFrame({
        "Total precipitation":[
            msg.data(lat1, lat2, lon1, lon2)[0][0][0] for msg in tp_messages
        ]
    })
    #日射量
    df8 = pd.DataFrame({
        "radiation flux":[
            msg.data(lat1, lat2, lon1, lon2)[0][0][0] for msg in dswrf_messages
        ]
    })

    # データ整理####################################################
    #データフレーム統合
    df_ = pd.concat([df_validdata, df1], axis=1)
    df_ = pd.concat([df_, df2], axis=1)
    df_ = pd.concat([df_, df3], axis=1)
    df_ = pd.concat([df_, df4], axis=1)
    df_ = pd.concat([df_, df5], axis=1)
    df_ = pd.concat([df_, df6], axis=1)
    df_ = pd.concat([df_, df7], axis=1)
    df_ = pd.concat([df_, df8], axis=1)
    
    #欠損値へ0を挿入
    df_.fillna(0)

    print(data_range +"時間後予測  データ取得完了")

    #ファイルクローズ
    gpv_file.close()
    #ファイル削除
    os.remove(file_path)

    print(data_range +"時間後予測  ファイル削除完了\n")

    return df_

##0-15時間後予測のファイルを処理#############################################
df_ = data_acquisition(data_year, data_date, data_time, data_range = "00-15")
df_T = df_.T    #空の列を挿入するために転置
list = (1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31)  #空の列挿入(毎時30分用)
for i in list:  
    df_T.insert(i, i + 0.5, np.nan)   #列の名前を混同しないように　i + 0.5 とする
df_ = df_T.T    #転置して元に戻す
df = pd.concat([df, df_], axis=0)   #出力用データフレームに統合


##16-33時間後(16-30時間後)データ
df_ = data_acquisition(data_year, data_date, data_time, data_range = "16-33")
df_.drop(range(15, 18),inplace=True)  #28-33時間後を削除
df_T = df_.T    #空の列を挿入するために転置
list = (1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27)  #空の列挿入(毎時30分用)
for i in list:
    df_T.insert(i, i + 0.5, np.nan)   #列の名前を混同しないように　i + 100.5 とする
df_ = df_T.T    #転置して元に戻す
df = pd.concat([df, df_], axis=0)   #出力用データフレームに統合


# データ整理######################################################
#index整理(1から振りなおす)
df = df.reset_index(drop=True)

#線形補間
df = df.interpolate()

# 線形補間後の数値調整
# 年・日付・月をまたぐときに数値がおかしくならないための調整

for i in range(5,59):   #ファイルの開始時間は3の倍数時からなので、確認するのは5番目のデータからでいい
    #年またぎ
    if df.at[i, 'year'] != df.at[i+1, 'year']:
        df.at[i, 'year'] = df.at[i-1, 'year']

    #月またぎ
    if df.at[i, 'month'] != df.at[i+1, 'month']:
        df.at[i, 'month'] = df.at[i-1, 'month']
        df.at[i, 'day'] = df.at[i-1, 'day']

    #日付またぎ
    if df.at[i-1, 'hour'] == 23.0:
        df.at[i, 'hour'] = 23.5
    

##転置の時に年月日がdouble型になっているため、int化
df['year'] = df['year'].astype('int')
df['month'] = df['month'].astype('int')
df['day'] = df['day'].astype('int')



##48個のデータにするためにデータを一部削除
#現在時刻の行を探索(行列で2つ出力される)
j = df.loc[df['hour'] == current_time, 'hour'].index.values

#現在時刻から24時間分以外を消去
#24時間後以降を消去(先に消さないと行がずれる)
df.drop(df.index[j[1] + 1:],inplace=True)
#現在時刻以前を消去
df.drop(df.index[:j[0] + 1], inplace=True)

#index整理(1から振りなおす)
df = df.reset_index(drop=True)


# ファイル出力###################################################################
df.to_csv('Battery-Control-By-Reinforcement-Learning/weather_data_realtime.csv')
print("--結果出力完了--")
print(df)
print("\n\n---気象予報データ抽出プログラム終了---")
