"""Opt-in live storage check; keeps one fixture outside users' recipe collections."""

import sys
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from uuid import UUID

from fastapi import HTTPException

from cs_452_finalproject.configuration import load_environment
from cs_452_finalproject.recipe_library import MongoRecipes, RecipeCreate, RecipeUpdate
from cs_452_finalproject.services import MongoAccounts


def repository(accounts):
    collection = accounts.collection().database.recipe_verification
    reference = SimpleNamespace(
        collection=lambda: SimpleNamespace(database=SimpleNamespace(recipes=collection))
    )
    return MongoRecipes(reference)


def main():
    if "--write-test-record" not in sys.argv:
        print("Opt in with --write-test-record. This writes one fixture in recipe_verification.")
        return 1
    load_environment()
    accounts = MongoAccounts()
    second_connection = MongoAccounts()
    uid = "development-storage-verification"
    try:
        recipes = repository(accounts)
        creation = RecipeCreate.model_validate(
            {
                "client_request_id": "179fbb66-a77d-47a4-b88d-c9023e10bdf2",
                "recipe": {
                    "title": "Backend verification fixture",
                    "servings": 2,
                    "ingredients": [
                        {
                            "name": "rice",
                            "original_text": "1 cup uncooked rice",
                            "quantity": "1",
                            "unit": "cup",
                        }
                    ],
                    "steps": ["Development test only; not cooking advice."],
                    "prep_minutes": 0,
                    "cook_minutes": 0,
                },
            }
        )
        saved = recipes.create(uid, creation)
        assert recipes.create(uid, creation).id == saved.id
        assert repository(second_connection).read(uid, saved.id).recipe.title == saved.recipe.title
        print("Live Atlas: create, idempotent retry, and read from a new connection passed.")

        def competing_save():
            try:
                recipes.update(
                    uid,
                    saved.id,
                    RecipeUpdate(
                        expected_revision=saved.revision,
                        recipe=saved.recipe,
                    ),
                )
                return 200
            except HTTPException as error:
                return error.status_code

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = sorted(executor.map(lambda _: competing_save(), range(2)))
        assert outcomes == [200, 409]
        assert recipes.read(uid, saved.id).revision == saved.revision + 1
        print("Live Atlas: concurrent edits produced one save and one 409 conflict.")
        try:
            recipes.read("another-development-user", UUID(str(saved.id)))
        except HTTPException as error:
            assert error.status_code == 404
        else:
            raise AssertionError("Owner filter failed")
        print("Live Atlas: another owner cannot read the fixture.")
        print("One fixture remains in recipe_verification; no real account or recipe was changed.")
        return 0
    except Exception as error:  # noqa: BLE001 -- avoid printing secret-bearing driver errors
        print(f"Live recipe verification failed ({type(error).__name__}).")
        return 1
    finally:
        accounts.close()
        second_connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
