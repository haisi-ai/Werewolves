"""
语音转文字模块 - 离线版
基于 faster-whisper 实现
"""

import os
import wave
import pyaudio
import numpy as np
from datetime import datetime
import threading
import time


class SpeechRecorder:
    """录音器类"""

    def __init__(self, save_dir="audio_records"):
        self.save_dir = save_dir
        self.is_recording = False
        self.recording_thread = None
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.chunk = 1024

        # 初始化PyAudio
        self.p = pyaudio.PyAudio()

        # 初始化Whisper模型（延迟加载）
        self.model = None

    def start_recording(self, filename):
        """开始录音"""
        self.filename = filename
        self.is_recording = True
        self.recording_thread = threading.Thread(target=self._record)
        self.recording_thread.start()

    def _record(self):
        """录音线程函数"""
        stream = self.p.open(format=self.audio_format,
                             channels=self.channels,
                             rate=self.rate,
                             input=True,
                             frames_per_buffer=self.chunk)

        frames = []

        while self.is_recording:
            try:
                data = stream.read(self.chunk, exception_on_overflow=False)
                frames.append(data)
            except Exception as e:
                print(f"录音错误: {e}")
                break

        # 停止录音
        stream.stop_stream()
        stream.close()

        # 保存为WAV文件
        if frames:
            wf = wave.open(self.filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.audio_format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()

    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        if self.recording_thread:
            self.recording_thread.join(timeout=2)

    def transcribe(self, audio_file, model_size="base"):
        """转写录音文件

        Args:
            audio_file: 音频文件路径
            model_size: 模型大小（tiny, base, small, medium, large）

        Returns:
            dict: 包含转写结果
        """
        try:
            # 延迟加载模型，避免启动时占用内存
            if self.model is None:
                from faster_whisper import WhisperModel
                # 检测可用设备
                import torch
                device = "cuda" if torch.cuda.is_available() else "cpu"
                compute_type = "float16" if device == "cuda" else "int8"

                print(f"加载Whisper模型 ({model_size}) 到 {device}...")
                self.model = WhisperModel(model_size, device=device, compute_type=compute_type)

            # 获取音频时长
            import wave
            with wave.open(audio_file, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                duration = frames / float(rate)

            # 狼人杀术语热词
            hotwords = "狼人,预言家,女巫,猎人,守卫,愚者,金水,银水,查杀,悍跳,警上,警下,遗言,投票,归票,抗推,自爆,毒药,解药,刀人,平安夜"

            # 转写
            segments, info = self.model.transcribe(
                audio_file,
                language="zh",
                beam_size=5,
                best_of=5,
                temperature=0.0,
                hotwords=hotwords,
                condition_on_previous_text=True,
                vad_filter=True,  # 启用语音活动检测
                vad_parameters=dict(
                    threshold=0.5,
                    min_speech_duration_ms=250,
                    min_silence_duration_ms=500
                )
            )

            # 收集结果
            text_parts = []
            for segment in segments:
                text_parts.append(segment.text)

            full_text = " ".join(text_parts)

            return {
                'success': True,
                'text': full_text,
                'duration': duration,
                'language': info.language,
                'confidence': info.language_probability
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def __del__(self):
        """析构函数，释放资源"""
        if hasattr(self, 'p'):
            self.p.terminate()


# 单独运行测试
if __name__ == "__main__":
    # 测试代码
    recorder = SpeechRecorder()
    print("语音转文字模块测试")
    print("1. 按回车开始录音")
    input()

    recorder.start_recording("test.wav")
    print("录音中...按回车停止")
    input()

    recorder.stop_recording()
    print("录音已保存，开始转写...")

    result = recorder.transcribe("test.wav")
    if result['success']:
        print(f"转写结果: {result['text']}")
    else:
        print(f"转写失败: {result['error']}")