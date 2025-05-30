"""Pytest of the plotting features of spectrafit."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

from spectrafit.plotting import PlotSpectra


if TYPE_CHECKING:
    from matplotlib.figure import Figure


def test_succeeds(plt: Figure) -> None:
    """Test that PlotSpectra class succeeds for 2D-plotting."""
    df = pd.DataFrame(
        {
            "energy": [
                0.016666666666660834,
                0.03333333333332744,
                0.04999999999999405,
                0.06666666666666066,
                0.08333333333332726,
                0.09999999999999389,
                0.11666666666666048,
                0.1333333333333271,
                0.14999999999999367,
                0.1666666666666603,
                0.18333333333332688,
            ],
            "intensity": [
                1.0,
                0.9729729729729932,
                0.9000684869288876,
                0.8003319898391893,
                0.6926622009062817,
                0.5905260079579859,
                0.5003698828803956,
                0.423907359037742,
                0.36038627792143624,
                0.3080871943516519,
                0.26510966833725974,
            ],
            "residual": [
                4.293843129771638,
                0.39554995606172927,
                -0.28453246680920363,
                -0.45258667445713796,
                -0.4696561377537798,
                -0.4354907592881011,
                -0.3863910251803334,
                -0.336604782590621,
                -0.2913861284024335,
                -0.25218528482526675,
                -0.21890253212043048,
            ],
            "fit": [
                5.293843129771638,
                1.3685229290347225,
                0.615536020119684,
                0.34774531538205133,
                0.22300606315250193,
                0.15503524866988483,
                0.11397885770006222,
                0.08730257644712103,
                0.06900014951900274,
                0.05590190952638513,
                0.04620713621682926,
            ],
            "peak": [
                5.293843129771638,
                1.3685229290347225,
                0.615536020119684,
                0.34774531538205133,
                0.22300606315250193,
                0.15503524866988483,
                0.11397885770006222,
                0.087302576447121,
                0.06900014951900275,
                0.05590190952638515,
                0.0462071362168292,
            ],
        },
    )
    args = {"noplot": True, "global_": False}
    PlotSpectra(df=df, args=args)()
    plt.show()


def test_empty(plt: Figure) -> None:
    """Test that PlotSpectra class succeeds for no-plotting."""
    df = pd.DataFrame(
        {
            "energy": [
                0.016666666666660834,
                0.03333333333332744,
                0.04999999999999405,
                0.06666666666666066,
                0.08333333333332726,
                0.09999999999999389,
                0.11666666666666048,
                0.1333333333333271,
                0.14999999999999367,
                0.1666666666666603,
                0.18333333333332688,
            ],
            "intensity": [
                1.0,
                0.9729729729729932,
                0.9000684869288876,
                0.8003319898391893,
                0.6926622009062817,
                0.5905260079579859,
                0.5003698828803956,
                0.423907359037742,
                0.36038627792143624,
                0.3080871943516519,
                0.26510966833725974,
            ],
            "residual": [
                4.293843129771638,
                0.39554995606172927,
                -0.28453246680920363,
                -0.45258667445713796,
                -0.4696561377537798,
                -0.4354907592881011,
                -0.3863910251803334,
                -0.336604782590621,
                -0.2913861284024335,
                -0.25218528482526675,
                -0.21890253212043048,
            ],
            "fit": [
                5.293843129771638,
                1.3685229290347225,
                0.615536020119684,
                0.34774531538205133,
                0.22300606315250193,
                0.15503524866988483,
                0.11397885770006222,
                0.08730257644712103,
                0.06900014951900274,
                0.05590190952638513,
                0.04620713621682926,
            ],
            "peak": [
                5.293843129771638,
                1.3685229290347225,
                0.615536020119684,
                0.34774531538205133,
                0.22300606315250193,
                0.15503524866988483,
                0.11397885770006222,
                0.087302576447121,
                0.06900014951900275,
                0.05590190952638515,
                0.0462071362168292,
            ],
        },
    )
    args = {"noplot": False, "global_": False}
    PlotSpectra(df=df, args=args)()
    plt.show()
