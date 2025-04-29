import pytest
import pandas as pd
from src.presentation_layer.gui.models.file_model import FileModel

def test_file_model_immutable_and_valid():
    df = pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00'],
        'phone_number': ['1234567890'],
        'message_type': ['sent']
    })
    model = FileModel(df)
    # Should not raise
    assert model.rowCount() == 1
    assert model.columnCount() == 3
    # Data is immutable (modifying original does not affect model)
    df['timestamp'] = ['bad']
    assert model.dataframe['timestamp'][0] == '2023-01-01 12:00:00'
    # Data is validated (missing column raises)
    with pytest.raises(ValueError):
        FileModel(pd.DataFrame({'timestamp': ['x']}))

def test_file_model_qt_data():
    df = pd.DataFrame({
        'timestamp': ['2023-01-01 12:00:00'],
        'phone_number': ['1234567890'],
        'message_type': ['sent']
    })
    model = FileModel(df)
    index = model.index(0, 0)
    assert model.data(index) == '2023-01-01 12:00:00'
    assert model.headerData(0, 1) == 'timestamp'
    assert model.headerData(0, 2) == '0'
