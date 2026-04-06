# Recipe Normalization Schema

Apply the SQL files in this order:

1. `00_extensions.sql`
2. `10_parsed_layer.sql`
3. `20_canonical_layer.sql`
4. `30_recipe_layer.sql`
5. `40_user_layer.sql`
6. `50_indexes.sql`

Python runner:

```bash
python -m app.apply_schema
```

Preview only:

```bash
python -m app.apply_schema --dry-run
```
