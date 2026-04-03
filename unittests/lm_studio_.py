import unittest
from unittest.mock import patch, MagicMock
from src.lm_studio import smart_model_loading

class TestSmartModelLoading(unittest.TestCase):

    @patch('src.lm_studio.load_model')
    @patch('src.lm_studio.unload_model_by_id')
    @patch('src.lm_studio.lms')
    @patch('src.lm_studio.config_lms')
    def test_smart_model_loading_unloads_correctly(self, mock_config, mock_lms, mock_unload_by_id, mock_load):
        mock_config.__getitem__.side_effect = lambda key: "mistral-8b" if key == "model_key" else None

        model1 = MagicMock(identifier="gpt-4-v1")
        model2 = MagicMock(identifier="llama-3")
        model3 = MagicMock(identifier="mistral-8b")
        mock_lms.list_loaded_models.return_value = [model1, model2, model3]

        smart_model_loading()

        mock_load.assert_not_called()
        self.assertEqual(2, mock_unload_by_id.call_count)
        expected_calls = [
            unittest.mock.call("gpt-4-v1"),
            unittest.mock.call("llama-3")
        ]
        mock_unload_by_id.assert_has_calls(expected_calls, any_order=True)

    @patch('src.lm_studio.load_model')
    @patch('src.lm_studio.unload_model_by_id')
    @patch('src.lm_studio.lms')
    @patch('src.lm_studio.config_lms')
    def test_smart_model_wrong_name(self, mock_config, mock_lms, mock_unload_by_id, mock_load):
        mock_config.__getitem__.side_effect = lambda key: "mistral-8b" if key == "model_key" else None
        model1 = MagicMock(identifier="mistral-8b-v2")
        mock_lms.list_loaded_models.return_value = [model1]

        smart_model_loading()

        mock_load.assert_called_once()
        mock_unload_by_id.assert_called_once()
        expected_calls = [
            unittest.mock.call("mistral-8b-v2")
        ]
        mock_unload_by_id.assert_has_calls(expected_calls, any_order=True)

    @patch('src.lm_studio.load_model')
    @patch('src.lm_studio.unload_model_by_id')
    @patch('src.lm_studio.lms')
    @patch('src.lm_studio.config_lms')
    def test_smart_model_unload_one_model(self, mock_config, mock_lms, mock_unload_by_id, mock_load):
        mock_config.__getitem__.side_effect = lambda key: "mistral-8b" if key == "model_key" else None
        model1 = MagicMock(identifier="mistral-8b")
        model2 = MagicMock(identifier="mistral-8b:2")
        mock_lms.list_loaded_models.return_value = [model1, model2]

        smart_model_loading()

        mock_load.assert_not_called()
        mock_unload_by_id.assert_called_once()
        expected_calls = [
            unittest.mock.call("mistral-8b:2")
        ]
        mock_unload_by_id.assert_has_calls(expected_calls, any_order=True)

    @patch('src.lm_studio.load_model')
    @patch('src.lm_studio.unload_model_by_id')
    @patch('src.lm_studio.lms')
    @patch('src.lm_studio.config_lms')
    def test_smart_model_loading_loads_if_empty(self, mock_config, mock_lms, mock_unload, mock_load):
        # Setup: No models currently loaded
        mock_lms.list_loaded_models.return_value = []

        smart_model_loading()

        # Assert: load_model should be triggered once
        mock_load.assert_called_once()
        mock_unload.assert_not_called()

    @patch('src.lm_studio.load_model')
    @patch('src.lm_studio.unload_model_by_id')
    @patch('src.lm_studio.lms')
    @patch('src.lm_studio.config_lms')
    def test_smart_model_one_model_no_unloading(self, mock_config, mock_lms, mock_unload_by_id, mock_load):
        mock_config.__getitem__.side_effect = lambda key: "mistral-8b" if key == "model_key" else None
        model1 = MagicMock(identifier="mistral-8b:2")
        mock_lms.list_loaded_models.return_value = [model1]

        smart_model_loading()

        mock_load.assert_not_called()
        mock_unload_by_id.assert_not_called()