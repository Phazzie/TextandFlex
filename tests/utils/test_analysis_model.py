import pytest
import pandas as pd
from src.presentation_layer.gui.models.analysis_model import AnalysisResult, AnalysisResultModel
from PySide6.QtCore import Qt

def test_analysis_result_immutable_and_valid():
    df = pd.DataFrame({
        'metric': ['count'],
        'value': [42]
    })
    result = AnalysisResult('basic_stats', df)
    # Should not raise
    assert result.result_type == 'basic_stats'
    assert result.data['value'][0] == 42
    # Data is immutable (modifying original does not affect result)
    df['value'] = [0]
    assert result.data['value'][0] == 42
    # Data is validated (empty raises)
    with pytest.raises(ValueError):
        AnalysisResult('empty', pd.DataFrame())

def test_analysis_result_model_qt_data():
    df = pd.DataFrame({
        'metric': ['count'],
        'value': [42]
    })
    result = AnalysisResult('basic_stats', df)
    model = AnalysisResultModel(result)
    index = model.index(0, 0)
    assert model.data(index) == 'count'
    assert model.headerData(0, Qt.Horizontal) == 'metric'
    assert model.headerData(0, Qt.Vertical) == '0'
