# Management Commands

## delete_stale_comments

Remove comments whose target object no longer exists.

Because the comment model uses a generic relation (`content_type` +
`object_pk`), the database does not enforce cascade deletes when the commented
object is removed. This command cleans up those orphaned comments.

```shell
python manage.py delete_stale_comments
```

### Options

| Flag | Description |
|------|-------------|
| `-y`, `--yes` | Automatically confirm every deletion (non-interactive). |
| `-v 0` | Implies `--yes` and silences output. |

### Usage with cron

```shell
# Daily cleanup, non-interactive
python manage.py delete_stale_comments --yes
```
