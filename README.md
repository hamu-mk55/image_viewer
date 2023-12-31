# Image Viewer
## 概要
+ ホルダ中の画像を表示
+ 画像表示数の変更、単一チャンネル化、二値化、ズーム処理が可能
+ プロファイル表示、ヒストグラム表示
+ image_proc.pyに記載した画像処理を行うことも可能

## 構成
+ gui_params.py: GUI表示パラメータ
+ gui_window.py: 二値化ウインドウやプロファイル/ヒストグラム表示
+ opencv_func.py: opencvの関数
+ image_proc.py: 任意の画像処理

## Version
+ python 3.10
+ opencv-python 4.5.5.62
+ numpy 1.24.3
+ scikit-learn 1.3.2

