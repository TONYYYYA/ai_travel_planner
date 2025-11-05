"""
Iat Client Usage Example
语音听写
"""
import io
import os
from xfyunsdkspeech.iat_client import IatClient
import logging
import time
import pyaudio
import threading
from config import config
import subprocess
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
current_dir = os.path.dirname(os.path.abspath(__file__))
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


def get_ffmpeg_path():
    # 判断当前系统
    if os.name == 'nt':  # Windows 系统
        # Windows 中指定 ffmpeg.exe 的路径（根据实际位置调整）
        return os.path.join(current_dir, '..', 'ffmpeg', 'bin', 'ffmpeg.exe')
    else:  # Linux 或 macOS 系统
        # Linux 中直接使用命令（已通过包管理器安装）
        return 'ffmpeg'

def convert_to_pcm(audio_bytes, input_format='webm'):
    """
    将音频二进制数据转换为 16k 采样率、16位单声道 PCM 格式
    :param audio_bytes: 输入音频的二进制数据（bytes 类型，如 WebM/MP3 等）
    :param input_format: 输入音频的格式（如 'webm'、'mp3'、'wav' 等）
    :return: 转换后的 PCM 二进制数据（bytes 类型）
    """
    try:
        # ffmpeg 命令参数说明：
        # -i pipe:0：从标准输入读取数据（即 audio_bytes）
        # -f s16le：输出格式为 16位 小端 PCM（语音识别常用格式）
        # -ac 1：单声道
        # -ar 16000：16k 采样率
        # pipe:1：输出到标准输出（便于 Python 捕获）
        ffmpeg_path = get_ffmpeg_path()
        # 例如这行，必须修改！
        # ##############################
        print("拼接后的ffmpeg路径：", ffmpeg_path)
        # 验证路径是否存在
        cmd = [
            ffmpeg_path,
            '-f', input_format,
            '-i', f'pipe:0',  # 从管道读取输入数据
            '-f', 's16le',  # 输出格式：16位 PCM（小端）
            '-ac', '1',  # 声道数：单声道
            '-ar', '16000',  # 采样率：16000Hz
            '-y',  # 覆盖输出（此处无实际文件，仅为兼容）
            'pipe:1'  # 输出到管道，供 Python 读取
        ]

        # 执行 ffmpeg 命令，输入音频数据，捕获输出的 PCM 数据
        result = subprocess.run(
            cmd,
            input=audio_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True  # 若命令执行失败，抛出异常
        )

        # 返回转换后的 PCM 二进制数据
        return result.stdout

    except subprocess.CalledProcessError as e:
        # 捕获 ffmpeg 执行错误（如格式不支持、数据损坏等）
        error_msg = e.stderr.decode('utf-8')
        raise RuntimeError(f"ffmpeg 转换失败：{error_msg}")
    except Exception as e:
        raise RuntimeError(f"转换过程出错：{str(e)}")


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
        with open("test.webm", "wb") as f:
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


def speech_to_text1():
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

        time.sleep(1)
        #input("按回车开始实时转写...")

        p = pyaudio.PyAudio()
        mic_stream = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=16000,
                            input=True,
                            frames_per_buffer=1280)
        all_chunks = []

        def run():
            for chunk in client.stream(mic_stream):
                #logger.info(f"返回结果: {chunk}")
                all_chunks.append(chunk)

        thread = threading.Thread(target=run)
        thread.start()
        time.sleep(2)
        input("正在聆听，按回车结束转写...\r\n")
        p.terminate()
        print('aaaa')
        print(all_chunks)
        return all_chunks
    except Exception as e:
        logger.error(f"生成音频失败: {str(e)}")
        raise


if __name__ == "__main__":
    # 可以选择运行非流式或流式生成
    speech_to_text1()
