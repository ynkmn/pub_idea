#include <memory>
#ifndef PBVR__JPV__PARTICLE_TRANSFER_PROTOCOL_H_INCLUDE
#define PBVR__JPV__PARTICLE_TRANSFER_PROTOCOL_H_INCLUDE

#include <string>
#include "Types.h"
#include <vismodule/Vector3>
#include "ExtendedTransferFunctionParameter.h"
#include "VariableRange.h"

#include <iostream>
#include <sstream>
#include <vector>

namespace vismodule
{
class Camera;
class TransferFunction;
}
namespace jpv
{

enum class InitializeParameter : int32_t {
     initial_step = -3,  // 値の設定
     end = -2,
     connection_reset = -1,
     generate_particle = 1,
     export_TFfile =2,
     generate_glyph = 3,
     send_glyph_flag_false = 4,
     plot_over_line = 5
};

enum class FileEnableFlag : int32_t
{
    Enable_VTK          = 0, //
    NotEnable_VTK       = 1, //
    NoFile          = 2  //
};


enum class DataDefines : int32_t
{
    Constant            = 0, //
    SingleVariable      = 1, //
    VariableArray       = 2  //
};

enum class GlyphMode  : int32_t
{
    UniformDistribution = 0, //max sampepoints,seed
    AllPoints           = 1, //No UI
    EveryNthPoints      = 2  //Stride
};

class ParticleTransferUtils
{
public:
    template<typename T>
    static void appendMessage( std::ostringstream& ss, T& content )
    {
        ss.write( reinterpret_cast<const char*>( &content ), sizeof( content ) );
    }
    static bool isLittleEndian( void );

private:
    static const int32_t m_magic_number;
};

class ParticleTransferClientMessage
{
public:
//    class VolumeEquation
//    {
//    public:
//        std::string m_name;
//        std::string m_equation;
//    };

    struct VolumeEquation
    {
        std::string m_name;
        std::string m_equation;
    };

    //2019 kawamura
    struct EquationToken
    {
        int exp_token[128];//数式のトークン配列
        int var_name[128];//数式の変数配列
        float value_array[128];//数式の値の配列
    };

public:
    char m_header[11];
    int32_t m_message_size;

    InitializeParameter m_initialize_parameter;
    bool m_import_flag;
    char m_sampling_method;
    int32_t m_subpixel_level;
    int32_t m_repeat_level;
    char m_shuffle_method;
    char m_node_type;
    float m_sampling_step;
    int32_t m_rendering_id;
    vismodule::Camera* m_camera;

    int32_t m_time_parameter;
    int32_t m_begin_time;
    int32_t m_last_time;
    int32_t m_memory_size;
    int32_t m_step;

    int32_t m_trans_parameter;
    int32_t m_level_index;

    int32_t m_enable_crop_region;
    float m_crop_region[6];
    int32_t m_particle_limit;
    float m_particle_density;
// #ifdef COMM_MODE_IS
    float m_particle_data_size_limit;
// #endif
    std::string m_input_directory;
    std::string m_filter_parameter_filename;         // add by @hira at 2016/12/01 //CS ONLY


    std::string m_x_synthesis; //CS ONLY
    std::string m_y_synthesis; //CS ONLY
    std::string m_z_synthesis; //CS ONLY

    std::vector<NamedTransferFunctionParameter> m_transfer_function;
    std::vector<VolumeEquation> m_volume_equation;

    std::string m_transfer_function_synthesis; //CS ONLY

    // add by @hira at 2016/12/01
    std::string m_color_transfer_function_synthesis;
    std::string m_opacity_transfer_function_synthesis;

    //2019 kawamura
    EquationToken opacity_func;//tfs_eq_token;
    EquationToken color_func;//tfs_eq_token;
    std::vector<EquationToken> opacity_var;//opacity_eq_token;
    std::vector<EquationToken> color_var;//color_eq_token;

    //2023 shimomura
    EquationToken x_synthesis_token;//x_synthesis; CS ONLY
    EquationToken y_synthesis_token;//y_synthesis; CS ONLY
    EquationToken z_synthesis_token;//z_synthesis; CS ONLY

    //グリフ
    bool m_glyph_flag; // グリフの生成判定
    //int32_t m_direction_variable[3];
    std::string m_direction_variable[3];
    //std::vector<std::string> m_direction_variable;

    DataDefines m_size_sampling_method;
    //std::vector<int32_t> m_size_variable;
    std::vector<std::string> m_size_variable;

    GlyphMode m_distribution_mode;
    int32_t m_number_of_sampling_point;
    uint32_t m_seed;
    int32_t m_stride;

    vismodule::ColorMap m_color_map;
    std::vector<int32_t> m_glyph_color_map_table;
    //std::vector<std::string> m_glyph_color_map_table;

    DataDefines m_color_data_sampling_method;
    std::vector<std::string> m_color_data_variable;

    float m_glyph_color_max;
    float m_glyph_color_min;
    float m_glyph_size_max;
    float m_glyph_size_min;

    //Plot Over Line
    bool m_plot_flag; // plot ober line の生成判定
    std::string m_plot_variable;
    int32_t m_sampling_size;
    float m_start_point[3];
    float m_end_point[3];

public:
    // message のサイズを計算
    int32_t byteSize( void ) const;
    // メッセージを byte 列に pack
    size_t pack( char* buf ) const;
    // byte 列からメッセージに unpack
    size_t unpack( const char* buf );

    ParticleTransferClientMessage( void );

    //2019 kawamura
    void show( void ) const;
};

class ParticleTransferServerMessage
{
public:

    struct VolumeEquation
    {
        std::string m_name;
        std::string m_equation;
    };

public:
    char m_header[18];
    int32_t m_message_size;
    int32_t m_server_status;   // 2015.12.23 Add Param for NaN CS ONLY
    int32_t m_time_step;
    int32_t m_subpixel_level;
    int32_t m_repeat_level;
    int32_t m_level_index;
    int32_t m_number_particle;
    int32_t m_number_volume_divide;
    int32_t m_start_step;
    int32_t m_last_step;
    int32_t m_number_step;
    // float* m_positions;
    // float* m_normals;
    // unsigned char* m_colors;
    std::unique_ptr<float[]> m_positions;
    std::unique_ptr<float[]> m_normals;
    std::unique_ptr<unsigned char[]> m_colors;
    float m_min_object_coord[3];
    float m_max_object_coord[3];
    float m_min_value;
    float m_max_value;
    int32_t m_number_nodes;
    int32_t m_number_elements;
    int32_t m_element_type;
    int32_t m_file_type;
    int32_t m_number_ingredients;
    int32_t m_flag_send_bins;  // 0:none, 1:histogram, 2: particle
    int32_t m_transfer_function_count;
//#ifdef COMM_MODE_IS
    int32_t m_particle_limit;
    float m_particle_density;
    float m_particle_data_size_limit;
    vismodule::Camera* m_camera;
    std::vector<NamedTransferFunctionParameter> m_transfer_function;
    std::vector<VolumeEquation> m_volume_equation;
//    std::vector<ParticleTransferClientMessage::VolumeEquation> voleqn;
//    std::string transferFunctionSynthesis;
//#endif
    std::string m_color_transfer_function_synthesis;
    std::string m_opacity_transfer_function_synthesis;
    vismodule::UInt64* m_color_nbins;
    vismodule::UInt64* m_opacity_nbins;
    std::vector<vismodule::UInt64*> m_color_bins;
    std::vector<vismodule::UInt64*> m_opacity_bins;
//    std::vector<std::string> m_color_bin_names;			// add by @hira at 2016/12/01
//    std::vector<std::string> m_opacity_bin_names;		// add by @hira at 2016/12/01

    FileEnableFlag m_file_enable_flag;
    
    // glyph
    int32_t m_number_glyph; 
    std::unique_ptr<float[]>  m_glyph_coords;
    std::unique_ptr<float[]>  m_glyph_vectors;
    std::unique_ptr<float[]>  m_glyph_sizes;
    std::unique_ptr<unsigned char[]>   m_glyph_colors;
    
    float m_glyph_color_max;
    float m_glyph_color_min;
    float m_glyph_size_max;
    float m_glyph_size_min;

    //Plot Over Line
    int32_t m_resolution;
    std::vector<float> m_xAxis;
    std::vector<int>  m_mask;
    std::vector<float> m_line_values;

    // message のサイズを計算
    int32_t byteSize( void ) const;
    // メッセージを byte 列に pack
    size_t pack( char* buf ) const;
    // byte 列からメッセージに unpack
    size_t unpack_message( const char* buf );
    size_t unpack_particles( const char* buf );
    size_t unpack_glyphs( const char* buf );
    size_t unpack_bins( const size_t index, const char* buf );
private:
    float m_transfer_function_min_value;
    float m_transfer_function_max_value;
public:
    VariableRange m_server_side_variable_range;

    ParticleTransferServerMessage( void );

    ParticleTransferServerMessage(size_t message_size, size_t number_particle)
        : m_message_size(message_size),
        m_number_particle(number_particle) {}

    // ムーブコンストラクタ
    ParticleTransferServerMessage(ParticleTransferServerMessage&& other) noexcept
        : m_message_size(other.m_message_size),
        m_number_particle(other.m_number_particle),
        m_positions(std::move(other.m_positions)),
        m_normals(std::move(other.m_normals)),
        m_colors(std::move(other.m_colors)) {}

    // ムーブ代入演算子
    ParticleTransferServerMessage& operator=(ParticleTransferServerMessage&& other) noexcept {
        if (this != &other) {
            m_message_size = other.m_message_size;
            m_number_particle = other.m_number_particle;
            m_positions = std::move(other.m_positions);
            m_normals = std::move(other.m_normals);
            m_colors = std::move(other.m_colors);
        }
        return *this;
    }

    // コピーコンストラクタとコピー代入演算子を削除
    ParticleTransferServerMessage(const ParticleTransferServerMessage&) = delete;
    ParticleTransferServerMessage& operator=(const ParticleTransferServerMessage&) = delete;

    void setColorHistogramBins(
        int histogram_size,
        int nbins,
        const vismodule::UInt64* arg_c_bins);/*,
            const std::vector<std::string> &transfer_function_names,
            const std::vector<std::string> &transfunc_synthesizer_names);*/
    void setOpacityHistogramBins(
        int histogram_size,
        int nbins,
        const vismodule::UInt64* arg_o_bins);/*,
            const std::vector<std::string> &transfer_function_names,
            const std::vector<std::string> &transfunc_synthesizer_names);*/

    void initializeTransferFunction(const int32_t transfer_function_count, const int nbins);
    //2019 kawamura
    void show( void ) const;
};

}

#endif //PBVR__JPV__PARTICLE_TRANSFER_PROTOCOL_H_INCLUDE
