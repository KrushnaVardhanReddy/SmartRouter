import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Add the repository root to sys.path so we can import from scripts without it being a package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from scripts import eval_classifier, seed_training_data


def test_seed_training_data_fallback() -> None:
    with (
        patch(
            "scripts.seed_training_data.load_dataset",
            side_effect=Exception("Gated dataset"),
        ),
        patch("scripts.seed_training_data.process_dataset") as mock_process,
    ):
        seed_training_data.main()

        # Verify fallback was called
        mock_process.assert_called_once()
        args, _kwargs = mock_process.call_args

        # Verify it passed a list of dicts (the dummy dataset)
        assert isinstance(args[0], list)
        assert len(args[0]) > 0
        assert "prompt" in args[0][0]


def test_seed_training_data_process_dataset(tmp_path: pytest.TempPathFactory) -> None:
    test_output_path = str(tmp_path / "training_seed.jsonl")  # type: ignore
    dummy_data = [
        {"prompt": "Hello", "winner_model": "gpt-3.5-turbo"},
        {"prompt": "Complex stuff", "winner_model": "gpt-4"},
        {"instruction": "Dummy instruction"},
    ]

    seed_training_data.process_dataset(dummy_data, test_output_path, max_samples=3)

    assert os.path.exists(test_output_path)

    with open(test_output_path, "r") as f:
        lines = f.readlines()

    assert len(lines) == 3
    parsed = [json.loads(line) for line in lines]

    assert parsed[0]["complexity"] == 0
    assert parsed[1]["complexity"] == 1
    assert parsed[2]["complexity"] in [0, 1]


def test_eval_classifier_main(capsys: pytest.CaptureFixture) -> None:
    # Patch joblib.load and SentenceTransformer
    with (
        patch("scripts.eval_classifier.joblib.load") as mock_load,
        patch("scripts.eval_classifier.SentenceTransformer") as mock_transformer,
        patch("scripts.eval_classifier.os.path.exists", return_value=True),
    ):
        mock_clf = MagicMock()
        mock_load.return_value = mock_clf

        # Predict should return a list of predictions same length as GOLDEN_DATASET
        mock_clf.predict.return_value = [0] * len(eval_classifier.GOLDEN_DATASET)

        mock_transformer_instance = MagicMock()
        mock_transformer_instance.encode.return_value = [[0.1, 0.2]] * len(
            eval_classifier.GOLDEN_DATASET
        )
        mock_transformer.return_value = mock_transformer_instance

        eval_classifier.main()

        # Verify encode and predict were called
        mock_transformer_instance.encode.assert_called_once()
        mock_clf.predict.assert_called_once()

        # Verify classification report was printed. The header " precision" should be there
        captured = capsys.readouterr()
        assert "precision" in captured.out
        assert "recall" in captured.out
