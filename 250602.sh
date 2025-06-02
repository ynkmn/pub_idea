cmake_minimum_required(VERSION 3.20)
project(MyFortranProject LANGUAGES Fortran)

add_executable(my_program src/main.f90)

# Fortran コンパイラのパス（フルパス）を取得
message(STATUS "Fortran compiler: ${CMAKE_Fortran_COMPILER}")

# 分岐によるフラグ設定
if(CMAKE_Fortran_COMPILER MATCHES "ifx$")
    message(STATUS "Using Intel ifx Fortran compiler")
    target_compile_options(my_program PRIVATE -real-size 64)

elseif(CMAKE_Fortran_COMPILER MATCHES "ifort$")
    message(STATUS "Using Intel ifort Fortran compiler")
    target_compile_options(my_program PRIVATE -real-size 64)

else()
    message(WARNING "Unknown Fortran compiler: ${CMAKE_Fortran_COMPILER}")
endif()



cmake_minimum_required(VERSION 3.15)
project(YourFortranProject LANGUAGES Fortran)

# OneAPI環境をCMakeに認識させるための設定
if(NOT DEFINED ENV{ONEAPI_ROOT})
    message(FATAL_ERROR "ONEAPI_ROOT environment variable is not set. Please source the OneAPI environment script.")
endif()

# OneAPIのFortranコンパイラ (ifx) を使用するように設定
set(CMAKE_Fortran_COMPILER ${ONEAPI_ROOT}/compiler/latest/bin/ifx)

# MPIを有効にするかどうかを制御するオプション
# デフォルトはOFF (MPIを使用しない)
option(ENABLE_MPI "Enable MPI support for the project" OFF)

# ソースファイルのリスト
# srcフォルダ内のすべての.f, .f90, .F90ファイルを追加
file(GLOB_RECURSE ALL_PROJECT_SOURCES
    src/*.f
    src/*.f90
    src/*.F90
)

# MPIの有効/無効に基づいてソースファイルを調整
set(PROJECT_SOURCES "") # 最終的なソースファイルのリストを初期化

if(ENABLE_MPI)
    message(STATUS "MPI support is ENABLED.")
    # MPIを有効にする場合のソースファイル
    # ここにMPI関連のソースファイルを含め、非MPIファイルを「除外」するロジックを記述

    # 例: src/non_mpi_module.f90 と src/non_mpi_main.f90 を除外
    # src/mpi_main.f90 と src/mpi_module.f90 を含める
    foreach(src_file IN LISTS ALL_PROJECT_SOURCES)
        if(NOT "${src_file}" MATCHES ".*non_mpi_module.f90$") # 例: 非MPIモジュールを除外
            if(NOT "${src_file}" MATCHES ".*non_mpi_main.f90$") # 例: 非MPIメインファイルを除外
                list(APPEND PROJECT_SOURCES "${src_file}")
            endif()
        endif()
    endforeach()

    # MPIライブラリの検索とリンク
    find_package(MPI REQUIRED Fortran) # Fortranバインディングを要求
    if(MPI_FOUND)
        message(STATUS "MPI Fortran found: ${MPI_Fortran_ADDITIONAL_INCLUDE_DIRS}")
        target_link_libraries(your_fortran_app PRIVATE ${MPI_Fortran_LIBRARIES})
        target_include_directories(your_fortran_app PRIVATE ${MPI_Fortran_ADDITIONAL_INCLUDE_DIRS})
        target_compile_options(your_fortran_app PRIVATE ${MPI_Fortran_COMPILE_OPTIONS})
    else()
        message(FATAL_ERROR "MPI Fortran was not found, but ENABLE_MPI is ON.")
    endif()

else()
    message(STATUS "MPI support is DISABLED.")
    # MPIを無効にする場合のソースファイル
    # ここに非MPI関連のソースファイルを含め、MPIファイルを「除外」するロジックを記述

    # 例: src/mpi_main.f90 と src/mpi_module.f90 を除外
    # src/non_mpi_main.f90 と src/non_mpi_module.f90 を含める
    foreach(src_file IN LISTS ALL_PROJECT_SOURCES)
        if(NOT "${src_file}" MATCHES ".*mpi_module.f90$") # 例: MPIモジュールを除外
            if(NOT "${src_file}" MATCHES ".*mpi_main.f90$") # 例: MPIメインファイルを除外
                list(APPEND PROJECT_SOURCES "${src_file}")
            endif()
        endif()
    endforeach()

endif()

# モジュールファイルの出力ディレクトリを設定
set(CMAKE_Fortran_MODULE_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}/modules)
file(MAKE_DIRECTORY ${CMAKE_Fortran_MODULE_DIRECTORY})

# 実行可能ファイルをビルドする
add_executable(your_fortran_app ${PROJECT_SOURCES})

# コンパイラフラグの設定 (リリース/デバッグ)
# ... (前回の内容と同じ。MPI特有のフラグは find_package(MPI) で追加される) ...

# モジュールパスの追加
target_include_directories(your_fortran_app PRIVATE ${CMAKE_Fortran_MODULE_DIRECTORY})

# ifx (Intel Fortran Compiler) 特有のオプション
target_compile_options(your_fortran_app PRIVATE -free -fixed)

# CMakeビルドタイプの設定
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release CACHE STRING
        "Choose the type of build, options are: Debug Release RelWithInfo MinSizeRel."
        FORCE
    )
endif()

message(STATUS "Build Type: ${CMAKE_BUILD_TYPE}")







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
