from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from django.core.management.base import BaseCommand, CommandParser

import tree_comments

if TYPE_CHECKING:
    from tree_comments.base import AbstractBaseComment


class Command(BaseCommand):
    help = "Remove comments for which the related objects don't exist anymore!"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "-y",
            "--yes",
            default="x",
            action="store_const",
            const="y",
            dest="answer",
            help="Automatically confirm deletion",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        verbose = options["verbosity"] >= 1
        answer = options["answer"]

        # -v0 sets --yes
        if not verbose:
            answer = "y"

        comment_model = cast("type[AbstractBaseComment]", tree_comments.get_comment_model())
        for comment in comment_model._default_manager.all():
            if comment.content_object is None:
                if verbose:
                    self.stdout.write(
                        f"Comment `{comment}' to non-existing "
                        f"`{comment.content_type.model}' with PK `{comment.object_pk}'"
                    )

                while answer not in "yn":
                    answer = input("Do you wish to delete? [yN] ")
                    if not answer:
                        answer = "x"
                        continue
                    answer = answer[0].lower()

                if answer == "y":
                    comment.delete()

                    if verbose:
                        self.stdout.write(f"Deleted comment `{comment}'")
