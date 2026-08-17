import pytest
from unittest.mock import patch, MagicMock
from ml.vision import VisionModelWrapper
from ml.audio import AudioModelWrapper

@patch('ml.vision.pipeline')
@patch('ml.vision.Image.open')
@patch('ml.vision.os.listdir')
def test_vision_wrapper(mock_listdir, mock_image_open, mock_pipeline):
    # Mock file list
    mock_listdir.return_value = ['frame_000001.jpg', 'frame_000002.jpg']
    
    # Mock model pipeline output
    mock_classifier = MagicMock()
    mock_classifier.return_value = [
        {'label': 'nsfw', 'score': 0.95}, # High score -> Should be kept
        {'label': 'normal', 'score': 0.05}
    ]
    mock_pipeline.return_value = mock_classifier
    
    vision = VisionModelWrapper(model_path="fake_path")
    results = vision.analyze("/mock/dir", fps=1.0, threshold=0.8)
    
    assert len(results) == 2  # One hit for each frame
    assert results[0]['label'] == 'Nudity/NSFW'
    assert results[0]['confidence'] == 0.95

@patch('ml.audio.pipeline')
def test_audio_wrapper(mock_pipeline):
    # Mock transcriber output
    mock_transcriber = MagicMock()
    mock_transcriber.return_value = {
        'chunks': [
            {'timestamp': (0.0, 2.0), 'text': 'Hello world'}, # Clean
            {'timestamp': (2.0, 4.0), 'text': 'What the fuck'} # Dirty
        ]
    }
    mock_pipeline.return_value = mock_transcriber
    
    audio = AudioModelWrapper(model_path="fake_path")
    results = audio.analyze("/mock/audio.wav")
    
    assert len(results) == 1
    assert results[0]['label'] == 'Profanity'
    assert results[0]['word'] == 'fuck'
    assert results[0]['start'] == 2.0
    assert results[0]['end'] == 4.0
