import pytest
import pendulum
from unittest.mock import Mock,patch
import unittest
from logzero import logger
tz = 'Asia/Kolkata'

from fastbt.models.base import *

def get_test_period():
    periods = pendulum.datetime(2020,1,1,10,10,tz=tz) - pendulum.datetime(2020,1,1,10,0,tz=tz)
    periods = [x for x in periods.range('minutes')]
    return periods

class TestBaseParams:
    def test_default_time_args(self):
        base = BaseSystem()
        assert base.SYSTEM_START_TIME == tuple_to_time((9,15,0))
        assert base.SYSTEM_END_TIME == tuple_to_time((15,15,0))
        assert base.TRADE_START_TIME == tuple_to_time((9,16,0))
        assert base.SQUARE_OFF_TIME == tuple_to_time((15,15,0))
        
    def test_default_args(self):
        base = BaseSystem()
        assert base.INTERVAL == 60
        assert base.MAX_POSITIONS == 10
        assert base.TZ == 'Asia/Kolkata'
        assert base.CAPITAL_PER_STOCK == 100000
        assert base.RISK_PER_STOCK == 1000
        assert base.WEIGHTAGE == 'capital'
        
    def test_properties(self):
        base = BaseSystem()
        assert base.env == 'paper'
        assert base.name == 'base_strategy'
        assert base.done is False

    def test_change_args(self):
        base = BaseSystem(INTERVAL=120)
        assert base.INTERVAL == 120

        base = BaseSystem(SYSTEM_START_TIME=(10,0,0))
        assert base.SYSTEM_START_TIME == tuple_to_time((10,0,0))
        
        base = BaseSystem(TRADE_START_TIME=(10,15,0),SQUARE_OFF_TIME=(14,0,0))
        assert base.TRADE_START_TIME == tuple_to_time((10,15,0))
        assert base.SQUARE_OFF_TIME == tuple_to_time((14,0,0))
        
    def test_other_args(self):
        base = BaseSystem(env='live', name='new_strategy')
        assert base.name == 'new_strategy' 
        assert base.env == 'live' 

        base = BaseSystem(CAPITAL_PER_STOCK=10000,RISK_PER_STOCK=100,WEIGHTAGE='risk')
        assert base.CAPITAL_PER_STOCK == 10000
        assert base.RISK_PER_STOCK == 100
        assert base.WEIGHTAGE == 'risk'
        

class TestBaseTimeSpans:
    
    def test_timespan(self):
        tz = 'Asia/Kolkata'
        base = BaseSystem()
        ts1 = base.get_timespan()
        ts2 = pendulum.today(tz=tz).add(hours=15,minutes=15) - pendulum.today(tz=tz).add(hours=9,minutes=15)
        print(ts1)
        assert ts1 == ts2

    @patch.object(BaseSystem, 'get_time_periods')
    def test_time_periods(self, periods):
        prds = pendulum.datetime(2020,1,1,10,10,tz=tz) - pendulum.datetime(2020,1,1,10,0,tz=tz)
        prds = [x for x in prds.range('minutes')]
        periods.return_value = prds
        base = BaseSystem()
        periods.assert_called_once()
        assert base.periods == prds 


@patch.object(BaseSystem, 'get_time_periods')
@patch('pendulum.now')
def test_next_scan_initial(mock_now, mock_get_time_periods):
    mock_get_time_periods.return_value = get_test_period()
    mock_now.return_value = pendulum.datetime(2020,1,1,10,0,tz=tz)
    base = BaseSystem()
    assert base.get_next_scan() == pendulum.datetime(2020,1,1,10,0,tz=tz)

@patch.object(BaseSystem, 'get_time_periods')
@patch('pendulum.now')
def test_next_scan_elapsed(mock_now, mock_get_time_periods):
    mock_get_time_periods.return_value = get_test_period()
    mock_now.return_value = pendulum.datetime(2020,1,1,10,0,second=15,tz=tz)
    base = BaseSystem()
    assert base.get_next_scan() == pendulum.datetime(2020,1,1,10,1,tz=tz)
    assert len(base.periods) == 10

@patch.object(BaseSystem, 'get_time_periods')
@patch('pendulum.now')
def test_subsequent_scans(mock_now, mock_get_time_periods):
    mock_get_time_periods.return_value = get_test_period()
    mock_now.return_value = pendulum.datetime(2020,1,1,10,4,microsecond=1,tz=tz)
    base = BaseSystem()
    next_scan = base.get_next_scan()
    assert next_scan == pendulum.datetime(2020,1,1,10,5,tz=tz)
    assert len(base.periods) == 6

@patch.object(BaseSystem, 'get_time_periods')
@patch('pendulum.now')
def test_next_scan_multiple_calls(mock_now, mock_get_time_periods):
    mock_get_time_periods.return_value = get_test_period()
    mock_now.return_value = pendulum.datetime(2020,1,1,10,1,tz=tz)
    base = BaseSystem()
    next_scan = base.get_next_scan()
    assert base.get_next_scan() == pendulum.datetime(2020,1,1,10,1,tz=tz)
    next_scan = base.get_next_scan()
    assert base.get_next_scan() == pendulum.datetime(2020,1,1,10,1,tz=tz)
    next_scan = base.get_next_scan()
    assert base.get_next_scan() == pendulum.datetime(2020,1,1,10,1,tz=tz)

@patch.object(BaseSystem, 'get_time_periods')
@patch('pendulum.now')
def test_scan_periods(mock_now, mock_get_time_periods):
    """
    Check whether the periods list is correctly changed
    when next scan is run
    """
    mock_get_time_periods.return_value = get_test_period()
    mock_now.return_value = pendulum.datetime(2020,1,1,10,0,second=15,tz=tz)
    base = BaseSystem()
    next_scan = base.get_next_scan()
    assert base.periods[0] == pendulum.datetime(2020,1,1,10,1,tz=tz)

    mock_now.return_value = pendulum.datetime(2020,1,1,10,1,second=15,tz=tz)
    next_scan = base.get_next_scan()
    assert base.periods[0] == pendulum.datetime(2020,1,1,10,2,tz=tz)

    mock_now.return_value = pendulum.datetime(2020,1,1,10,9,second=15,tz=tz)
    next_scan = base.get_next_scan()
    assert base.periods[0] == pendulum.datetime(2020,1,1,10,10,tz=tz)
    assert len(base.periods) == 1
    
def test_intervals_periods():
    """
    Test number of periods with different intervals
    """
    start = pendulum.today().add(hours=9, minutes=15)
    with patch('pendulum.now') as mock_now:
        mock_now.return_value = start
        base = BaseSystem()
        assert len(base.periods) == 361

        base = BaseSystem(INTERVAL=120)
        assert len(base.periods) == 181
        
        base = BaseSystem(INTERVAL=300)
        assert len(base.periods) == 73 

        base = BaseSystem(INTERVAL=30)
        assert len(base.periods) == 721

def test_cycle_count():
    base = BaseSystem()
    base.run()
    assert base.cycle == 1
    for i in range(10):
        base.run()
    assert base.cycle == 11

def test_get_quantity_risk():
    base = BaseSystem(RISK_PER_STOCK=2500,WEIGHTAGE='risk')
    assert base.get_quantity(stop=25) == 100

def test_get_quantity_capital():
    base = BaseSystem(CAPITAL_PER_STOCK=2500)
    assert base.get_quantity(price=100) == 25

def test_get_quantity_unknown_method():
    base = BaseSystem(CAPITAL_PER_STOCK=2500,WEIGHTAGE='rl')
    assert base.get_quantity(price=100) == 25

def test_get_quantity_risk_no_stop():
    base = BaseSystem(WEIGHTAGE='risk')
    assert base.get_quantity() == 0
    assert base.get_quantity(price=100) == 0

def test_get_quantity_capital_no_price():
    base = BaseSystem()
    assert base.get_quantity() == 0
    assert base.get_quantity(stop=100) == 0
    


