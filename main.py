
from benchmark.config import load_config
from benchmark.engine import start_engine, stop_engine


def run_benchmark(config):
    """执行性能测试"""
    cases = config["benchmark"]["cases"]

    for case_id in cases:
        print(f"Running case: {case_id}")

        # TODO: 加载 Case
        # TODO: 发送推理请求
        # TODO: 采集性能指标
        # TODO: 保存测试结果


def main():
    config = load_config()
    engine_process = None

    try:
        engine_process = start_engine(config)
        run_benchmark(config)
    finally:
        stop_engine(engine_process, config)


if __name__ == "__main__":
    main()
