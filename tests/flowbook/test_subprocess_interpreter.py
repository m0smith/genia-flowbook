import json
import subprocess
from pathlib import Path

from genia.flowbook.executor import (
    DEFAULT_GENIA_TIMEOUT_SECONDS,
    LocalGeniaInterpreter,
    SubprocessGeniaInterpreter,
    _get_default_interpreter,
)


def test_missing_runner_path_returns_structured_error(monkeypatch):
    monkeypatch.delenv("GENIA_FLOWBOOK_RUNNER", raising=False)
    interpreter = SubprocessGeniaInterpreter(executable_path="genia")

    result = interpreter.execute_pipeline({"nodes": [], "edges": []})

    assert result == {
        "success": False,
        "output": [],
        "error": "Genia runner path is not set. Set GENIA_FLOWBOOK_RUNNER or inject runner_path.",
        "nodeOutputs": {},
    }


def test_runner_path_not_found_returns_structured_error(tmp_path):
    interpreter = SubprocessGeniaInterpreter(
        executable_path="genia",
        runner_path=str(tmp_path / "missing.genia"),
    )

    result = interpreter.execute_pipeline({"nodes": [], "edges": []})

    assert result == {
        "success": False,
        "output": [],
        "error": f"Genia runner path does not exist: {tmp_path / 'missing.genia'}",
        "nodeOutputs": {},
    }


def test_missing_executable_returns_structured_error(tmp_path, monkeypatch):
    runner = tmp_path / "runner.genia"
    runner.write_text("// runner", encoding="utf-8")
    interpreter = SubprocessGeniaInterpreter(
        executable_path="missing-genia",
        runner_path=str(runner),
    )

    def raise_file_not_found(*args, **kwargs):
        raise FileNotFoundError("No such file or directory")

    monkeypatch.setattr(subprocess, "run", raise_file_not_found)

    result = interpreter.execute_pipeline({"nodes": [], "edges": []})

    assert result == {
        "success": False,
        "output": [],
        "error": "Genia executable not found: missing-genia",
        "nodeOutputs": {},
    }


def test_non_zero_exit_returns_stderr_error(tmp_path, monkeypatch):
    runner = tmp_path / "runner.genia"
    runner.write_text("// runner", encoding="utf-8")
    interpreter = SubprocessGeniaInterpreter(
        executable_path="genia",
        runner_path=str(runner),
    )

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0],
            1,
            stdout="",
            stderr="runner blew up",
        ),
    )

    result = interpreter.execute_pipeline({"nodes": [], "edges": []})

    assert result == {
        "success": False,
        "output": [],
        "error": "runner blew up",
        "nodeOutputs": {},
    }


def test_invalid_json_stdout_returns_error(tmp_path, monkeypatch):
    runner = tmp_path / "runner.genia"
    runner.write_text("// runner", encoding="utf-8")
    interpreter = SubprocessGeniaInterpreter(
        executable_path="genia",
        runner_path=str(runner),
    )

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0],
            0,
            stdout="not json",
            stderr="",
        ),
    )

    result = interpreter.execute_pipeline({"nodes": [], "edges": []})

    assert result["success"] is False
    assert result["output"] == []
    assert result["nodeOutputs"] == {}
    assert result["error"].startswith("Genia subprocess returned invalid JSON:")


def test_success_path_returns_normalized_result_and_payload(tmp_path, monkeypatch):
    runner = tmp_path / "runner.genia"
    runner.write_text("// runner", encoding="utf-8")
    interpreter = SubprocessGeniaInterpreter(
        executable_path="genia",
        runner_path=str(runner),
        timeout_seconds=3.5,
    )

    seen = {}

    def fake_run(args, capture_output, text, timeout, check):
        seen["args"] = args
        seen["capture_output"] = capture_output
        seen["text"] = text
        seen["timeout"] = timeout
        seen["check"] = check

        payload_path = Path(args[2])
        seen["payload_exists_during_run"] = payload_path.exists()
        seen["payload"] = json.loads(payload_path.read_text(encoding="utf-8"))

        return subprocess.CompletedProcess(
            args,
            0,
            stdout=json.dumps(
                {
                    "success": True,
                    "output": 15,
                    "error": None,
                    "nodeOutputs": ["ignored"],
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    pipeline = {
        "nodes": [{"id": "n1", "type": "source", "operation": "source"}],
        "edges": [],
    }
    result = interpreter.execute_pipeline(pipeline, input_val={"hello": "world"})

    assert result == {
        "success": True,
        "output": [15],
        "error": None,
        "nodeOutputs": {},
    }
    assert seen["args"][0] == "genia"
    assert seen["args"][1] == str(runner)
    assert seen["capture_output"] is True
    assert seen["text"] is True
    assert seen["timeout"] == 3.5
    assert seen["check"] is False
    assert seen["payload_exists_during_run"] is True
    assert seen["payload"] == {
        "pipeline": pipeline,
        "input": {"hello": "world"},
    }
    assert not Path(seen["args"][2]).exists()


def test_timeout_returns_structured_error(tmp_path, monkeypatch):
    runner = tmp_path / "runner.genia"
    runner.write_text("// runner", encoding="utf-8")
    interpreter = SubprocessGeniaInterpreter(
        executable_path="genia",
        runner_path=str(runner),
        timeout_seconds=1.25,
    )

    def raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=1.25)

    monkeypatch.setattr(subprocess, "run", raise_timeout)

    result = interpreter.execute_pipeline({"nodes": [], "edges": []})

    assert result == {
        "success": False,
        "output": [],
        "error": "Genia execution timed out after 1.25 seconds.",
        "nodeOutputs": {},
    }


def test_default_timeout_is_bounded():
    interpreter = SubprocessGeniaInterpreter(
        executable_path="genia",
        runner_path="/tmp/runner.genia",
    )

    assert interpreter.timeout_seconds == DEFAULT_GENIA_TIMEOUT_SECONDS


def test_default_interpreter_is_local_workflow_runner():
    assert isinstance(_get_default_interpreter(), LocalGeniaInterpreter)
