# Video_Clipper
### 実行環境
- macOS Sierra 10.12.6
- Python 3.7.0
- ffmpeg 4.0.2
- 動画ファイルの拡張子はmp4がテスト済み

### Python 前提ライブラリ
- ffmpeg-python==0.1.16
- more-itertools==4.3.0
- numpy==1.14.5
- scipy==1.1.0
- sk-video==1.1.10
- tqdm==4.25.0
- configparser==3.5.0
- opencv-python==3.4.2.17

### セットアップ
- セットアップにgitのインストールが必要
- setup.shに実行権限を付与し、実行
- "pip3 install -r requirments.txt"でPythonの前提ライブラリが入る

### 実行方法とデータの見方
1. python3 video_clipper.py [動画ファイルのパス]
2. saves/ に"[動画名]_[作成日時]"というフォルダが生成される
3. その中に、clip_name_list.txt, part_of_*****.**, clipped_[動画ファイル名]というファイルが生成される
4. 各ファイルの見方
    A. clip_name_list.txt
    - カットされたファイルのパスが書かれている
    B. part_of_*****.**
    - 複数存在し、カットされた結合する前の動画
    C. clipped_[動画ファイル名]
    - "目的のファイル"
    - カットされた動画を結合したもの

### config.confの読み方
1. skipping_frame
- 最小で1
- 大きくする程、処理を飛ばすフレームが増える
- 内部的には、frameの番号をskipping_frameで割った時の余りが0になる時のみ画像を解析するようになっている
2. search_range
- 最小で1
- 各フレームを比べるのではなく、フレームを固まりで捉えオブジェクト数の数を判定する時に用いる変数
- 1時間~の動画であれば10程度あれば十分
3. clip_num
- いくつの動画を切り出すか. 3つであれば、clip_num = 3
4. output_video_length
- 単位は"秒"
- 最終的な動画の長さ

