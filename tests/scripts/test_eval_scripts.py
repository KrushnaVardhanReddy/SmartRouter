import json
from unittest.mock import MagicMock, mock_open, patch

from scripts.eval_classifier import main as eval_main
from scripts.seed_training_data import main as seed_main


@patch("scripts.seed_training_data.load_dataset")
def test_seed_training_data_success(mock_load_dataset: MagicMock, tmpdir: str) -> None:
    # Setup mock dataset
    mock_dataset = [
        {
            "question_id": "1",
            "conversation_a": [{"role": "user", "content": "Hello"}],
            "winner_model_a": 1,
            "model_a": "mistral-7b",
        },
        {
            "question_id": "2",
            "conversation_a": [{"role": "user", "content": "Complex question"}],
            "winner_model_b": 1,
            "model_b": "gpt-4",
        },
    ]
    mock_load_dataset.return_value = mock_dataset

    with (
        patch("os.makedirs") as mock_makedirs,
        patch("builtins.open", mock_open()) as mock_file,
    ):
        seed_main()
        mock_makedirs.assert_called_with("data", exist_ok=True)
        mock_file.assert_called_with("data/training_seed.jsonl", "w")

        # Check if write was called with expected JSON strings
        handle = mock_file()
        handle.write.assert_any_call(
            json.dumps(
                {"prompt": "Hello", "winner_model": "mistral-7b", "is_complex": 0}
            )
            + "\n"
        )
        handle.write.assert_any_call(
            json.dumps(
                {"prompt": "Complex question", "winner_model": "gpt-4", "is_complex": 1}
            )
            + "\n"
        )


@patch("scripts.seed_training_data.load_dataset")
def test_seed_training_data_fallback(mock_load_dataset: MagicMock, tmpdir: str) -> None:
    # Force exception
    mock_load_dataset.side_effect = Exception("HF Access Denied")

    with (
        patch("os.makedirs") as mock_makedirs,
        patch("builtins.open", mock_open()) as mock_file,
    ):
        seed_main()
        mock_makedirs.assert_called_with("data", exist_ok=True)
        mock_file.assert_called_with("data/training_seed.jsonl", "w")

        # Verify fallback wrote data
        handle = mock_file()
        assert handle.write.call_count == 4


@patch("scripts.eval_classifier.joblib.load")
@patch("scripts.eval_classifier.SentenceTransformer")
@patch("os.path.exists")
def test_eval_classifier_success(
    mock_exists: MagicMock,
    mock_transformer: MagicMock,
    mock_load: MagicMock,
    capsys: MagicMock,
) -> None:
    mock_exists.return_value = True

    # Mock classifier predict
    mock_clf = MagicMock()
    # Assume 50 golden prompts, return dummy predictions
    mock_clf.predict.return_value = [0] * 35 + [1] * 15
    mock_load.return_value = mock_clf

    # Mock transformer encode
    mock_transformer_instance = MagicMock()
    mock_transformer_instance.encode.return_value = [[0.1, 0.2]] * 50
    mock_transformer.return_value = mock_transformer_instance

    eval_main()

    # Check that classification report was printed
    captured = capsys.readouterr()
    assert "Simple (0)" in captured.out
    assert "Complex (1)" in captured.out


@patch("os.path.exists")
def test_eval_classifier_missing_model(mock_exists: MagicMock) -> None:
    # Need to mock joblib so we don't try to load the missing file
    mock_exists.side_effect = lambda path: path != "models/complexity_classifier.pkl"

    with patch("sys.exit") as mock_exit:
        mock_exit.side_effect = SystemExit(1)
        try:
            eval_main()
        except SystemExit:
            pass
        mock_exit.assert_called_once_with(1)
