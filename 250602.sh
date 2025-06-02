cmake_minimum_required(VERSION 3.15) # CMakeの最低バージョンを指定。OneAPI 2025 なら十分新しいはずです。
project(YourFortranProject LANGUAGES Fortran)

# OneAPI環境をCMakeに認識させるための設定
# 環境変数ONEAPI_ROOTが設定されていることを前提とします。
if(NOT DEFINED ENV{ONEAPI_ROOT})
    message(FATAL_ERROR "ONEAPI_ROOT environment variable is not set. Please source the OneAPI environment script.")
endif()

# OneAPIのFortranコンパイラ (ifx) を使用するように設定
set(CMAKE_Fortran_COMPILER ${ONEAPI_ROOT}/compiler/latest/bin/ifx)

# ソースファイルのリスト
# srcフォルダ内のすべての.f, .f90, .F90ファイルを追加
file(GLOB_RECURSE PROJECT_SOURCES
    src/*.f
    src/*.f90
    src/*.F90
)

# モジュールファイルの出力ディレクトリを設定
# 通常はプロジェクトのビルドディレクトリに配置されます。
set(CMAKE_Fortran_MODULE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/modules)
file(MAKE_DIRECTORY ${CMAKE_Fortran_MODULE_DIRECTORY})

# 実行可能ファイルをビルドする
add_executable(your_fortran_app ${PROJECT_SOURCES})

# コンパイラフラグの設定

# リリースビルド用のフラグ
set(CMAKE_Fortran_FLAGS_RELEASE
    "-O3"               # 最適化レベル3
    "-xHost"            # 実行環境に合わせた最適化
    "-ipo"              # プログラム間最適化
    "-ansi_alias"       # ANSIエイリアシング規則を有効にする（パフォーマンス向上に寄与する場合がある）
    "-warn all"         # 全ての警告を有効にする
    "-module ${CMAKE_Fortran_MODULE_DIRECTORY}" # モジュール出力ディレクトリ
    "-gen-interfaces"   # モジュールのインターフェースファイルも生成
)

# デバッグビルド用のフラグ
set(CMAKE_Fortran_FLAGS_DEBUG
    "-g"                # デバッグ情報を生成
    "-O0"               # 最適化なし
    "-check all"        # ランタイムエラーチェックをすべて有効化
    "-traceback"        # エラー発生時のバックトレース情報を出力
    "-fpe0"             # 浮動小数点例外をトラップ
    "-warn all"         # 全ての警告を有効にする
    "-module ${CMAKE_Fortran_MODULE_DIRECTORY}" # モジュール出力ディレクトリ
    "-gen-interfaces"   # モジュールのインターフェースファイルも生成
)

# モジュールパスの追加
# モジュールをコンパイルする際に、他のモジュールを検索するパスを指定します。
# 通常、CMAKE_Fortran_MODULE_DIRECTORY は自動的に検索パスに追加されますが、
# 明示的に追加することで、より確実になります。
target_include_directories(your_fortran_app PRIVATE ${CMAKE_Fortran_MODULE_DIRECTORY})


# ifx (Intel Fortran Compiler) 特有のオプション
# 大文字小文字を区別しないソースファイル名の場合、f90として扱うオプション
# これにより、.f, .F90 でもモジュールや現代Fortranの機能が利用可能になります。
# ただし、これが望ましくない場合（例えば、.fファイルを意図的に古いFortranとしてコンパイルしたい場合）は削除してください。
target_compile_options(your_fortran_app PRIVATE -free -fixed) # .f と .F90 に対応するために指定
# -free は自由形式ソース、-fixed は固定形式ソースとして扱います。
# CMakeがファイルの拡張子に基づいて適切に処理しますが、明示的に指定することで意図を明確にできます。
# 混在している場合は、個別のファイルに対してコンパイラオプションを指定する必要があるかもしれませんが、
# 一般的にはifxが賢く処理してくれます。
# `-source-format free` や `-source-format fixed` もありますが、`-free` と `-fixed` の方が古い形式です。
# ifxはデフォルトで拡張子に基づいてソース形式を判断します。

# CMakeビルドタイプの設定
# `cmake -DCMAKE_BUILD_TYPE=Release ..` または `cmake -DCMAKE_BUILD_TYPE=Debug ..` で切り替えます。
# デフォルトはReleaseです。
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING
        "Choose the type of build, options are: Debug Release RelWithDebInfo MinSizeRel."
        FORCE
    )
endif()

message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")
