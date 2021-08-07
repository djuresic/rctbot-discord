from __future__ import annotations

import datetime
from typing import Optional, List

from pydantic import BaseModel  # pylint: disable=no-name-in-module

# Reference: https://fastapi.tiangolo.com/tutorial/body-nested-models/
# TODO: Question.question, yikes. This has be changed in Mongo and other files first and then updated here to match.
# Question.text is preferable.
class Question(BaseModel):
    _id: int
    enabled: bool
    category: str
    question: str
    answer: List[str]
    hint: Optional[str] = None


# Allow new player object creation with just ID. TODO: _id back to Mongo default and Optional, discord_id as a key.
class Player(BaseModel):
    _id: int
    active: Optional[bool] = True
    points: Optional[int] = 0
    correct: Optional[int] = 0
    wrong: Optional[int] = 0
    total_rounds: Optional[int] = 0
    total_games: Optional[int] = 0
    tokens: Optional[int] = 0


class RoundParticipant(BaseModel):
    id: int
    name: Optional[str] = None
    display_name: Optional[str] = None


class GameRound(BaseModel):
    question: str
    answers: List[str]
    winners: Optional[List[RoundParticipant]] = []
    wrong: Optional[List[RoundParticipant]] = []


class GameChannel(BaseModel):
    id: int
    name: Optional[str] = None


class GameSettings:
    name: Optional[str] = "Unnamed"
    rounds: int
    round_length: int
    pause_time: int
    attempts: int
    repost: Optional[bool] = False
    point_distribution: Optional[List[int]] = [1]
    mute_duration: Optional[float] = 0.0
    channel: Optional[GameChannel] = None


class GameResults(BaseModel):
    _id: int
    rounds: Optional[List[GameRound]] = []
    settings: GameSettings
    date: datetime.datetime
