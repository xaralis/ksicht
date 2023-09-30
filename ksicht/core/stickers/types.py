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


class GradeParticipantDetails(TypedDict):
    series: Dict[models.GradeSeries, SeriesDetails]
    submissions: Submissions


class GradeDetails(TypedDict):
    series: List[models.GradeSeries]
    tasks: Dict[models.GradeSeries, List[models.Task]]
    by_participant: Dict[models.Participant, GradeParticipantDetails]


class CurrentGradeExtras(TypedDict):
    grade: GradeDetails
    series: models.GradeSeries
    is_last_series: bool
    participant: GradeParticipantDetails


class StickerContext(TypedDict):
    participant: models.Participant
    current: CurrentGradeExtras
    by_grades: Dict[int, GradeDetails]
