# 100年天気図データベース(http://agora.ex.nii.ac.jp/digital-typhoon/weather-chart/)から天気図を取得

import os
import urllib.request
import urllib.error
import urllib.parse
import time
import datetime

#### 期間を指定 ####
# 開始日時(UTC)
start = datetime.datetime(2022, 12, 31, 18, 0, 0)
# 終了日時(UTC)
end = datetime.datetime(2023, 11, 27, 12, 0, 0)
####################


savedir = './'  # データ保存先ディレクトリ
if not os.path.exists(savedir):
    os.makedirs(savedir)

d = start
while d <= end:
    if d.hour in [0, 3, 6, 9, 12, 18, 21]:
        # データ取得先URL
        url = f'http://agora.ex.nii.ac.jp/digital-typhoon/weather-chart/wxchart/{d.year}{d.month:02d}/SPAS_COLOR_{d.strftime("%Y%m%d%H%M")}.png'

        # ファイル名
        basename = os.path.basename(url)
        savename = os.path.join(savedir, basename)

        # ファイルが存在しない場合のみダウンロード
        if not os.path.exists(savename):
            try:
                urllib.request.urlretrieve(url, savename)
                time.sleep(1)
                print('downloaded:', basename)
            except urllib.error.URLError as e:
                print(url)
                print(e)
        else:
            print('file exists:', basename)

    d += datetime.timedelta(hours=3)