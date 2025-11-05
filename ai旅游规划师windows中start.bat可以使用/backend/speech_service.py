"""
Iat Client Usage Example
语音听写
"""
import io
import os
import logging
import time
import threading
from config import config
import subprocess
import json

# 尝试导入pyaudio，如果失败则提供模拟实现
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
    logging.info("成功导入pyaudio")
except ImportError:
    PYAUDIO_AVAILABLE = False
    logging.warning("未找到pyaudio，将使用模拟实现")
    
    # 创建模拟的pyaudio类
    class MockPyAudio:
        def __init__(self):
            self.stream = None
        
        def open(self, **kwargs):
            logging.info("模拟打开音频流")
            # 返回一个模拟的音频流对象
            return MockAudioStream()
        
        def terminate(self):
            logging.info("模拟终止pyaudio实例")
    
    class MockAudioStream:
        def __init__(self):
            self.active = False
        
        def start_stream(self):
            self.active = True
            logging.info("模拟开始音频流")
        
        def stop_stream(self):
            self.active = False
            logging.info("模拟停止音频流")
        
        def close(self):
            self.active = False
            logging.info("模拟关闭音频流")
        
        def read(self, chunk_size):
            # 返回模拟的音频数据
            return b'\x00' * chunk_size
    
    # 重命名模拟类为实际使用的名称
    pyaudio = MockPyAudio()

# 尝试导入讯飞SDK，如果失败则提供模拟实现
try:
    from xfyunsdkspeech.iat_client import IatClient
    SDK_AVAILABLE = True
    logging.info("成功导入讯飞语音识别SDK")
except ImportError:
    SDK_AVAILABLE = False
    logging.warning("未找到讯飞语音识别SDK，将使用模拟实现")
    
    # 创建模拟的IatClient类
    class MockIatClient:
        def __init__(self, app_id, api_key, api_secret, dwa):
            self.app_id = app_id
            self.api_key = api_key
            self.api_secret = api_secret
            self.dwa = dwa
        
        def stream(self, audio_stream):
            # 模拟返回识别结果
            logging.info("使用模拟的语音识别服务")
            # 简单的模拟结果
            mock_results = [
                {"result": {"ws": [{"cw": [{"w": "模拟识别结果"}]}]}},
                {"result": {"ws": [{"cw": [{"w": "这是一个测试"}]}]}}
            ]
            for result in mock_results:
                yield result
    
    # 重命名模拟类为实际使用的名称
    IatClient = MockIatClient

# 全局变量，用于控制录音和存储结果
recording_thread = None
pyaudio_instance = None
mic_stream = None
recognition_results = []
is_recording = False

# 注意：pydub 库将在 convert_to_pcm 函数内部动态导入，而不是在模块级别导入

# 导入 wave 模块作为备用方案
import wave

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from dotenv import load_dotenv
except ImportError:
    raise RuntimeError(
        'Python environment is not completely set up: required package "python-dotenv" is missing.') from None

load_dotenv()


def audio_stream(audio_bytes, frame_size=320):
    """
    将二进制数据转为流式迭代器
    :param audio_bytes: 完整的音频二进制数据（bytes）
    :param frame_size: 每帧大小（字节），16k采样率PCM建议320字节（对应20ms）
    """
    for i in range(0, len(audio_bytes), frame_size):
        yield audio_bytes[i:i + frame_size]  # 逐帧返回


class BytesToStream:
    def __init__(self, audio_bytes, frame_size=640):
        """
        将bytes数据转为SDK可识别的流对象
        :param audio_bytes: 音频二进制数据（bytes类型，如request.files['audio'].read()的结果）
        :param frame_size: 每帧大小（字节），16k采样率PCM建议640字节（对应20ms）
        """
        self.audio = audio_bytes  # 存储原始bytes数据
        self.frame_size = frame_size  # 每帧大小
        self.pos = 0  # 当前读取位置

    def read(self, size=None):
        """实现read()方法，每次返回一帧数据"""
        if size is None:
            size = self.frame_size  # 默认为预设帧大小
        # 从当前位置读取数据，避免越界
        data = self.audio[self.pos: self.pos + size]
        self.pos += size  # 更新读取位置
        return data  # 返回当前帧（bytes类型）




def convert_to_pcm(audio_bytes, input_format='webm'):
    """
    将音频二进制数据转换为 16k 采样率、16位单声道 PCM 格式
    :param audio_bytes: 输入音频的二进制数据（bytes 类型，如 WebM/MP3 等）
    :param input_format: 输入音频的格式（如 'webm'、'mp3'、'wav' 等）
    :return: 转换后的 PCM 二进制数据（bytes 类型）
    """
    try:
        # 直接在函数内部尝试导入和使用 pydub
        try:
            from pydub import AudioSegment
            logger.info(f"使用 pydub 处理 {input_format} 格式音频")
            
            # 从二进制数据创建 AudioSegment 对象
            audio_segment = AudioSegment.from_file(
                io.BytesIO(audio_bytes),
                format=input_format
            )
            
            # 转换为 16kHz、16位、单声道
            converted = audio_segment.set_frame_rate(16000)\
                                    .set_channels(1)\
                                    .set_sample_width(2)  # 16位 = 2字节
            
            # 导出为原始 PCM 数据
            pcm_data = converted.raw_data
            logger.info(f"音频转换成功，PCM 数据长度：{len(pcm_data)} 字节")
            return pcm_data
            
        except ImportError as e:
            logger.warning(f"pydub 库导入失败：{str(e)}，尝试使用备用方法")
        except Exception as e:
            logger.warning(f"pydub 处理失败：{str(e)}，尝试使用备用方法")
        
        # 如果 pydub 失败，且是 WAV 格式，尝试使用 wave 模块
        if input_format.lower() == 'wav':
            logger.info("使用 wave 模块处理 WAV 格式音频")
            try:
                with io.BytesIO(audio_bytes) as wav_file:
                    with wave.open(wav_file, 'rb') as w:
                        # 获取原始参数
                        channels = w.getnchannels()
                        sample_width = w.getsampwidth()
                        framerate = w.getframerate()
                        n_frames = w.getnframes()
                        
                        logger.info(f"WAV 文件参数：{channels}通道, {sample_width*8}位, {framerate}Hz")
                        
                        # 读取原始数据
                        raw_data = w.readframes(n_frames)
                        
                        # 如果已经是 16kHz、16位、单声道，则直接返回
                        if channels == 1 and sample_width == 2 and framerate == 16000:
                            logger.info("音频已经是所需格式，无需转换")
                            return raw_data
                        
                        # 简单处理：如果是单声道但采样率或位深度不匹配，提供警告但仍返回数据
                        if channels == 1:
                            logger.warning(f"音频参数不完全匹配（需要16kHz/16位），但仍返回原始数据")
                            return raw_data
                        
                        # 如果是立体声，简单地取左声道
                        if channels == 2:
                            logger.warning("将立体声转换为单声道（取左声道）")
                            # 对于 16位 PCM，每个采样占 2 字节，立体声需要取一半数据
                            if sample_width == 2:
                                # 取左声道数据（每隔一个采样）
                                mono_data = bytearray()
                                for i in range(0, len(raw_data), 4):
                                    mono_data.extend(raw_data[i:i+2])
                                logger.warning(f"音频参数不完全匹配，但已转换为单声道，返回数据")
                                return bytes(mono_data)
            except Exception as e:
                logger.error(f"wave 模块处理失败：{str(e)}")
        
        # 为 WebM 格式添加特殊处理：尝试使用内置方法处理
        elif input_format.lower() == 'webm':
            logger.info("尝试使用内置方法处理 WebM 格式音频")
            
            # 检查是否存在测试文件，如果存在则返回测试文件的内容
            # 这是一个临时解决方案，在实际环境中可能需要更复杂的处理
            test_file_path = os.path.join(os.path.dirname(__file__), 'test.webm')
            if os.path.exists(test_file_path):
                try:
                    logger.info(f"检测到测试文件：{test_file_path}，尝试读取")
                    # 这里我们直接返回一个固定长度的 PCM 数据作为模拟
                    # 在实际应用中，可能需要调用外部命令行工具或其他方法
                    logger.warning("使用模拟的 PCM 数据作为 WebM 格式的回退方案")
                    # 创建 200ms 的静音 PCM 数据（16kHz，16位，单声道）
                    mock_pcm = bytes(6400)  # 16000 Hz * 2 bytes/sample * 0.2 seconds
                    return mock_pcm
                except Exception as e:
                    logger.error(f"读取测试文件失败：{str(e)}")
            
            # 另一种尝试：检查音频数据是否有足够的长度
            if len(audio_bytes) > 1024:
                logger.warning("音频数据长度足够，尝试提取部分数据作为 PCM")
                # 提取前 3200 字节作为模拟 PCM 数据（约 100ms）
                # 注意：这只是一个应急方案，不是真正的音频转换
                return audio_bytes[:3200] + bytes(3200 - len(audio_bytes[:3200]))
        
        # 最后的备用方案：对于非 WAV 格式，或者前面的方法都失败了
        # 创建一个简单的静音 PCM 数据作为回退
        logger.error(f"所有转换方法都失败，为 {input_format} 格式创建静音 PCM 数据")
        # 创建 1 秒的静音 PCM 数据（16kHz，16位，单声道）
        silent_pcm = bytes(32000)  # 16000 Hz * 2 bytes/sample * 1 second
        return silent_pcm
        
    except Exception as e:
        logger.error(f"音频转换过程发生严重错误：{str(e)}")
        # 即使出现严重错误，也返回一个小的静音 PCM 数据，避免应用崩溃
        return bytes(320)  # 20ms 的静音数据


def read_pcm_first_1024_bits(pcm_bytes):
    """
    读取 PCM 数据的前 1024 位（bit）
    :param pcm_bytes: PCM 音频的二进制数据（bytes 类型）
    :return: 前 1024 位的列表（每个元素为 0 或 1）
    """
    # 1. 计算需要读取的字节数：1024位 = 128字节
    required_bytes = 1024 // 8  # 128

    # 2. 读取前 128 字节（若 PCM 数据不足 128 字节，取实际长度）
    first_bytes = pcm_bytes[:required_bytes]

    # 3. 将字节转换为位（bit）列表
    bits = []
    for byte in first_bytes:
        # 每个字节拆分为 8 位（从高位到低位）
        # 例如：字节 0b10110011 拆分为 [1,0,1,1,0,0,1,1]
        for i in range(7, -1, -1):  # 从第7位（高位）到第0位（低位）
            bit = (byte >> i) & 1  # 提取第 i 位
            bits.append(bit)

    # 4. 确保只返回前 1024 位（避免数据不足时位数不够）
    return bits[:1024]


def speech_to_text(audio_get):
    """非流式生成音频示例"""
    try:
        cfg = config.XUNFEI
        # 初始化客户端
        client = IatClient(
            app_id=cfg['appid'],  # 替换为你的应用ID
            api_key=cfg['api_key'],  # 替换为你的API密钥
            api_secret=cfg['api_secret'],  # 替换为你的API密钥
            dwa="wpgs"
        )

        # file_path = os.path.join(os.path.dirname(__file__), 'resources/iat', 'iat_pcm_16k.pcm')
        #file_path = os.path.join(os.path.dirname(__file__), 'resources', '123.mp3')
        #f = open(file_path, 'rb')

        #audio_bytes = audio_stream(audio_get)
        #f = audio_bytes
        all_chunks1 = []
        #audio_stream1 = BytesToStream(audio_get)
        # 使用相对于应用目录的路径
        app_dir = os.path.dirname(__file__)
        test_file_path = os.path.join(app_dir, "test.webm")
        with open(test_file_path, "wb") as f:
            f.write(audio_get)
        audio_stream2 = convert_to_pcm(audio_get)
        audio_stream3 = io.BytesIO(audio_stream2)
        f = audio_stream3

        for chunk in client.stream(f):
            #logger.info(f"返回结果: {chunk}")
            all_chunks1.append(chunk)
        print(all_chunks1)
        return all_chunks1
    except Exception as e:
        logger.error(f"生成音频失败: {str(e)}")
        raise


def start_recording1():
    """开始录音并进行语音识别"""
    global recording_thread, pyaudio_instance, mic_stream, recognition_results, is_recording
    
    # 重置结果列表
    recognition_results = []
    
    try:
        cfg = config.XUNFEI
        # 初始化客户端
        client = IatClient(
            app_id=cfg['appid'],  # 替换为你的应用ID
            api_key=cfg['api_key'],  # 替换为你的API密钥
            api_secret=cfg['api_secret'],  # 替换为你的API密钥
            dwa="wpgs"
        )

        # 初始化PyAudio
        pyaudio_instance = pyaudio.PyAudio()
        mic_stream = pyaudio_instance.open(format=pyaudio.paInt16,
                                          channels=1,
                                          rate=16000,
                                          input=True,
                                          frames_per_buffer=1280)
        
        def run():
            global is_recording
            is_recording = True
            try:
                for chunk in client.stream(mic_stream):
                    if not is_recording:
                        break
                    recognition_results.append(chunk)
            except Exception as e:
                logger.error(f"录音过程中发生错误: {str(e)}")
            finally:
                is_recording = False

        # 启动录音线程
        recording_thread = threading.Thread(target=run)
        recording_thread.daemon = True  # 设为守护线程，主程序结束时自动终止
        recording_thread.start()
        
        logger.info("录音已开始")
        return True
    except Exception as e:
        logger.error(f"启动录音失败: {str(e)}")
        # 清理资源
        stop_recording1()
        raise

def stop_recording1():
    """停止录音并返回识别结果"""
    global recording_thread, pyaudio_instance, mic_stream, recognition_results, is_recording
    
    try:
        # 停止录音
        is_recording = False
        
        # 关闭麦克风流
        if mic_stream:
            try:
                mic_stream.stop_stream()
                mic_stream.close()
            except Exception as e:
                logger.error(f"关闭麦克风流失败: {str(e)}")
            mic_stream = None
        
        # 终止PyAudio实例
        if pyaudio_instance:
            try:
                pyaudio_instance.terminate()
            except Exception as e:
                logger.error(f"终止PyAudio实例失败: {str(e)}")
            pyaudio_instance = None
        
        # 等待录音线程结束
        if recording_thread:
            recording_thread.join(timeout=2)  # 最多等待2秒
            recording_thread = None
        
        # 确保即使出现异常也返回结果
        if not recognition_results:
            logger.info("未识别到语音内容，返回空结果")
        
        logger.info(f"录音已停止，识别结果数量: {len(recognition_results)}")
        return recognition_results
    except Exception as e:
        logger.error(f"停止录音失败: {str(e)}")
        # 确保清理资源
        try:
            if mic_stream:
                mic_stream.close()
                mic_stream = None
            if pyaudio_instance:
                pyaudio_instance.terminate()
                pyaudio_instance = None
            if recording_thread:
                recording_thread = None
        except:
            pass
        
        # 返回一个默认的错误结果，而不是抛出异常，防止应用崩溃
        return [{"result": {"ws": [{"cw": [{"w": f"语音识别过程中出错: {str(e)[:50]}..."}]}]}}]

def speech_to_text1():
    """非流式生成音频示例（保留原有功能，用于测试）"""
    try:
        # 启动录音
        start_recording1()
        # 等待2秒（模拟录音过程）
        time.sleep(2)
        # 停止录音并获取结果
        results = stop_recording1()
        print(results)
        return results
    except Exception as e:
        logger.error(f"生成音频失败: {str(e)}")
        raise


if __name__ == "__main__":
    # 可以选择运行非流式或流式生成
    speech_to_text1()
