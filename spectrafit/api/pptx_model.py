"""PPTXModel class for SpectraFit API."""
import re
import tempfile

from pathlib import Path
from typing import Dict
from typing import List
from typing import Tuple
from typing import Type
from typing import Union

import pandas as pd
import pkg_resources

from matplotlib import pyplot as plt
from pptx.util import Pt
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field
from pydantic import field_validator
from spectrafit import __version__
from spectrafit.plotting import PlotSpectra


class MethodAPI(BaseModel):
    """Method class to check if global fitting is enabled."""

    global_fitting: bool


class DescriptionAPI(BaseModel):
    """Description class for PPTXData input."""

    project_name: str
    version: str


class InputAPI(BaseModel):
    """Input class for PPTXData input."""

    method: MethodAPI
    description: DescriptionAPI


class OutputAPI(BaseModel):
    """Dataframe class for PPTXData output."""

    df_fit: Dict[str, List[float]]


class GoodnessOfFitAPI(BaseModel):
    """GoodnessOfFit class."""

    chi2: float = Field(..., alias="chi_square")
    r_chi2: float = Field(..., alias="reduced_chi_square")
    akaike: float = Field(..., alias="akaike_information")
    bayesian: float = Field(..., alias="bayesian_information")


class RegressionMetricsAPI(BaseModel):
    """RegressionMetrics class."""

    index: List[str]
    columns: List[int]
    data: List[List[float]]

    @field_validator("index")
    @classmethod
    def short_metrics(cls, v: List[str]) -> List[str]:
        """Shorten the metrics names.

        Args:
            v (List[str]): The metrics names.

        Returns:
            List[str]: The shortened metrics names.
        """
        pattern = r"(?<!\d)[a-zA-Z0-9]{2,}(?!\d)"
        abbreviations: Dict[str, str] = {}
        for metric in v:
            abbreviation = "".join(re.findall(pattern, metric)).lower()[:2]
            while abbreviation in abbreviations.values() or len(abbreviation) < 2:
                abbreviation = "".join(re.findall(pattern, metric)).lower()[
                    : len(abbreviation) + 1
                ]
            abbreviations[metric] = abbreviation
        return list(abbreviations.values())


class SolverAPI(BaseModel):
    """Solver class for getting the metrics of the fit for PPTXData output."""

    goodness_of_fit: GoodnessOfFitAPI
    regression_metrics: RegressionMetricsAPI
    variables: Dict[str, Dict[str, float]]

    @field_validator("variables")
    @classmethod
    def short_variables(
        cls, v: Dict[str, Dict[str, float]]
    ) -> Dict[str, Dict[str, float]]:
        """Shorten the variables names.

        Args:
            v (Dict[str, Dict[str, float]]): The variables names.

        Returns:
            Dict[str, Dict[str, float]]: The shortened variables names.
        """
        new_dict = {}
        for key, value in v.items():
            new_key = "".join([part[:2] for part in key.split("_")])
            new_value = {}
            for sub_key, sub_value in value.items():
                new_sub_key = sub_key.replace("_value", "")
                new_value[new_sub_key] = sub_value
            new_dict[new_key] = new_value
        return new_dict


class PPTXDataAPI(BaseModel):
    """PPTXData class for SpectraFit API."""

    output: OutputAPI
    input: InputAPI
    solver: SolverAPI

    class Config:
        """Config class to allow to pass also not pydantic class members."""

        extra = "ignore"


class PPTXRatioAPI(BaseModel, arbitrary_types_allowed=True):
    """Ratio class for PPTXData input.

    !!! info "About the ratio"

        The ratio of the powerpoint presentation. This includes the width and height
        of the powerpoint presentation. The ratio is either `16:9` or `4:3`. The
        default ratio is `16:9` and the default width and height are `1920` and
        `1080` respectively. The width and height are in pixels.

    """

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
    width: Pt
    height: Pt


class PPTXPositionAPI(BaseModel):
    """Position class for PPTXData input.

    !!! info "About the position"

        The position of the elements in the powerpoint presentation. This includes
        the top, left, width and height of the elements for figure, table and
        textbox. All the values are in pixels.
    """

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
    left: Pt
    top: Pt
    width: Pt
    height: Pt


class PPTXHeaderAPI(BaseModel):
    """Header class for PPTXData input."""

    position: PPTXPositionAPI
    text: str


class PPTXDescriptionAPI(BaseModel):
    """Description class for PPTXData input.

    !!! info "About the description"

        The description of the elements in the powerpoint presentation. This
        includes the text of the description for figure, table and textbox.
    """

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
    position: PPTXPositionAPI
    text: str
    font_size: Pt = Field(default_factory=lambda: Pt(8))


class PPTXFigureAPI(BaseModel):
    """Figure class for PPTXData input.

    !!! info "About the figure"

        The figure of the elements in the powerpoint presentation, which is connected
        to the `PPTXDescriptionAPI` to provide both the figure and the description at
        the same time. This includes the position of the figure and the description
        of the figure. The figure can be either a `png` or `jpg` file and the
        description is a `str`.
    """

    position: PPTXPositionAPI
    description: PPTXDescriptionAPI
    fname: Path


class PPTXTableAPI(BaseModel):
    """Table class for PPTXData input.

    !!! info "About the table"

        The table of the elements in the powerpoint presentation, which is connected
        to the `PPTXDescriptionAPI` to provide both the table and the description at
        the same time. This includes the position of the table and the description
        of the table. The table is a `pandas.DataFrame` and the description is a
        `str`.
    """

    model_config = ConfigDict(validate_assignment=True, arbitrary_types_allowed=True)
    df: pd.DataFrame
    transpose: bool
    index_hidden: bool
    position: PPTXPositionAPI
    description: PPTXDescriptionAPI


class PPTXSubTitleLeftAPI(BaseModel):
    """SubTitle_1 class for PPTXData input.

    !!! info "About the left subtitle"

        The left subtitle of the elements in the powerpoint presentation defines the
        first column of the powerpoint presentation with the elements of the subtitle,
        the figure and the description of the figure. This includes the position of
        the subtitle, the text of the subtitle, the figure and the description of the
        figure.
    """

    index: int = 1
    position: PPTXPositionAPI
    text: str
    figure: PPTXFigureAPI


class PPTXSubTitleRightAPI(BaseModel):
    """SubTitle_2 class for PPTXData input.

    !!! info "About the right subtitle"

        The right subtitle of the elements in the powerpoint presentation defines the
        second column of the powerpoint presentation with the elements of the subtitle,
        the tables and their descriptions. The tables are divided into three tables for
        `goodness_of_fit`, `regression_metrics` and `variables`. This includes the
        position of the subtitle, the text of the subtitle, the tables and their
        descriptions. Finally, the credit of the figure is also included in the
        right subtitle.
    """

    index: int = 2
    position: PPTXPositionAPI
    text: str
    table_1: PPTXTableAPI
    table_2: PPTXTableAPI
    table_3: PPTXTableAPI
    credit: PPTXFigureAPI


class PPTXStructureAPI(BaseModel):
    """Structure class for PPTXData input."""

    header: PPTXHeaderAPI
    sub_title_left: PPTXSubTitleLeftAPI
    sub_title_right: PPTXSubTitleRightAPI


class Field169HDRAPI(BaseModel):
    """Field169HDRAPI class for PPTXData input.

    !!! info "About the field `16:9 High Definition Resolution (HDR)`"

        The field `16:9` of the elements in the powerpoint presentation defines the
        structure of the powerpoint presentation with the elements of the header,
        left subtitle and right subtitle for the ratio of `16:9` with pixel width
        and height of __1920__ and __1080__ respectively.
    """

    ratio: PPTXRatioAPI
    structure: PPTXStructureAPI


class Field169API(BaseModel):
    """Field169 class for PPTXData input.

    !!! info "About the field `16:9`"

        The field `16:9` of the elements in the powerpoint presentation defines the
        structure of the powerpoint presentation with the elements of the header,
        left subtitle and right subtitle for the ratio of `16:9` with pixel width
        and height of __1280__ and __720__ respectively.
    """

    ratio: PPTXRatioAPI
    structure: PPTXStructureAPI


class Field43API(BaseModel):
    """Field43 class for PPTXData input.

    !!! info "About the field `4:3`"

        The field `4:3` of the elements in the powerpoint presentation defines the
        structure of the powerpoint presentation with the elements of the header,
        left subtitle and right subtitle for the ratio of `4:3` with pixel width
        and height of __960__ and __720__ respectively.
    """

    ratio: PPTXRatioAPI
    structure: PPTXStructureAPI


class PPTXBasicTitleAPI(BaseModel):
    """PPTXBasicTitle class for PPTXData input.

    !!! info "About the basic title"

        The basic title of the elements in the powerpoint presentation defines the
        structure of the powerpoint presentation with the elements of the header,
        left subtitle and right subtitle for the ratio of `16:9` and `4:3`.
    """

    sub_title_left: str = "Plot: Fitted and Experimental Spectra"
    sub_title_right: str = "Tables: Metrics and Variables"
    figure_description: str = (
        "Figure 1: Fitted and Experimental Spectra with the Residuals"
    )
    table_1_description: str = "Table 1: Goodness of Fit"
    table_2_description: str = "Table 2: Regression Metrics"
    table_3_description: str = "Table 3: Variables"

    credit_logo: Path = (
        Path(pkg_resources.get_distribution("spectrafit").location)
        / "spectrafit/plugins/img/SpectraFit.png"
    )
    credit_description: str = f"SpectraFit: v{__version__}"


class PPTXLayoutAPI:
    """PPTXLayout class for PPTXData input.

    Attributes:
        pptx_formats (Dict[str, List[Union[Field169API, Field169HDRAPI, Field43API]]]):
            The formats of the powerpoint presentation. This includes the ratio of
            `16:9` and `4:3` with pixel width and height of __1280__ and __720__
            respectively for `16:9` and __960__ and __720__ respectively for `4:3`.
    """

    pptx_formats: Dict[
        str, Tuple[Type[Union[Field169API, Field169HDRAPI, Field43API]], Dict[str, int]]
    ] = {
        "16:9": (Field169API, {"width": 1280, "height": 720}),
        "16:9HDR": (Field169HDRAPI, {"width": 1920, "height": 1080}),
        "4:3": (Field43API, {"width": 960, "height": 720}),
    }

    def __init__(self, format: str, data: PPTXDataAPI) -> None:
        """Initialize the PPTXLayout class.

        Args:
            format (str): The format of the powerpoint presentation.
            data (PPTXDataAPI): The data of the powerpoint presentation.
        """
        self._format = format
        self.tmp_fname = self.tmp_plot(pd.DataFrame(data.output.df_fit))
        self.title = data.input.description.project_name
        self.df_gof = pd.DataFrame({k: [v] for k, v in data.solver.goodness_of_fit})
        self.df_regression = pd.DataFrame(**data.solver.regression_metrics.dict())
        self.df_variables = pd.DataFrame.from_dict(
            data.solver.variables, orient="index", columns=None
        )

    def tmp_plot(self, df_fit: pd.DataFrame) -> Path:
        """Create a temporary plot.

        Args:
            df_fit (pd.DataFrame): The DataFrame containing the fit results.

        Returns:
            Path: The path to the temporary plot.
        """
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            PlotSpectra(
                df=df_fit,
                args={},
            ).plot_local_spectra()
            tmp_fname = Path(tmp.name)
            plt.savefig(tmp_fname, dpi=300, bbox_inches="tight")
            return tmp_fname

    def create_ratio(self) -> PPTXRatioAPI:
        """Create the ratio of the powerpoint presentation.

        Returns:
            PPTXRatioAPI: The ratio of the powerpoint presentation.
        """
        return PPTXRatioAPI(
            width=Pt(self.pptx_formats[self._format][1]["width"]),
            height=Pt(self.pptx_formats[self._format][1]["height"]),
        )

    def create_header(self) -> PPTXHeaderAPI:
        """Create the header of the powerpoint presentation.

        Returns:
            PPTXHeaderAPI: The header of the powerpoint presentation.
        """
        return PPTXHeaderAPI(
            position=PPTXPositionAPI(
                left=Pt(0),
                top=Pt(0),
                width=Pt(self.pptx_formats[self._format][1]["width"]),
                height=Pt(self.pptx_formats[self._format][1]["height"] // 5),
            ),
            text=self.title,
        )

    def create_sub_title_left(self) -> PPTXSubTitleLeftAPI:
        """Create the left subtitle of the powerpoint presentation.

        Returns:
            PPTXSubTitleLeftAPI: The left subtitle of the powerpoint presentation.
        """
        return PPTXSubTitleLeftAPI(
            position=PPTXPositionAPI(
                left=Pt(0),
                top=Pt(self.pptx_formats[self._format][1]["height"] // 5),
                width=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                height=Pt(self.pptx_formats[self._format][1]["height"] // 10),
            ),
            text=PPTXBasicTitleAPI().sub_title_left,
            figure=PPTXFigureAPI(
                position=PPTXPositionAPI(
                    left=Pt(0),
                    top=Pt(
                        self.pptx_formats[self._format][1]["height"] // 5
                        + self.pptx_formats[self._format][1]["height"] // 10
                    ),
                    width=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                    height=Pt(3 * self.pptx_formats[self._format][1]["height"] // 5),
                ),
                description=PPTXDescriptionAPI(
                    position=PPTXPositionAPI(
                        left=Pt(0),
                        top=Pt(
                            self.pptx_formats[self._format][1]["height"] // 10
                            + 4 * self.pptx_formats[self._format][1]["height"] // 5
                        ),
                        width=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                        height=Pt(18),
                    ),
                    text=PPTXBasicTitleAPI().figure_description,
                ),
                fname=self.tmp_fname,
            ),
        )

    def create_sub_title_right(self) -> PPTXSubTitleRightAPI:
        """Create the right subtitle of the powerpoint presentation.

        Returns:
            PPTXSubTitleRightAPI: The right subtitle of the powerpoint presentation.
        """
        return PPTXSubTitleRightAPI(
            position=PPTXPositionAPI(
                left=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                top=Pt(self.pptx_formats[self._format][1]["height"] // 5),
                width=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                height=Pt(self.pptx_formats[self._format][1]["height"] // 10),
            ),
            text=PPTXBasicTitleAPI().sub_title_right,
            table_1=self.create_table_1(),
            table_2=self.create_table_2(),
            table_3=self.create_table_3(),
            credit=self.create_credit(),
        )

    def create_table_1(self) -> PPTXTableAPI:
        """Create the table 1 of the powerpoint presentation.

        Returns:
            PPTXTableAPI: The table 1 of the powerpoint presentation.
        """
        _basic_block = (
            self.pptx_formats[self._format][1]["height"] // 5
            + self.pptx_formats[self._format][1]["height"] // 10
        )
        return PPTXTableAPI(
            position=PPTXPositionAPI(
                left=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                top=Pt(_basic_block + 20),
                width=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                height=Pt(self.pptx_formats[self._format][1]["height"] // 6),
            ),
            description=PPTXDescriptionAPI(
                position=PPTXPositionAPI(
                    left=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                    top=Pt(_basic_block),
                    width=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                    height=Pt(18),
                ),
                text=PPTXBasicTitleAPI().table_1_description,
            ),
            df=self.df_gof,
            transpose=False,
            index_hidden=True,
        )

    def create_table_2(self) -> PPTXTableAPI:
        """Create the table 2 of the powerpoint presentation.

        Returns:
            PPTXTableAPI: The table 2 of the powerpoint presentation.
        """
        _basic_block = (
            self.pptx_formats[self._format][1]["height"] // 5
            + self.pptx_formats[self._format][1]["height"] // 10
            + self.pptx_formats[self._format][1]["height"] // 6
        )
        return PPTXTableAPI(
            position=PPTXPositionAPI(
                left=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                top=Pt(_basic_block + 40),
                width=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                height=Pt(self.pptx_formats[self._format][1]["height"] // 6),
            ),
            description=PPTXDescriptionAPI(
                position=PPTXPositionAPI(
                    left=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                    top=Pt(_basic_block + 20),
                    width=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                    height=Pt(18),
                ),
                text=PPTXBasicTitleAPI().table_2_description,
            ),
            df=self.df_regression,
            transpose=True,
            index_hidden=True,
        )

    def create_table_3(self) -> PPTXTableAPI:
        """Create the table 3 of the powerpoint presentation.

        Returns:
            PPTXTableAPI: The table 3 of the powerpoint presentation.
        """
        _basic_block = (
            self.pptx_formats[self._format][1]["height"] // 5
            + self.pptx_formats[self._format][1]["height"] // 10
            + self.pptx_formats[self._format][1]["height"] // 3
        )
        return PPTXTableAPI(
            position=PPTXPositionAPI(
                left=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                top=Pt(_basic_block + 60),
                width=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                height=Pt(self.pptx_formats[self._format][1]["height"] // 6),
            ),
            description=PPTXDescriptionAPI(
                position=PPTXPositionAPI(
                    left=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                    top=Pt(_basic_block + 40),
                    width=Pt(self.pptx_formats[self._format][1]["width"] // 2),
                    height=Pt(18),
                ),
                text=PPTXBasicTitleAPI().table_3_description,
            ),
            df=self.df_variables,
            transpose=True,
            index_hidden=False,
        )

    def create_credit(self) -> PPTXFigureAPI:
        """Create the credit of the powerpoint presentation.

        Returns:
            PPTXFigureAPI: The credit of the powerpoint presentation.
        """
        return PPTXFigureAPI(
            position=PPTXPositionAPI(
                left=Pt(self.pptx_formats[self._format][1]["width"] - 40),
                top=Pt(self.pptx_formats[self._format][1]["height"] - 40),
                width=Pt(40),
                height=Pt(40),
            ),
            description=PPTXDescriptionAPI(
                position=PPTXPositionAPI(
                    left=Pt(self.pptx_formats[self._format][1]["width"] - 200),
                    top=Pt(self.pptx_formats[self._format][1]["height"] - 40),
                    width=Pt(200),
                    height=Pt(14),
                ),
                text=PPTXBasicTitleAPI().credit_description,
            ),
            fname=PPTXBasicTitleAPI().credit_logo,
        )

    def get_pptx_layout(self) -> Union[Field169API, Field169HDRAPI, Field43API]:
        """Get the powerpoint presentation layout.

        Returns:
            Union[Field169API, Field169HDRAPI, Field43API]: The powerpoint presentation
                layout.
        """
        return self.pptx_formats[self._format][0](
            ratio=self.create_ratio(),
            structure=PPTXStructureAPI(
                header=self.create_header(),
                sub_title_left=self.create_sub_title_left(),
                sub_title_right=self.create_sub_title_right(),
            ),
        )
