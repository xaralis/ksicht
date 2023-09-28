from typing import Dict, List

from typing_extensions import TypedDict

from .. import models


class Submissions(TypedDict):
    all: List[models.TaskSolutionSubmission]
    by_series: Dict[models.GradeSeries, List[models.TaskSolutionSubmission]]
    by_tasks: Dict[models.Task, List[models.TaskSolutionSubmission]]


class SeriesDetails(TypedDict):
    rank: int
    score: float
    max_score: float
    tasks: List[models.Task]


class StickerContext(TypedDict):
    current_series: models.GradeSeries
    current_application: models.GradeApplication
    applications: List[models.GradeApplication]
    series: Dict[models.GradeSeries, SeriesDetails]
    all_series: List[models.GradeSeries]
    tasks: List[models.Task]
    submissions: Submissions
    is_last_series: bool
