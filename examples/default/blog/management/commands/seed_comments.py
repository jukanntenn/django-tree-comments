import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from tree_comments.models import Comment

from ...models import Post
from ...sentences import SENTENCES  # noqa: F401  (validates import at runtime)
from ...topology import build_topology

User = get_user_model()

DEMO_USERNAMES = [
    "alice_dev",
    "bob_dev",
    "carol_dev",
    "dave_dev",
    "eve_dev",
    "frank_dev",
    "grace_dev",
    "heidi_dev",
    "ivan_dev",
    "judy_dev",
    "karl_dev",
    "lily_dev",
    "mallory_dev",
    "nia_dev",
    "oscar_dev",
]
DEMO_EMAIL_DOMAIN = "example.com"
POST_BASE_TIME = datetime.datetime(2026, 1, 1, 9, 0, 0, tzinfo=datetime.timezone.utc)

POSTS = [
    {
        "title": "Welcome to django-tree-comments demo",
        "body": (
            "This post showcases the **wide and shallow** topology: many root "
            "comments, each with a few direct replies. It's the most common "
            "shape for a popular announcement thread."
        ),
        "topology": "wide_shallow",
    },
    {
        "title": "Ask Me Anything: behind the scenes",
        "body": (
            "This post showcases the **flat replies** topology: few root "
            "comments, each with many direct replies but no further nesting. "
            "Typical of AMA / Q&A threads."
        ),
        "topology": "flat_replies",
    },
    {
        "title": "Technical deep dive: recursive CTE performance",
        "body": (
            "This post showcases the **wide and deep** topology: many root "
            "comments each spawning a balanced sub-tree several levels deep. "
            "Stress-tests nesting visualization."
        ),
        "topology": "wide_deep",
    },
    {
        "title": "Empty comments section",
        "body": ("This post intentionally has no comments. It exists to show the empty-state UI."),
        "topology": "empty",
    },
    {
        "title": "A long back-and-forth discussion",
        "body": (
            "This post showcases a **single deep chain**: one root comment "
            "with a focused multi-level reply thread. Demonstrates deep "
            "nesting with conversational continuity."
        ),
        "topology": "deep_chain",
    },
]


class Command(BaseCommand):
    help = "Seed the demo database with posts, users, and threaded comments."

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42, help="Random seed (default 42).")
        parser.add_argument("--no-flush", action="store_true", help="Skip clearing existing comments.")

    def handle(self, *args, **options):
        seed = options["seed"]
        do_flush = not options["no_flush"]
        verbosity = options.get("verbosity", 1)

        with transaction.atomic():
            users = self._ensure_users(seed=seed, verbosity=verbosity)
            if do_flush:
                self._flush_comments(verbosity=verbosity)
            for i, post_spec in enumerate(POSTS, start=1):
                post = self._ensure_post(post_spec, seq=i)
                nodes = build_topology(post_spec["topology"], seed=seed + i)
                self._seed_comments(post, nodes, users, verbosity=verbosity)
                if verbosity >= 1:
                    self.stdout.write(
                        self.style.SUCCESS(f"  [{i}/{len(POSTS)}] {post_spec['topology']:<14} -> {len(nodes)} comments")
                    )
            if verbosity >= 1:
                self.stdout.write(self.style.SUCCESS("Seed complete."))

    def _ensure_users(self, *, seed, verbosity):
        created = []
        for idx, username in enumerate(DEMO_USERNAMES):
            user, was_created = User.objects.get_or_create(
                username=username,
                defaults={"email": f"{username}@{DEMO_EMAIL_DOMAIN}"},
            )
            created.append(user)
            if verbosity >= 2 and was_created:
                self.stdout.write(f"  created user {username}")
        return created

    def _flush_comments(self, *, verbosity):
        deleted, _ = Comment.objects.all().delete()
        if verbosity >= 2 and deleted:
            self.stdout.write(f"  flushed {deleted} existing comments")

    def _ensure_post(self, spec, *, seq):
        base_time = POST_BASE_TIME + datetime.timedelta(days=seq - 1)
        post, _ = Post.objects.get_or_create(
            title=spec["title"],
            defaults={
                "body": spec["body"],
                "created_at": base_time,
                "enable_comments": True,
                "author": User.objects.first(),
            },
        )
        return post

    def _seed_comments(self, post, nodes, users, *, verbosity):
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.sites.models import Site

        ct = ContentType.objects.get_for_model(Post)
        site_id = Site.objects.get_current().pk
        from faker import Faker

        fake = Faker()
        fake.seed_instance(99)

        index_to_pk = [None] * len(nodes)
        count = 0
        for position, node in enumerate(nodes):
            parent_pk = index_to_pk[node["parent_index"]] if node["parent_index"] is not None else None
            submit_date = post.created_at + datetime.timedelta(seconds=node["submit_offset"])
            if node["is_anon"]:
                user = None
                user_name = fake.user_name()
                user_email = fake.email()
            else:
                user = users[node["user_index"]]
                user_name = user.username
                user_email = user.email
            c = Comment(
                content_type=ct,
                object_pk=str(post.pk),
                site_id=site_id,
                parent_id=parent_pk,
                user=user,
                user_name=user_name,
                user_email=user_email,
                user_url="",
                comment=node["body"],
                submit_date=submit_date,
                is_public=True,
                is_removed=False,
            )
            c.save()
            index_to_pk[position] = c.pk
            count += 1
        if verbosity >= 2:
            self.stdout.write(f"    persisted {count} comments for post pk={post.pk}")
