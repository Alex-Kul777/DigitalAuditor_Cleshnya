import pytest
from tools.risk_matrix import calculate_risk_level

def test_critical_risk():
    assert calculate_risk_level('High', 'High') == 'Critical'

def test_low_risk():
    assert calculate_risk_level('Low', 'Low') == 'Low'
