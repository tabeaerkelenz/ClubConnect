from __future__ import annotations

import os
from typing import Any

from openai import OpenAI

from app.repositories.ai_usage import AIUsageRepository
from app.schemas.workout_plan_ai import WorkoutPlanAIDraftRequest, WorkoutPlanAIDraft
from app.services.workout_plan import WorkoutPlanService
from app.exceptions.base import RateLimitError


FEATURE_WORKOUTPLAN_DRAFT = "workout_plan_draft"


class WorkoutPlanAIService:
    def __init__(
        self,
        workout_plan_service: WorkoutPlanService,
        ai_usage_repo: AIUsageRepository,
        *,
        daily_limit: int = 3,
    ):
        self.workout_plan_service = workout_plan_service
        self.ai_usage_repo = ai_usage_repo
        self.daily_limit = daily_limit

        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_and_create_plan(
        self,
        *,
        club_id: int,
        user_id: int,
        req: WorkoutPlanAIDraftRequest,
    ):
        # 1) Quota check BEFORE paying for an AI call
        used_today = self.ai_usage_repo.count_today(
            user_id=user_id,
            feature=FEATURE_WORKOUTPLAN_DRAFT,
        )
        if used_today >= self.daily_limit:
            raise RateLimitError(
                detail=f"Daily AI quota reached ({self.daily_limit}/day). Try again tomorrow."
            )

        # 2) Generate draft JSON via Structured Outputs
        draft = self._generate_draft(req)

        # 3) Persist using existing service rules (created_by_id = user)
        plan = self.workout_plan_service.create_plan(
            club_id=club_id,
            user_id=user_id,
            data={
                "name": draft.name,
                "description": draft.description,
                "goal": draft.goal or req.goal,
                "level": draft.level or req.level,
                "duration_weeks": draft.duration_weeks or req.duration_weeks,
                "is_template": False,
            },
        )

        for item in draft.items:
            created_item = self.workout_plan_service.create_item(
                club_id=club_id,
                plan_id=plan.id,
                user_id=user_id,
                data={
                    "week_number": item.week_number,
                    "day_label": item.day_label,
                    "order_index": item.order_index,
                    "title": item.title,
                },
            )

            for ex in item.exercises:
                self.workout_plan_service.create_exercise(
                    club_id=club_id,
                    plan_id=plan.id,
                    item_id=created_item.id,
                    user_id=user_id,
                    data={
                        "name": ex.name,
                        "description": ex.description,
                        "sets": ex.sets,
                        "repetitions": ex.repetitions,
                        "rest_seconds": ex.rest_seconds,
                        "tempo": ex.tempo,
                        "weight_kg": ex.weight_kg,
                        "position": ex.position,
                    },
                )

        # 4) Record usage AFTER success (so failed calls don't consume quota)
        self.ai_usage_repo.record(
            user_id=user_id,
            club_id=club_id,
            feature=FEATURE_WORKOUTPLAN_DRAFT,
        )

        # 5) Return nested read for UI
        return self.workout_plan_service.get_plan(
            club_id=club_id,
            plan_id=plan.id,
            user_id=user_id,
            nested=True,
        )

    def _generate_draft(self, req: WorkoutPlanAIDraftRequest) -> WorkoutPlanAIDraft:
        schema: dict[str, Any] = WorkoutPlanAIDraft.model_json_schema()

        prompt = (
            "You are a strength & conditioning coach. Generate a workout plan draft.\n"
            "Return ONLY valid JSON that matches the provided JSON Schema.\n"
            "Rules:\n"
            "- Provide structured weeks and days_per_week.\n"
            "- Use concise exercise names.\n"
            "- Positions/order_index start at 0 and increase.\n"
            "- Day labels must be one of: monday..sunday when used.\n"
            "- Keep it realistic for the given level.\n"
        )

        user_input = {
            "goal": req.goal,
            "level": req.level,
            "duration_weeks": req.duration_weeks,
            "days_per_week": req.days_per_week,
            "equipment": req.equipment,
            "constraints": req.constraints,
            "notes": req.notes,
            "style": req.style,
        }

        resp = self.client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-5.2"),
            input=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"Input:\n{user_input}"},
            ],
            text={  # type: ignore[arg-type]
                "format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "WorkoutPlanAIDraft",
                        "schema": schema,
                        "strict": True,
                    },
                }
            },
        )

        json_text = resp.output_text
        return WorkoutPlanAIDraft.model_validate_json(json_text)
