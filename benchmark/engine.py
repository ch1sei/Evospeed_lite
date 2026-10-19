
import os
import signal
import subprocess
import time
import urllib.error
import urllib.request

from benchmark.config import ROOT_DIR

STARTUP_TIMEOUT = 600  # 默认等待引擎就绪的最长秒数


def start_engine(config):
    """启动推理引擎，等待就绪后返回进程"""
    engine_config = config["engine"]
    start_script = ROOT_DIR / engine_config["start_script"]
    if not start_script.is_file():
        raise FileNotFoundError(f"未找到启动脚本: {start_script}")

    # 在独立进程组中启动，便于 stop_engine 关闭整棵进程树
    engine_process = subprocess.Popen(
        ["bash", str(start_script)],
        cwd=ROOT_DIR,
        start_new_session=True,
    )

    try:
        # 轮询 OpenAI 的 /v1/models，直到引擎就绪
        url = engine_config["base_url"].rstrip("/") + "/models"
        timeout = int(engine_config.get("startup_timeout", STARTUP_TIMEOUT))
        deadline = time.monotonic() + timeout

        while time.monotonic() < deadline:
            if engine_process.poll() is not None:
                raise RuntimeError(f"引擎进程已退出: {engine_process.returncode}")
            try:
                with urllib.request.urlopen(url, timeout=2) as resp:
                    if resp.status == 200:
                        return engine_process
            except (urllib.error.URLError, TimeoutError):
                pass  # 等待并重试
            time.sleep(1)

        raise TimeoutError(f"引擎在 {timeout}s 内未就绪: {url}")
    except BaseException:
        # 等待失败时进程对象还没返回给 main，这里负责清理
        stop_engine(engine_process, config)
        raise


def stop_engine(engine_process, config):
    """停止推理引擎：优先执行 stop_script，留空则直接杀进程组"""
    if engine_process is None or engine_process.poll() is not None:
        return

    stop_script = config["engine"].get("stop_script")
    if stop_script:
        try:
            subprocess.run(
                ["bash", str(ROOT_DIR / stop_script)],
                cwd=ROOT_DIR,
                timeout=60,
            )
            engine_process.wait(timeout=10)
            return
        except subprocess.TimeoutExpired:
            pass  # 脚本超时或引擎未退出

    # 向整个进程组发送 SIGTERM，再兜底 SIGKILL
    try:
        os.killpg(engine_process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return

    try:
        engine_process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        os.killpg(engine_process.pid, signal.SIGKILL)
        engine_process.wait()
