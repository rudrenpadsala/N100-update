import pytest

from src.analytics.cagr import (
    calculate_cagr,
    revenue_cagr,
    pat_cagr,
    eps_cagr,
    is_valid,
    is_turnaround,
    is_decline_to_loss,
    is_zero_base,
    is_both_negative,
    is_insufficient
)


# --------------------------------------------------
# Test 1
# Normal CAGR
# --------------------------------------------------

def test_normal_cagr():

    value, flag = calculate_cagr(100, 200, 5)

    assert value == 14.87
    assert flag == "OK"


# --------------------------------------------------
# Test 2
# Turnaround
# --------------------------------------------------

def test_turnaround():

    value, flag = calculate_cagr(-100, 200, 5)

    assert value is None
    assert is_turnaround(flag)


# --------------------------------------------------
# Test 3
# Decline to Loss
# --------------------------------------------------

def test_decline_to_loss():

    value, flag = calculate_cagr(100, -200, 5)

    assert value is None
    assert is_decline_to_loss(flag)


# --------------------------------------------------
# Test 4
# Zero Base
# --------------------------------------------------

def test_zero_base():

    value, flag = calculate_cagr(0, 100, 5)

    assert value is None
    assert is_zero_base(flag)


# --------------------------------------------------
# Test 5
# Both Negative
# --------------------------------------------------

def test_both_negative():

    value, flag = calculate_cagr(-50, -100, 5)

    assert value is None
    assert is_both_negative(flag)


# --------------------------------------------------
# Test 6
# Insufficient Years
# --------------------------------------------------

def test_insufficient():

    value, flag = calculate_cagr(100, 200, 2)

    assert value is None
    assert is_insufficient(flag)


# --------------------------------------------------
# Test 7
# Revenue CAGR
# --------------------------------------------------

def test_revenue_cagr():

    value, flag = revenue_cagr(1000, 2000, 5)

    assert value == 14.87
    assert flag == "OK"


# --------------------------------------------------
# Test 8
# PAT CAGR
# --------------------------------------------------

def test_pat_cagr():

    value, flag = pat_cagr(200, 500, 5)

    assert value == 20.11
    assert flag == "OK"


# --------------------------------------------------
# Test 9
# EPS CAGR
# --------------------------------------------------

def test_eps_cagr():

    value, flag = eps_cagr(10, 25, 5)

    assert value == 20.11
    assert flag == "OK"


# --------------------------------------------------
# Test 10
# Valid Flag
# --------------------------------------------------

def test_valid_flag():

    value, flag = calculate_cagr(100, 200, 5)

    assert is_valid(flag)